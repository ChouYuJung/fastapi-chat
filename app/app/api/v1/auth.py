from typing import Text

from app.schemas.oauth import Token
from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
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
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented"
    )


@router.post("/logout")
async def logout(token: Text = Query(...)):
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented"
    )


@router.post("/refresh-token", response_model=Token)
async def refresh_token(refresh_token: RefreshToken = Body(...)):
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented"
    )
