from typing import Literal, Optional, Text

from app.db._base import DatabaseBase
from app.db.users import create_user, delete_user, list_users, update_user
from app.deps.db import depend_db
from app.deps.oauth import TYPE_TOKEN_PAYLOAD_DATA_USER_TAR_USER, UserPermissionChecker
from app.schemas.oauth import (
    Permission,
    PlatformUserCreate,
    PlatformUserUpdate,
    Role,
    User,
)
from app.schemas.pagination import Pagination
from app.utils.common import run_as_coro
from app.utils.oauth import get_password_hash
from fastapi import APIRouter, Body, Depends, HTTPException, Query, Response, status

router = APIRouter()


@router.get(
    "/platform/users",
    dependencies=[
        Depends(UserPermissionChecker([Permission.MANAGE_PLATFORM], "platform_user"))
    ],
)
async def api_list_platform_users(
    db: DatabaseBase = Depends(depend_db),
    disabled: Optional[bool] = Query(None),
    sort: Literal["asc", "desc"] = Query("asc"),
    start: Optional[Text] = Query(None),
    before: Optional[Text] = Query(None),
    limit: Optional[int] = Query(20, ge=1, le=100),
) -> Pagination[User]:
    """List users from the database."""

    users_res = await run_as_coro(
        list_users,
        db,
        organization_id=None,
        role=Role.PLATFORM_ADMIN,
        disabled=disabled,
        sort=sort,
        start=start,
        before=before,
        limit=limit,
    )
    return Pagination[User].model_validate(users_res.model_dump())


@router.post(
    "/platform/users",
    dependencies=[
        Depends(UserPermissionChecker([Permission.MANAGE_PLATFORM], "platform_user"))
    ],
)
async def api_create_platform_user(
    user_create: PlatformUserCreate = Body(...),
    db: DatabaseBase = Depends(depend_db),
) -> User:
    """Create a new platform user."""

    created_user = await create_user(
        db,
        user_create=user_create,
        hashed_password=get_password_hash(user_create.password),
        organization_id=None,
        allow_org_empty=True,
    )
    if created_user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this username already exists",
        )
    return created_user


@router.get("/platform/users/{user_id}")
async def api_retrieve_platform_user(
    token_payload_data_user_tar_user: TYPE_TOKEN_PAYLOAD_DATA_USER_TAR_USER = Depends(
        UserPermissionChecker(
            [Permission.MANAGE_PLATFORM], "platform_user_managing_user"
        )
    ),
) -> User:
    """Retrieve a platform user."""

    target_user = token_payload_data_user_tar_user[4]
    return target_user


@router.put("/platform/users/{user_id}")
async def api_update_platform_user(
    token_payload_data_user_tar_user: TYPE_TOKEN_PAYLOAD_DATA_USER_TAR_USER = Depends(
        UserPermissionChecker(
            [Permission.MANAGE_PLATFORM], "platform_user_managing_user"
        )
    ),
    user_update: PlatformUserUpdate = Body(...),
    db: DatabaseBase = Depends(depend_db),
) -> User:
    """Update a platform user."""

    target_user_id = token_payload_data_user_tar_user[4].id
    updated_user = await update_user(
        db, user_id=target_user_id, user_update=user_update
    )
    if updated_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return updated_user


@router.delete("/platform/users/{user_id}")
def api_delete_platform_user(
    token_payload_data_user_tar_user: TYPE_TOKEN_PAYLOAD_DATA_USER_TAR_USER = Depends(
        UserPermissionChecker(
            [Permission.MANAGE_PLATFORM], "platform_user_managing_user"
        )
    ),
    db: DatabaseBase = Depends(depend_db),
) -> Response:
    """Delete a platform user."""

    target_user_id = token_payload_data_user_tar_user[4].id
    success = delete_user(
        db,
        user_id=target_user_id,
        organization_id=None,
        soft_delete=True,
    )
    if success is False:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
