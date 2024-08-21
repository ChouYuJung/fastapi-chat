from typing import Annotated, Literal, Optional, Text

from app.db.users import get_user_by_id
from app.db.users import list_users as list_db_users
from app.db.users import update_user as update_db_user
from app.deps.oauth import RoleChecker, get_current_active_user
from app.schemas.oauth import Role, User, UserCreate, UserUpdate
from app.schemas.pagination import Pagination
from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi import Path as QueryPath
from fastapi import Query, status
from pydantic import BaseModel, ConfigDict, EmailStr, Field

router = APIRouter()


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


@router.post(
    "/users",
    dependencies=[Depends(RoleChecker([Role.ADMIN]))],
)
async def create_user(user_create: UserCreate) -> User:
    """Create a new user."""

    return user


@router.get(
    "/users/{user_id}",
    dependencies=[Depends(RoleChecker([Role.ADMIN, Role.CONTRIBUTOR]))],
)
async def retrieve_user(
    user_id: Text = QueryPath(..., min_length=4, max_length=64),
) -> User:
    """Retrieve user profile information."""

    user = get_user_by_id(user_id=user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


@router.put(
    "/users/{user_id}",
    dependencies=[Depends(RoleChecker([Role.ADMIN]))],
)
async def update_user(user_id: Text, user_update: UserUpdate = Body(...)) -> User:
    """Update user profile information."""

    user = update_db_user(
        user_id=user_id, update_data=user_update.model_dump(exclude_none=True)
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user
