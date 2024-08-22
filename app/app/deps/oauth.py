import time
from typing import Annotated, List, Text, Tuple

from app.config import logger
from app.db.tokens import fake_token_blacklist, is_token_invalid
from app.db.users import fake_users_db, get_user
from app.schemas.oauth import PayloadParam, Role, TokenData, User, UserInDB
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
    ]
) -> Tuple[Text, PayloadParam]:

    token = token_payload[0]
    if is_token_invalid(fake_token_blacklist, token=token):
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
    ]
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
    user = get_user(fake_users_db, username=token_data.username)
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


def RoleChecker(allowed_roles: List[Role]):
    """
    Decorator function for role-based access control.

    This function checks if the user's role, extracted from the JWT token,
    is included in the list of allowed roles. If not, raises an HTTP
    exception.

    Parameters
    ----------
    allowed_roles : List[Role]
        A list of allowed roles for the decorated endpoint.

    Returns
    -------
    Callable
        The inner function `check_role` that performs the actual role check.

    Raises
    ------
    HTTPException
        * Status code 401 (Unauthorized) if the token is invalid.
        * Status code 403 (Forbidden) if the user's role is not allowed.

    Examples
    --------
    >>> from app.schemas.oauth import Role
    >>> @app.get("/admin", dependencies=[Depends(RoleChecker([Role.ADMIN]))])
    >>> async def admin_endpoint():
    >>>     return {"message": "Admin access granted"}
    """

    async def check_role(token: Text = Depends(oauth2_scheme)):
        # Verify the token and check the user's role.
        payload = verify_token(token)
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )
        # Check if the token is in the blacklist.
        if is_token_invalid(fake_token_blacklist, token=token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been invalidated",
            )
        # Check if the user's role is allowed.
        role = payload.get("role")
        if role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Operation not permitted"
            )
        return payload

    return check_role
