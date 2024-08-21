from typing import Annotated, Literal, Optional, Text

from app.db.users import list_users as list_db_users
from app.deps.oauth import RoleChecker, get_current_active_user
from app.schemas.oauth import Role, User
from app.schemas.pagination import Pagination
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


@router.get(
    "/users/me",
    dependencies=[Depends(RoleChecker([Role.ADMIN, Role.CONTRIBUTOR, Role.VIEWER]))],
)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)]
) -> User:
    """Retrieve the current user."""

    return current_user


@router.get(
    "/users",
    dependencies=[Depends(RoleChecker([Role.ADMIN, Role.CONTRIBUTOR]))],
)
async def list_users(
    disabled: Optional[bool] = Query(False),
    sort: Literal["asc", "desc"] = Query("asc"),
    start: Optional[Text] = Query(None),
    before: Optional[Text] = Query(None),
    limit: Optional[int] = Query(10, ge=1, le=100),
) -> Pagination[User]:
    """Search for users by username or other criteria."""

    return Pagination[User].model_validate(
        list_db_users(
            disabled=disabled, sort=sort, start=start, before=before, limit=limit
        ).model_dump()
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
