from typing import Annotated, Literal, Optional, Text

from app.db.users import create_user as create_db_user
from app.db.users import get_user_by_id
from app.db.users import list_users as list_db_users
from app.db.users import update_user as update_db_user
from app.deps.oauth import RoleChecker, get_current_active_user
from app.schemas.oauth import Role, User, UserCreate, UserUpdate
from app.schemas.pagination import Pagination
from app.utils.oauth import get_password_hash
from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi import Path as QueryPath
from fastapi import Query, status

router = APIRouter()


@router.get(
    "/users/me",
    dependencies=[Depends(RoleChecker([Role.ADMIN, Role.EDITOR, Role.VIEWER]))],
)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)]
) -> User:
    """Retrieve the current user."""

    return current_user


@router.get(
    "/users",
    dependencies=[Depends(RoleChecker([Role.ADMIN, Role.EDITOR]))],
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
async def create_user(
    user_create: UserCreate = Body(
        ...,
        openapi_examples={
            "guest_user": {
                "summary": "Create a new guest user",
                "value": {
                    "username": "new_guest",
                    "email": "guest@example.com",
                    "password": "pass1234",
                    "full_name": "New Guest User",
                    "role": "viewer",
                },
            }
        },
    )
) -> User:
    """Create a new user."""

    user = user_create.to_user()
    created_user = create_db_user(
        user=user, hashed_password=get_password_hash(user_create.password)
    )
    if created_user is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="User already exists"
        )
    return created_user


@router.get(
    "/users/{user_id}",
    dependencies=[Depends(RoleChecker([Role.ADMIN, Role.EDITOR]))],
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
