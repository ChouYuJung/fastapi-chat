from datetime import timedelta
from typing import Annotated, Text

from app.config import settings
from app.db.users import fake_users_db, get_user_by_id
from app.db.users import list_users as list_db_users
from app.db.users import update_user as update_db_user
from app.deps.oauth import get_current_active_user
from app.schemas.oauth import Token, User
from app.utils.oauth import authenticate_user, create_access_token, invalidate_token
from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, ConfigDict, EmailStr

router = APIRouter()


class RefreshToken(BaseModel):
    refresh_token: Text


@router.post("/register", response_model=Token)
async def register(user: UserRegister = Body(...)) -> Token:

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented"
    )


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()) -> Token:
    """Authenticate a user with the given username and password."""

    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=access_token_expires,
    )
    return Token.model_validate({"access_token": access_token, "token_type": "bearer"})


@router.post("/logout")
async def logout(current_user: Annotated[User, Depends(get_current_active_user)]):
    """Invalidate the token for the given user.
    TODO: Implement logout to invalidate the token.
    """

    invalidate_token(current_user.username)
    return JSONResponse(
        content={"message": "Successfully logged out"},
        status_code=status.HTTP_200_OK,
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, private",
            "Pragma": "no-cache",
        },
    )


@router.post("/refresh-token", response_model=Token)
async def refresh_token(
    current_user: Annotated[User, Depends(get_current_active_user)]
) -> Token:
    """Refresh the access token for the current user.
    TODO: Implement refresh token to invalidate the old token and return a new token.
    """

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access_token = create_access_token(
        data={"sub": current_user.username}, expires_delta=access_token_expires
    )
    return Token.model_validate(
        {"access_token": new_access_token, "token_type": "bearer"}
    )
