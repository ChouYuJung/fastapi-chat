from datetime import timedelta
from typing import Annotated, Text

from app.config import settings
from app.db.users import fake_users_db
from app.deps.oauth import get_current_active_user
from app.schemas.oauth import LoginResponse, Token, User
from app.utils.oauth import authenticate_user, create_access_token, invalidate_token
from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr

router = APIRouter()


class UserRegister(BaseModel):
    username: Text
    email: EmailStr
    password: Text
    full_name: Text


class UserLogin(BaseModel):
    username: Text
    password: Text


class RefreshToken(BaseModel):
    refresh_token: Text


@router.post("/register", response_model=Token)
async def register(user: UserRegister):
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented"
    )


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()) -> LoginResponse:
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
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return LoginResponse.model_validate(
        {"access_token": access_token, "token_type": "bearer"}
    )


@router.post("/logout")
async def logout(current_user: Annotated[User, Depends(get_current_active_user)]):
    """Invalidate the token for the given user."""

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
async def refresh_token(refresh_token: RefreshToken = Body(...)):
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented"
    )
