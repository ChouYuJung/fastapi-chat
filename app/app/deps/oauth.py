import time
from typing import Annotated, List, Text, Tuple

from app.config import logger
from app.db._base import DatabaseBase
from app.db.tokens import is_token_blocked
from app.db.users import get_user
from app.deps.db import depend_db
from app.schemas.oauth import PayloadParam, Permission, Role, TokenData, User, UserInDB
from app.utils.oauth import oauth2_scheme, verify_payload, verify_token
from fastapi import Depends, HTTPException, status


async def get_token_payload(
    token: Text = Depends(oauth2_scheme),
) -> Tuple[Text, PayloadParam]:
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
    token_payload: Annotated[Tuple[Text, PayloadParam], Depends(get_token_payload)]
) -> Tuple[Text, PayloadParam]:
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
    token_payload: Annotated[
        Tuple[Text, PayloadParam], Depends(get_current_token_payload)
    ],
    db: Annotated[DatabaseBase, Depends(depend_db)],
) -> Tuple[Text, PayloadParam]:

    token = token_payload[0]
    if is_token_blocked(db, token=token):
        logger.debug(f"Token '{token}' has been invalidated")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token_payload


async def get_current_user(
    token_payload: Annotated[
        Tuple[Text, PayloadParam], Depends(get_current_active_token_payload)
    ],
    db: Annotated[DatabaseBase, Depends(depend_db)],
) -> UserInDB:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Parse token data
    payload = token_payload[1]
    username = payload.get("sub")
    token_data = TokenData(username=username)
    if token_data.username is None:
        logger.debug(f"Token '{token_payload[0]}' has an invalid username")
        raise credentials_exception

    # Get user from the database
    user = get_user(db, username=token_data.username)
    if user is None:
        logger.debug(f"User '{token_data.username}' not found")
        raise credentials_exception

    # Return the user
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
):
    if current_user.disabled:
        logger.debug(f"User '{current_user.username}' is inactive")
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def require_permissions(required_permissions: List[Permission]):
    def get_current_active_user_permissions(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        if Permission.MANAGE_ALL_RESOURCES in current_user.role.permissions:
            return current_user  # Super Admin has all permissions

        if not set(required_permissions).issubset(set(current_user.role.permissions)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
            )

        return current_user

    return get_current_active_user_permissions


def PermissionChecker(required_permissions: List[Permission]):
    async def check_permission(
        current_user: Annotated[User, Depends(get_current_active_user)],
        db: DatabaseBase = Depends(depend_db),
    ):
        if Permission.MANAGE_ALL_RESOURCES in current_user.role.permissions:
            return  # Super Admin has all permissions

        if not set(required_permissions).issubset(set(current_user.role.permissions)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
            )

        # Additional checks for organization-specific permissions
        if (
            Permission.MANAGE_ORG_CONTENT in required_permissions
            or Permission.MANAGE_ORG_USERS in required_permissions
        ):
            # Ensure the user is operating within their own organization
            # Implement this logic based on your specific requirements
            # TODO:
            pass

    return check_permission
