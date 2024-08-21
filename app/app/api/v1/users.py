from typing import Annotated, Literal, Optional, Text

from app.deps.oauth import get_current_active_user
from app.schemas.oauth import User
from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi import Path as QueryPath
from fastapi import Query, status
from pydantic import BaseModel, ConfigDict, EmailStr, Field

router = APIRouter()


class UserUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    email: Optional[EmailStr] = Field(default=None)
    full_name: Optional[Text] = Field(default=None)
    disabled: Optional[bool] = Field(default=None)


@router.get("/users/me")
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)]
) -> User:
    """Retrieve the current user."""

    return current_user


@router.get("/users")
async def list_users(
    current_user: Annotated[User, Depends(get_current_active_user)],
    disabled: Optional[bool] = Query(False),
    sort: Literal["asc", "desc"] = Query("asc"),
    start: Optional[Text] = Query(None),
    before: Optional[Text] = Query(None),
    limit: Optional[int] = Query(10, ge=1, le=100),
):
    """Search for users by username or other criteria."""

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented"
    )


@router.get("/users/{user_id}")
async def retrieve_user(
    current_user: Annotated[User, Depends(get_current_active_user)],
    user_id: Text = QueryPath(..., min_length=4, max_length=64),
) -> User:
    """Retrieve user profile information."""

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented"
    )


@router.put("/users/{user_id}")
async def update_user(
    current_user: Annotated[User, Depends(get_current_active_user)],
    user_id: Text,
    user_update: UserUpdate = Body(...),
) -> User:
    """Update user profile information."""

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented"
    )
