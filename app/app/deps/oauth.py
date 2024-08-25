import time
from typing import Annotated, List, Text, Tuple, TypeAlias

from app.config import logger
from app.db._base import DatabaseBase
from app.db.tokens import is_token_blocked
from app.db.users import get_user
from app.deps.db import depend_db
from app.schemas.oauth import (
    ROLE_PERMISSIONS,
    PayloadParam,
    Permission,
    Role,
    TokenData,
    User,
    UserInDB,
)
from app.utils.oauth import oauth2_scheme, verify_payload, verify_token
from fastapi import Depends, HTTPException
from fastapi import Path as QueryPath
from fastapi import status
from pydantic_core import ValidationError

TYPE_TOKEN_PAYLOAD: TypeAlias = Tuple[Text, PayloadParam]
TYPE_TOKEN_PAYLOAD_DATA: TypeAlias = Tuple[Text, PayloadParam, TokenData]
TYPE_TOKEN_PAYLOAD_DATA_USER: TypeAlias = Tuple[Text, PayloadParam, TokenData, UserInDB]
TYPE_TOKEN_PAYLOAD_DATA_USER_ORG: TypeAlias = Tuple[
    Text, PayloadParam, TokenData, UserInDB, Text
]


async def get_token_payload(token: Text = Depends(oauth2_scheme)) -> TYPE_TOKEN_PAYLOAD:
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

    return (token, payload)


async def get_current_token_payload(
    token_payload: Annotated[TYPE_TOKEN_PAYLOAD, Depends(get_token_payload)]
) -> TYPE_TOKEN_PAYLOAD:
    payload = token_payload[1]
    if time.time() > payload["exp"]:
        logger.debug(f"Token '{token_payload[0]}' has expired at {payload['exp']}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token_payload


async def get_current_active_token_payload(
    token_payload: Annotated[TYPE_TOKEN_PAYLOAD, Depends(get_current_token_payload)],
    db: Annotated[DatabaseBase, Depends(depend_db)],
) -> TYPE_TOKEN_PAYLOAD:

    token = token_payload[0]
    if is_token_blocked(db, token=token):
        logger.debug(f"Token '{token}' has been invalidated")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token_payload


async def get_current_active_token_payload_data(
    token_payload: Annotated[
        TYPE_TOKEN_PAYLOAD, Depends(get_current_active_token_payload)
    ],
) -> TYPE_TOKEN_PAYLOAD_DATA:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Parse token data
    payload = token_payload[1]
    try:
        token_data = TokenData.from_payload(payload=dict(payload))
    except ValidationError as e:
        logger.exception(e)
        logger.error(f"Token '{token_payload[0]}' has invalid payload: {payload}")
        raise credentials_exception
    if token_data.username is None:
        logger.error(f"Token '{token_payload[0]}' has an invalid username")
        raise credentials_exception

    return (token_payload[0], token_payload[1], token_data)


async def get_current_user(
    token_payload_data: Annotated[
        TYPE_TOKEN_PAYLOAD_DATA, Depends(get_current_active_token_payload_data)
    ],
    db: Annotated[DatabaseBase, Depends(depend_db)],
) -> TYPE_TOKEN_PAYLOAD_DATA_USER:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token_data = token_payload_data[2]

    # Get user from the database
    user = get_user(db, username=token_data.username)
    if user is None:
        logger.debug(f"User '{token_data.username}' not found")
        raise credentials_exception

    # Return the user
    return (token_payload_data[0], token_payload_data[1], token_payload_data[2], user)


async def get_current_active_user(
    token_payload_data_user: Annotated[
        TYPE_TOKEN_PAYLOAD_DATA_USER, Depends(get_current_user)
    ]
) -> TYPE_TOKEN_PAYLOAD_DATA_USER:
    current_user = token_payload_data_user[3]
    if current_user.disabled:
        logger.debug(f"User '{current_user.username}' is inactive")
        raise HTTPException(status_code=400, detail="Inactive user")
    return token_payload_data_user


async def get_current_active_user_of_org(
    org_id: Text = QueryPath(
        ..., description="The ID of the organization to retrieve."
    ),
    token_payload_data_user: TYPE_TOKEN_PAYLOAD_DATA_USER = Depends(
        get_current_active_user
    ),
) -> TYPE_TOKEN_PAYLOAD_DATA_USER_ORG:
    user = token_payload_data_user[3]

    if user.role in (Role.SUPER_ADMIN, Role.PLATFORM_ADMIN):
        pass

    elif user.organization_id != org_id:
        logger.debug(
            f"User '{user.username}' is not a member of organization '{org_id}'"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
        )

    return (
        token_payload_data_user[0],
        token_payload_data_user[1],
        token_payload_data_user[2],
        user,
        org_id,
    )


def get_user_with_required_permissions(required_permissions: List[Permission]):
    """Check if the current user has the required permissions."""

    def get_current_active_user_permissions(
        token_payload_data_user: TYPE_TOKEN_PAYLOAD_DATA_USER = Depends(
            get_current_active_user
        ),
        # db: DatabaseBase = Depends(depend_db),  # Implement this if you need to access the database
    ) -> TYPE_TOKEN_PAYLOAD_DATA_USER:
        user = token_payload_data_user[3]
        user_permissions = ROLE_PERMISSIONS[user.role].permissions
        logger.debug(
            f"User '{user.username}' with role '{user.role}' "
            + f"has permissions '{user_permissions}'"
        )

        # Check if the user has the required permissions
        if Permission.MANAGE_ALL_RESOURCES in user_permissions:
            return token_payload_data_user  # Super Admin has all permissions

        if not set(required_permissions).issubset(set(user_permissions)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
            )

        # Additional checks for organization-specific permissions
        if (
            Permission.MANAGE_ORG_CONTENT in required_permissions
            or Permission.MANAGE_ORG_USERS in required_permissions
        ):
            pass

        return token_payload_data_user

    return get_current_active_user_permissions


def get_user_of_org_with_required_permissions(required_permissions: List[Permission]):
    """Check if the current user has the required permissions."""

    def get_current_active_user_of_org_permissions(
        token_payload_data_user_org: TYPE_TOKEN_PAYLOAD_DATA_USER_ORG = Depends(
            get_current_active_user_of_org
        ),
        # db: DatabaseBase = Depends(depend_db),  # Implement this if you need to access the database
    ) -> TYPE_TOKEN_PAYLOAD_DATA_USER_ORG:
        user = token_payload_data_user_org[3]
        user_permissions = ROLE_PERMISSIONS[user.role].permissions
        logger.debug(
            f"User '{user.username}' with role '{user.role}' "
            + f"has permissions '{user_permissions}'"
        )

        # Check if the user has the required permissions
        if Permission.MANAGE_ALL_RESOURCES in user_permissions:
            return token_payload_data_user_org  # Super Admin has all permissions

        if not set(required_permissions).issubset(set(user_permissions)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
            )

        # Additional checks for organization-specific permissions
        if (
            Permission.MANAGE_ORG_CONTENT in required_permissions
            or Permission.MANAGE_ORG_USERS in required_permissions
        ):
            pass

        return token_payload_data_user_org

    return get_current_active_user_of_org_permissions


def PermissionChecker(required_permissions: List[Permission]):
    """Check if the current user has the required permissions."""

    async def check_permission(
        current_user: Annotated[User, Depends(get_current_active_user)],
        # db: DatabaseBase = Depends(depend_db),  # Implement this if you need to access the database
    ) -> None:
        user_permissions = ROLE_PERMISSIONS[current_user.role].permissions
        logger.debug(
            f"User '{current_user.username}' with role '{current_user.role}' "
            + f"has permissions '{user_permissions}'"
        )

        # Check if the user has the required permissions
        if Permission.MANAGE_ALL_RESOURCES in user_permissions:
            return  # Super Admin has all permissions

        if not set(required_permissions).issubset(set(user_permissions)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
            )

        # Additional checks for organization-specific permissions
        if (
            Permission.MANAGE_ORG_CONTENT in required_permissions
            or Permission.MANAGE_ORG_USERS in required_permissions
        ):
            pass

    return check_permission
