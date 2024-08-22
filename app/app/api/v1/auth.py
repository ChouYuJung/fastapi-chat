from datetime import timedelta
from typing import Annotated, Text

from app.config import logger, settings
from app.db.tokens import (
    create_token,
    fake_token_blacklist,
    fake_token_db,
    get_token,
    invalidate_token,
    is_token_invalid,
    logout_user,
)
from app.db.users import create_user, fake_users_db
from app.deps.oauth import get_current_active_user
from app.schemas.oauth import Token, User, UserGuestRegister
from app.utils.oauth import (
    authenticate_user,
    create_access_token,
    get_password_hash,
    is_token_expired,
    oauth2_scheme,
    verify_payload,
    verify_token,
)
from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

router = APIRouter()


class RefreshToken(BaseModel):
    refresh_token: Text


@router.post("/register", response_model=Token)
async def api_register(
    user_guest_register: UserGuestRegister = Body(
        ...,
        openapi_examples={
            "guest_user": {
                "summary": "Create a new guest user",
                "value": {
                    "username": "new_guest",
                    "password": "pass1234",
                    "full_name": "Guest User",
                    "email": "guest@example.com",
                },
            },
        },
    )
) -> Token:
    """Register a new user with the given username and password."""

    # Create a new user with the given username and password.
    user = user_guest_register.to_user()
    created_user = create_user(
        user=user, hashed_password=get_password_hash(user_guest_register.password)
    )
    if created_user is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="User already exists"
        )

    # Create an access token for the new user.
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": created_user.username, "role": created_user.role},
        expires_delta=access_token_expires,
    )

    # Save the token to the database.
    create_token(fake_token_db, username=created_user.username, token=access_token)

    # Return the access token.
    return Token.from_bearer_token(access_token)


@router.post("/login", response_model=Token)
async def api_login(form_data: OAuth2PasswordRequestForm = Depends()) -> Token:
    """Authenticate a user with the given username and password."""

    # Authenticate the user with the given username and password.
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        logger.debug(f"User '{form_data.username}' failed to authenticate")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if token exists in the database
    access_token: Text
    token_exists = get_token(fake_token_db, username=user.username)
    if token_exists is not None:
        access_token = token_exists
        logger.debug(f"User '{form_data.username}' already has a token")
        return Token.from_bearer_token(access_token)
    # Create an access token for the authenticated user.
    else:
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username, "role": user.role},
            expires_delta=access_token_expires,
        )

    # Save the token to the database.
    create_token(fake_token_db, username=user.username, token=access_token)

    # Return the access token.
    return Token.from_bearer_token(access_token)


@router.post("/logout")
async def api_logout(token: Annotated[Text, Depends(oauth2_scheme)]):
    """Invalidate the token for the given user."""

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Verify the token and invalidate it.
    payload = verify_token(token)
    if payload is None:
        raise credentials_exception
    payload = verify_payload(payload)
    if payload is None:
        raise credentials_exception
    if is_token_expired(payload):
        credentials_exception.detail = "Token expired"
        raise credentials_exception

    # Check if token is inactivated
    if is_token_invalid(fake_token_blacklist, token=token):
        credentials_exception.detail = "Token has been invalidated"
        raise credentials_exception

    # Logout user by setting the token disable
    username = payload.get("sub")
    if not isinstance(username, Text):
        raise credentials_exception
    existing_token = get_token(fake_token_db, username=username)
    if existing_token is None:
        raise credentials_exception
    logout_user(fake_token_db, username=username)

    # Invalidate the token.
    invalidate_token(fake_token_blacklist, token=token)

    # Return a response.
    return JSONResponse(
        content={"message": "Successfully logged out"},
        status_code=status.HTTP_200_OK,
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, private",
            "Pragma": "no-cache",
        },
    )


@router.post("/refresh-token", response_model=Token)
async def api_refresh_token(
    current_user: Annotated[User, Depends(get_current_active_user)]
) -> Token:
    """Refresh the access token for the current user.
    TODO: Implement refresh token to invalidate the old token and return a new token.
    """

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access_token = create_access_token(
        data={"sub": current_user.username}, expires_delta=access_token_expires
    )
    return Token.from_bearer_token(new_access_token)
