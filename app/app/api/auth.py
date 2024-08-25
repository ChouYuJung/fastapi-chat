from datetime import timedelta
from typing import Annotated, Text, Tuple

from app.config import logger, settings
from app.db._base import DatabaseBase
from app.db.tokens import caching_token, invalidate_token, retrieve_cached_token
from app.deps.db import depend_db
from app.deps.oauth import (
    get_current_active_token_payload,
    get_current_active_token_payload_data,
    get_current_active_user,
    get_current_token_payload,
    get_current_user,
    get_token_payload,
)
from app.schemas.oauth import PayloadParam, RefreshTokenRequest, Token
from app.utils.oauth import (
    authenticate_user,
    create_token_model,
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


@router.post("/login", response_model=Token)
async def api_login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: DatabaseBase = Depends(depend_db),
) -> Token:
    """Authenticate a user with the given username and password."""

    # Authenticate the user with the given username and password.
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        logger.debug(f"User '{form_data.username}' failed to authenticate")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Return if token active
    token = retrieve_cached_token(db, username=user.username)
    if token is not None and is_token_expired(token.access_token) is False:
        logger.debug(f"User '{form_data.username}' already has a token")
        return token

    # Create an access token for the authenticated user.
    token = create_token_model(
        data={
            "sub": user.username,
            "role": user.role,
            "organization_id": user.organization_id,
        },
        access_token_expires_delta=timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        ),
        refresh_token_expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )

    # Save the token to the database.
    caching_token(db, username=user.username, token=token)

    # Return the access token.
    return token


@router.post("/logout")
async def api_logout(
    token_payload: Annotated[
        Tuple[Text, PayloadParam], Depends(get_current_active_token_payload)
    ],
    db: DatabaseBase = Depends(depend_db),
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

    token = retrieve_cached_token(db, username=username)

    # Logout user and invalidate the token.
    if token is not None:
        invalidate_token(db, token=token)

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
    form_data: RefreshTokenRequest = Body(...),
    db: DatabaseBase = Depends(depend_db),
):
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
    token_payload = await get_current_active_token_payload(
        await get_current_token_payload(
            await get_token_payload(form_data.refresh_token)
        ),
        db=db,
    )
    token_payload_data = await get_current_active_token_payload_data(token_payload)
    token_payload_data_user = await get_current_active_user(
        await get_current_user(token_payload_data, db=db)
    )
    user = token_payload_data_user[3]

    # Create a new access token for the user
    token = create_token_model(
        data={"sub": user.username, "role": user.role},
        access_token_expires_delta=timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        ),
        refresh_token_expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    # Save the new token to the database
    caching_token(db, username=user.username, token=token)

    # Logout user and invalidate the token.
    token_old = retrieve_cached_token(db, username=user.username)
    if token_old is not None:
        invalidate_token(db, token=token_old)

    # Return the new access token
    return token
