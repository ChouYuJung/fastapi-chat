import time
from typing import Annotated, List, Text

from app.config import settings
from app.db.users import fake_users_db, get_user
from app.schemas.oauth import Role, TokenData, User
from app.utils.oauth import oauth2_scheme, verify_token
from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt


async def get_current_user(token: Annotated[Text, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token_expired_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token expired",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        username: Text = payload.get("sub")  # type: ignore
        expires: int = payload.get("exp")  # type: ignore
        if username is None:
            raise credentials_exception
        if time.time() > expires:
            raise token_expired_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    if token_data.username is None:
        raise credentials_exception
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
):
    if current_user.disabled:
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
        payload = verify_token(token)
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )
        role = payload.get("role")
        if role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Operation not permitted"
            )
        return payload

    return check_role
