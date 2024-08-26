import time
from typing import Annotated, List, Literal, Text, Tuple, TypeAlias, TypeVar

from app.config import logger
from app.db._base import DatabaseBase
from app.db.tokens import is_token_blocked
from app.db.users import get_user
from app.deps.db import depend_db
from app.schemas.oauth import (
    ROLE_AUTH_LEVELS,
    ROLE_PERMISSIONS,
    Organization,
    PayloadParam,
    Permission,
    Role,
    TokenData,
    UserInDB,
)
from app.utils.common import run_as_coro
from app.utils.oauth import oauth2_scheme, verify_payload, verify_token
from fastapi import Depends, HTTPException
from fastapi import Path as QueryPath
from fastapi import status
from pydantic_core import ValidationError

T = TypeVar("T")

TYPE_TOKEN_PAYLOAD: TypeAlias = Tuple[Text, PayloadParam]
TYPE_TOKEN_PAYLOAD_DATA: TypeAlias = Tuple[Text, PayloadParam, TokenData]
TYPE_TOKEN_PAYLOAD_DATA_USER: TypeAlias = Tuple[Text, PayloadParam, TokenData, UserInDB]
TYPE_TOKEN_PAYLOAD_DATA_USER_TAR_USER: TypeAlias = Tuple[
    Text, PayloadParam, TokenData, UserInDB, UserInDB
]
TYPE_TOKEN_PAYLOAD_DATA_USER_ORG: TypeAlias = Tuple[
    Text, PayloadParam, TokenData, UserInDB, Organization
]
TYPE_TOKEN_PAYLOAD_DATA_USER_ORG_TAR_USER: TypeAlias = Tuple[
    Text, PayloadParam, TokenData, UserInDB, Organization, UserInDB
]


async def depend_token(token: Text = Depends(oauth2_scheme)) -> Text:
    return token


async def depend_token_payload(
    token: Text = Depends(depend_token),
) -> TYPE_TOKEN_PAYLOAD:
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


async def depend_current_token_payload(
    token_payload: Annotated[TYPE_TOKEN_PAYLOAD, Depends(depend_token_payload)]
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


async def depend_current_active_token_payload(
    token_payload: Annotated[TYPE_TOKEN_PAYLOAD, Depends(depend_current_token_payload)],
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


async def depend_current_active_token_payload_data(
    token_payload: Annotated[
        TYPE_TOKEN_PAYLOAD, Depends(depend_current_active_token_payload)
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


async def depend_current_user(
    token_payload_data: Annotated[
        TYPE_TOKEN_PAYLOAD_DATA, Depends(depend_current_active_token_payload_data)
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


async def depend_current_active_user(
    token_payload_data_user: Annotated[
        TYPE_TOKEN_PAYLOAD_DATA_USER, Depends(depend_current_user)
    ]
) -> TYPE_TOKEN_PAYLOAD_DATA_USER:
    current_user = token_payload_data_user[3]
    if current_user.disabled:
        logger.debug(f"User '{current_user.username}' is inactive")
        raise HTTPException(status_code=400, detail="Inactive user")
    return token_payload_data_user


async def depend_querying_user(
    user_id: Text = QueryPath(..., description="The ID of the user to retrieve."),
    db: DatabaseBase = Depends(depend_db),
):
    user = await run_as_coro(db.retrieve_user, user_id=user_id)
    if user is None:
        logger.debug(f"User '{user_id}' not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


async def depend_current_org(
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


async def depend_current_active_org(
    current_org: Organization = Depends(depend_current_org),
):
    if current_org.disabled:
        logger.debug(f"Organization '{current_org.id}' is inactive")
        raise HTTPException(status_code=400, detail="Inactive organization")
    return current_org


async def depend_user_of_platform(
    token_payload_data_user: TYPE_TOKEN_PAYLOAD_DATA_USER = Depends(
        depend_current_active_user
    ),
) -> TYPE_TOKEN_PAYLOAD_DATA_USER:
    user = token_payload_data_user[3]
    if user.role in (Role.SUPER_ADMIN, Role.PLATFORM_ADMIN):
        pass
    else:
        logger.debug(f"User '{user.username}' is not a platform user")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
        )
    return token_payload_data_user


async def depend_user_of_platform_managing_user(
    target_user: UserInDB = Depends(depend_querying_user),
    token_payload_data_user: TYPE_TOKEN_PAYLOAD_DATA_USER = Depends(
        depend_current_active_user
    ),
) -> TYPE_TOKEN_PAYLOAD_DATA_USER_TAR_USER:
    user = token_payload_data_user[3]

    if ROLE_AUTH_LEVELS[target_user.role] > ROLE_AUTH_LEVELS[user.role]:
        logger.debug(
            f"User '{user.username}' cannot manage user '{target_user.id}' with higher role"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
        )
    elif user.role in (Role.SUPER_ADMIN, Role.PLATFORM_ADMIN):
        pass
    elif target_user.role == Role.SUPER_ADMIN:
        logger.debug(
            f"User '{user.username}' cannot manage Super Admin '{target_user.id}'"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
        )
    return (
        token_payload_data_user[0],
        token_payload_data_user[1],
        token_payload_data_user[2],
        user,
        target_user,
    )


async def depend_user_of_platform_managing_org(
    org: Organization = Depends(depend_current_org),
    token_payload_data_user: TYPE_TOKEN_PAYLOAD_DATA_USER = Depends(
        depend_current_active_user
    ),
) -> TYPE_TOKEN_PAYLOAD_DATA_USER_ORG:
    user = token_payload_data_user[3]

    if user.role not in (Role.SUPER_ADMIN, Role.PLATFORM_ADMIN):
        logger.debug(f"User '{user.username}' is not a platform user")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
        )
    return (
        token_payload_data_user[0],
        token_payload_data_user[1],
        token_payload_data_user[2],
        user,
        org,
    )


async def depend_user_of_org(
    org: Organization = Depends(depend_current_active_org),
    token_payload_data_user: TYPE_TOKEN_PAYLOAD_DATA_USER = Depends(
        depend_current_active_user
    ),
) -> TYPE_TOKEN_PAYLOAD_DATA_USER_ORG:
    user = token_payload_data_user[3]

    if user.role in (Role.SUPER_ADMIN, Role.PLATFORM_ADMIN):
        pass
    elif user.organization_id != org.id:
        logger.debug(
            f"User '{user.username}' is not a member of organization '{org.id}'"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
        )
    return (
        token_payload_data_user[0],
        token_payload_data_user[1],
        token_payload_data_user[2],
        user,
        org,
    )


async def depend_user_of_org_managing_user(
    target_user: UserInDB = Depends(depend_querying_user),
    token_payload_data_user_org: TYPE_TOKEN_PAYLOAD_DATA_USER_ORG = Depends(
        depend_user_of_org
    ),
) -> TYPE_TOKEN_PAYLOAD_DATA_USER_ORG_TAR_USER:
    user = token_payload_data_user_org[3]
    org = token_payload_data_user_org[4]

    if ROLE_AUTH_LEVELS[target_user.role] > ROLE_AUTH_LEVELS[user.role]:
        logger.debug(
            f"User '{user.username}' cannot manage user '{target_user.id}' with higher role"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
        )
    elif user.role in (Role.SUPER_ADMIN, Role.PLATFORM_ADMIN):
        pass
    elif user.role == Role.ORG_ADMIN:
        if target_user.organization_id != org.id:
            logger.debug(
                f"User '{user.username}' is not a member of organization '{org.id}'"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
            )
    elif user.role == Role.ORG_USER:  # User can only manage themselves
        if target_user.organization_id != org.id or target_user.id != user.id:
            logger.debug(
                f"User '{user.username}' is not a member of organization '{org.id}'"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
            )
    return (
        token_payload_data_user_org[0],
        token_payload_data_user_org[1],
        token_payload_data_user_org[2],
        user,
        org,
        target_user,
    )


def UserPermissionChecker(
    required_permissions: List[Permission],
    depends_type: (
        Literal[
            "platform_user",
            "platform_user_managing_user",
            "platform_user_managing_org",
            "org_user",
            "org_user_managing_user",
        ]
        | None
    ) = None,
):
    """Check if the current user has the required permissions."""

    def _depend_basic_user_permissions(_payload: T) -> T:
        user: UserInDB = _payload[3]  # Get the user from the payload # type: ignore
        user_permissions = ROLE_PERMISSIONS[user.role].permissions
        logger.debug(
            f"User '{user.username}' with role '{user.role}' "
            + f"has permissions '{user_permissions}'"
        )
        # Check if the user has the required permissions
        if Permission.MANAGE_ALL_RESOURCES in user_permissions:
            return _payload  # Super Admin has all permissions
        if not set(required_permissions).issubset(set(user_permissions)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
            )
        return _payload

    def _depend_platform_user(
        token_payload_data_user: TYPE_TOKEN_PAYLOAD_DATA_USER = Depends(
            depend_user_of_platform
        ),
    ) -> TYPE_TOKEN_PAYLOAD_DATA_USER:
        return _depend_basic_user_permissions(token_payload_data_user)

    def _depend_platform_user_managing_user(
        token_payload_data_user_tar_user: TYPE_TOKEN_PAYLOAD_DATA_USER_TAR_USER = Depends(
            depend_user_of_platform_managing_user
        ),
    ) -> TYPE_TOKEN_PAYLOAD_DATA_USER_TAR_USER:
        return _depend_basic_user_permissions(token_payload_data_user_tar_user)

    def _depend_platform_user_managing_org(
        token_payload_data_user_org: TYPE_TOKEN_PAYLOAD_DATA_USER_ORG = Depends(
            depend_user_of_platform_managing_org
        ),
    ) -> TYPE_TOKEN_PAYLOAD_DATA_USER_ORG:
        return _depend_basic_user_permissions(token_payload_data_user_org)

    def _depend_org_user(
        token_payload_data_user_org: TYPE_TOKEN_PAYLOAD_DATA_USER_ORG = Depends(
            depend_user_of_org
        ),
    ) -> TYPE_TOKEN_PAYLOAD_DATA_USER_ORG:
        token_payload_data_user_org = _depend_basic_user_permissions(
            token_payload_data_user_org
        )
        # Additional checks for organization-specific permissions
        if (
            Permission.MANAGE_ORG_CONTENT in required_permissions
            or Permission.MANAGE_ORG_USERS in required_permissions
        ):
            pass
        return token_payload_data_user_org

    def _depend_org_user_managing_user(
        token_payload_data_user_org_tar_user: TYPE_TOKEN_PAYLOAD_DATA_USER_ORG_TAR_USER = Depends(
            depend_user_of_org_managing_user
        ),
    ) -> TYPE_TOKEN_PAYLOAD_DATA_USER_ORG_TAR_USER:
        token_payload_data_user_org_tar_user = _depend_basic_user_permissions(
            token_payload_data_user_org_tar_user
        )
        # Additional checks for organization-specific permissions
        if (
            Permission.MANAGE_ORG_CONTENT in required_permissions
            or Permission.MANAGE_ORG_USERS in required_permissions
        ):
            pass
        return token_payload_data_user_org_tar_user

    if depends_type == "platform_user":
        return _depend_platform_user
    elif depends_type == "platform_user_managing_user":
        return _depend_platform_user_managing_user
    elif depends_type == "platform_user_managing_org":
        return _depend_platform_user_managing_org
    elif depends_type == "org_user":
        return _depend_org_user
    elif depends_type == "org_user_managing_user":
        return _depend_org_user_managing_user
    else:
        return _depend_basic_user_permissions
