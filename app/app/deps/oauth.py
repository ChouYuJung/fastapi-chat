import time
from enum import Enum
from typing import Annotated, Dict, List, Text, TypeVar

from app.config import logger
from app.db._base import DatabaseBase
from app.db.tokens import is_token_blocked
from app.db.users import get_user
from app.deps.db import depend_db
from app.schemas.oauth import TokenData
from app.utils.common import run_as_coro
from app.utils.oauth import oauth2_scheme, verify_payload, verify_token
from fastapi import Depends, HTTPException
from fastapi import Path as QueryPath
from fastapi import status
from pydantic import BaseModel
from pydantic_core import ValidationError

from ..schemas.organizations import Organization
from ..schemas.permissions import Permission
from ..schemas.role_per_definitions import get_role_permissions
from ..schemas.roles import Role
from ..schemas.users import UserInDB

T = TypeVar("T")


class TokenPayloadDepends(BaseModel):
    token: Text
    payload: Dict


class TokenDataDepends(TokenPayloadDepends):
    token_data: TokenData


class TokenUserDepends(TokenDataDepends):
    user: UserInDB


class TokenUserManagingDepends(TokenUserDepends):
    target_user: UserInDB


class TokenOrgDepends(TokenUserDepends):
    organization: Organization


class TokenOrgUserManagingDepends(TokenUserManagingDepends, TokenOrgDepends):
    pass


async def depends_token(token: Text = Depends(oauth2_scheme)) -> Text:
    return token


async def depends_token_payload(
    token: Text = Depends(depends_token),
) -> TokenPayloadDepends:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Verify the token and check the payload.
    payload = verify_token(token)
    if payload is None:
        logger.debug(f"Token '{token}' is invalid")
        raise credentials_exception
    payload = verify_payload(payload)
    if payload is None:
        logger.debug(f"Token '{token}' has an invalid payload")
        raise credentials_exception

    return TokenPayloadDepends.model_validate({"token": token, "payload": payload})


async def depends_current_token_payload(
    token_payload: Annotated[TokenPayloadDepends, Depends(depends_token_payload)]
) -> TokenPayloadDepends:
    payload = token_payload.payload
    if time.time() > payload["exp"]:
        logger.debug(f"Token '{token_payload.token}' has expired at {payload['exp']}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token_payload


async def depends_active_token_payload(
    token_payload: Annotated[
        TokenPayloadDepends, Depends(depends_current_token_payload)
    ],
    db: Annotated[DatabaseBase, Depends(depend_db)],
) -> TokenPayloadDepends:

    token = token_payload.token
    payload = token_payload.payload
    if await run_as_coro(is_token_blocked, db, token=token):
        logger.debug(f"Token '{token}' has been invalidated")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if payload.get("disabled") is True:
        logger.debug(f"Token '{token}' has been disabled")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token disabled",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token_payload


async def depends_token_data(
    token_payload: Annotated[
        TokenPayloadDepends, Depends(depends_active_token_payload)
    ],
) -> TokenDataDepends:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Parse token data
    payload = token_payload.payload
    try:
        token_data = TokenData.from_payload(payload=dict(payload))
    except ValidationError as e:
        logger.exception(e)
        logger.error(f"Token '{token_payload.token}' has invalid payload: {payload}")
        raise credentials_exception
    if token_data.username is None:
        logger.error(f"Token '{token_payload.token}' has an invalid username")
        raise credentials_exception

    return TokenDataDepends.model_validate(
        {"token": token_payload.token, "payload": payload, "token_data": token_data}
    )


async def depends_current_user(
    token_payload_data: Annotated[TokenDataDepends, Depends(depends_token_data)],
    db: Annotated[DatabaseBase, Depends(depend_db)],
) -> TokenUserDepends:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token_data = token_payload_data.token_data

    # Get user from the database
    user = await get_user(db, username=token_data.username)
    if user is None:
        logger.debug(f"User '{token_data.username}' not found")
        raise credentials_exception

    return TokenUserDepends.model_validate(
        {
            "token": token_payload_data.token,
            "payload": token_payload_data.payload,
            "token_data": token_data,
            "user": user,
        }
    )


async def depends_active_user(
    token_payload_user: Annotated[TokenUserDepends, Depends(depends_current_user)]
) -> TokenUserDepends:
    current_user = token_payload_user.user
    if current_user.disabled:
        logger.debug(f"User '{current_user.username}' is inactive")
        raise HTTPException(status_code=400, detail="Inactive user")
    return token_payload_user


async def depends_path_user_id(
    user_id: Text = QueryPath(..., description="The ID of the user to retrieve."),
    db: DatabaseBase = Depends(depend_db),
):
    user = await run_as_coro(db.retrieve_user, user_id=user_id)
    if user is None:
        logger.debug(f"Querying user '{user_id}' not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


async def depends_current_path_org_id(
    org_id: Text = QueryPath(
        ..., description="The ID of the organization to retrieve."
    ),
    db: DatabaseBase = Depends(depend_db),
):
    current_org = await run_as_coro(db.retrieve_organization, organization_id=org_id)
    if current_org is None:
        logger.debug(f"Organization '{org_id}' not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
        )
    return current_org


async def depends_active_path_org_id(
    current_org: Organization = Depends(depends_current_path_org_id),
):
    if current_org.disabled:
        logger.debug(f"Organization '{current_org.id}' is inactive")
        raise HTTPException(status_code=400, detail="Inactive organization")
    return current_org


async def depends_platform_user(
    token_payload_user: TokenUserDepends = Depends(depends_active_user),
) -> TokenUserDepends:
    user = token_payload_user.user
    if user.role in (
        Role.SUPER_ADMIN,
        Role.PLATFORM_ADMIN,
        Role.PLATFORM_EDITOR,
        Role.PLATFORM_VIEWER,
    ):
        pass  # Platform users have access
    else:
        logger.debug(f"User '{user.username}' is not a platform user")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
        )
    return token_payload_user


async def depends_user_managing(
    target_user: UserInDB = Depends(depends_path_user_id),
    token_payload_user: TokenUserDepends = Depends(depends_active_user),
) -> TokenUserManagingDepends:
    user = token_payload_user.user
    user_role_per = get_role_permissions(user.role)
    tar_user_role_per = get_role_permissions(target_user.role)

    # Check if the user has the required permissions
    # User can manage users with lower or equal roles
    if tar_user_role_per.auth_level > user_role_per.auth_level:
        logger.debug(
            f"User '{user.id}' cannot manage user '{target_user.id}' with higher role"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
        )

    # Super admin and platform users have access to all users
    elif user.role in (Role.SUPER_ADMIN, Role.PLATFORM_ADMIN, Role.PLATFORM_EDITOR):
        pass

    # Hard check that the super admin cannot be managed
    elif target_user.role == Role.SUPER_ADMIN:
        logger.debug(
            f"User '{user.username}' cannot manage Super Admin '{target_user.id}'"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
        )

    # Check if the user is a member of the same organization
    elif user.organization_id != target_user.organization_id:
        logger.debug(
            f"User organization '{user.organization_id}' does not match "
            + f"target user organization '{target_user.organization_id}'"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
        )

    return TokenUserManagingDepends.model_validate(
        {
            "token": token_payload_user.token,
            "payload": token_payload_user.payload,
            "token_data": token_payload_user.token_data,
            "user": user,
            "target_user": target_user,
        }
    )


async def depends_org_managing(
    org: Organization = Depends(depends_current_path_org_id),
    token_payload_user: TokenUserDepends = Depends(depends_active_user),
) -> TokenOrgDepends:
    user = token_payload_user.user

    if user.role in (Role.SUPER_ADMIN, Role.PLATFORM_ADMIN, Role.PLATFORM_EDITOR):
        pass

    elif org.id != user.organization_id:
        logger.debug(f"User '{user.id}' is not a member of organization '{org.id}'")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
        )

    return TokenOrgDepends.model_validate(
        {
            "token": token_payload_user.token,
            "payload": token_payload_user.payload,
            "token_data": token_payload_user.token_data,
            "user": user,
            "organization": org,
        }
    )


async def depends_org_user_managing(
    target_payload_user_managing: TokenUserManagingDepends = Depends(
        depends_user_managing
    ),
    token_payload_org: TokenOrgDepends = Depends(depends_org_managing),
) -> TokenOrgUserManagingDepends:
    user = token_payload_org.user
    org = token_payload_org.organization
    target_user = target_payload_user_managing.target_user

    # Super admin and platform users have access to all users
    if user.role in (Role.SUPER_ADMIN, Role.PLATFORM_ADMIN, Role.PLATFORM_EDITOR):
        pass

    # Hard check that the super admin cannot be managed
    elif target_user.role == Role.SUPER_ADMIN:
        logger.debug(
            f"User '{user.username}' cannot manage Super Admin '{target_user.id}'"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
        )

    # Check if the user is a member of the same organization
    elif user.organization_id != org.id:
        logger.debug(
            f"User '{user.username}' is not a member of organization '{org.id}'"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
        )

    # Check if the target user is a member of the same organization
    elif target_user.organization_id != org.id:
        logger.debug(
            f"User '{target_user.username}' is not a member of organization '{org.id}'"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
        )

    return TokenOrgUserManagingDepends.model_validate(
        {
            "token": token_payload_org.token,
            "payload": token_payload_org.payload,
            "token_data": token_payload_org.token_data,
            "user": user,
            "organization": org,
            "target_user": target_user,
        }
    )


class DependsUserPermissionsFunctions(Enum):
    DEPENDS_CURRENT_USER = depends_current_user
    DEPENDS_ACTIVE_USER = depends_active_user
    DEPENDS_PATH_USER_ID = depends_path_user_id
    DEPENDS_CURRENT_PATH_ORG_ID = depends_current_path_org_id
    DEPENDS_ACTIVE_PATH_ORG_ID = depends_active_path_org_id
    DEPENDS_PLATFORM_USER = depends_platform_user
    DEPENDS_USER_MANAGING = depends_user_managing
    DEPENDS_ORG_MANAGING = depends_org_managing
    DEPENDS_ORG_USER_MANAGING = depends_org_user_managing


async def DependsUserPermissions(
    required_permissions: List[Permission],
    depends_payload: DependsUserPermissionsFunctions,
):
    """Check if the current user has the required permissions."""

    depends_payload_func = None
    if depends_payload is not None:
        depends_payload_func = (
            depends_payload.value
            if isinstance(depends_payload, Enum)
            else depends_payload
        )

    async def _depends(token_payload: T = Depends(depends_payload_func)) -> T:
        if hasattr(token_payload, "user") is False:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user: UserInDB = getattr(token_payload, "user")
        user_permissions = get_role_permissions(user.role)
        logger.debug(
            f"User '{user.username}' with role '{user.role}' "
            + f"has permissions '{user_permissions}'"
        )

        # Check if the user has the required permissions
        if user_permissions.manage_all_resources is True:
            pass  # Super Admin has all permissions

        # Check if the user has the required permissions
        elif user_permissions.is_permission_granted(required_permissions) is False:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
            )

        return token_payload

    return _depends
