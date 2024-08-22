from datetime import timedelta
from typing import Annotated, Text, Tuple

from app.config import logger, settings
from app.db.tokens import fake_token_db, get_token, logout_user, save_token
from app.db.users import create_user, fake_users_db
from app.deps.oauth import (
    get_current_active_token_payload,
    get_current_active_user,
    get_current_token_payload,
    get_current_user,
    get_token_payload,
)
from app.schemas.oauth import (
    PayloadParam,
    RefreshTokenRequest,
    Token,
    UserGuestRegister,
)
from app.utils.oauth import (
    authenticate_user,
    create_access_and_refresh_tokens,
    get_password_hash,
    is_token_expired,
    validate_client,
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
    access_token, refresh_token = create_access_and_refresh_tokens(
        data={"sub": created_user.username, "role": created_user.role},
        access_token_expires_delta=timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        ),
        refresh_token_expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    token = Token.from_bearer_token(
        access_token=access_token, refresh_token=refresh_token
    )

    # Save the token to the database.
    save_token(fake_token_db, username=created_user.username, token=token)

    # Return the access token.
    return token


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

    # Return if token active
    token = get_token(fake_token_db, username=user.username)
    if token is not None and is_token_expired(token.access_token) is False:
        logger.debug(f"User '{form_data.username}' already has a token")
        return token

    # Create an access token for the authenticated user.
    access_token, refresh_token = create_access_and_refresh_tokens(
        data={"sub": user.username, "role": user.role},
        access_token_expires_delta=timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        ),
        refresh_token_expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    token = Token.from_bearer_token(
        access_token=access_token, refresh_token=refresh_token
    )

    # Save the token to the database.
    save_token(fake_token_db, username=user.username, token=token)

    # Return the access token.
    return token


@router.post("/logout")
async def api_logout(
    token_payload: Annotated[
        Tuple[Text, PayloadParam], Depends(get_current_active_token_payload)
    ]
    # token: Annotated[Text, Depends(oauth2_scheme)]
):
    """Invalidate the token for the given user."""

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = token_payload[1]
    username = payload.get("sub")
    if not isinstance(username, Text):
        raise credentials_exception

    # Logout user and invalidate the token.
    logout_user(fake_token_db, username=username, with_invalidate_token=True)

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
async def api_refresh_token(form_data: RefreshTokenRequest = Body(...)):
    """Refresh the access token for the current user."""

    # Validate grant_type
    if form_data.grant_type != "refresh_token":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid grant_type",
            headers={"WWW-Authenticate": "Bearer error=invalid_request"},
        )

    # Validate client credentials (replace with your actual client validation logic)
    if not validate_client(form_data.client_id, form_data.client_secret):
        raise HTTPException(status_code=401, detail="Invalid client credentials")

    # Validate the user from refresh token and payload
    user = await get_current_active_user(
        await get_current_user(
            await get_current_active_token_payload(
                await get_current_token_payload(
                    await get_token_payload(form_data.refresh_token)
                )
            )
        )
    )

    # Create a new access token for the user
    access_token, refresh_token = create_access_and_refresh_tokens(
        data={"sub": user.username, "role": user.role},
        access_token_expires_delta=timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        ),
        refresh_token_expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    token = Token.from_bearer_token(
        access_token=access_token, refresh_token=refresh_token
    )

    # Invalidate the old token
    logout_user(fake_token_db, username=user.username, with_invalidate_token=True)

    # Save the new token to the database
    save_token(fake_token_db, username=user.username, token=token)

    # Return the new access token
    return token
