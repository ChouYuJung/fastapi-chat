from typing import Literal, Optional, Text

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Response, status

from ..db._base import DatabaseBase
from ..db.users import create_user, delete_user, list_users, update_user
from ..deps.db import depend_db
from ..deps.oauth import (
    DependsUserPermissions,
    TokenUserDepends,
    TokenUserManagingDepends,
)
from ..schemas.pagination import Pagination
from ..schemas.permissions import Permission
from ..schemas.role_per_definitions import get_role_permissions
from ..schemas.roles import Role
from ..schemas.users import PlatformUserCreate, PlatformUserUpdate, User
from ..utils.common import run_as_coro
from ..utils.oauth import get_password_hash

router = APIRouter()


@router.get(
    "/platform/users",
    dependencies=[Depends(DependsUserPermissions([Permission.READ_PLATFORM_USER]))],
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
        roles=[Role.PLATFORM_ADMIN, Role.PLATFORM_EDITOR, Role.PLATFORM_VIEWER],
        disabled=disabled,
        sort=sort,
        start=start,
        before=before,
        limit=limit,
    )
    return Pagination[User].model_validate(users_res.model_dump())


@router.post("/platform/users")
async def api_create_platform_user(
    user_create: PlatformUserCreate = Body(...),
    token_payload_user: TokenUserDepends = Depends(
        DependsUserPermissions([Permission.CREATE_PLATFORM_USER], "depends_active_user")
    ),
    db: DatabaseBase = Depends(depend_db),
) -> User:
    """Create a new platform user."""

    if (
        get_role_permissions(user_create.role).auth_level
        > get_role_permissions(token_payload_user.user.role).auth_level
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "You do not have permission to create a user with "
                + "a higher role than yours"
            ),
        )

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
    token_payload_user_managing: TokenUserManagingDepends = Depends(
        DependsUserPermissions([Permission.READ_PLATFORM_USER], "depends_user_managing")
    ),
) -> User:
    """Retrieve a platform user."""

    target_user = token_payload_user_managing.target_user
    return target_user


@router.put("/platform/users/{user_id}")
async def api_update_platform_user(
    user_update: PlatformUserUpdate = Body(...),
    token_payload_user_managing: TokenUserManagingDepends = Depends(
        DependsUserPermissions(
            [Permission.UPDATE_PLATFORM_USER], "depends_user_managing"
        )
    ),
    db: DatabaseBase = Depends(depend_db),
) -> User:
    """Update a platform user."""

    if (
        get_role_permissions(token_payload_user_managing.target_user.role).auth_level
        > get_role_permissions(token_payload_user_managing.user.role).auth_level
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "You do not have permission to update a user to a role "
                + "with a higher auth level than yours"
            ),
        )

    target_user_id = token_payload_user_managing.user.id
    updated_user = await update_user(
        db, user_id=target_user_id, user_update=user_update
    )
    if updated_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return updated_user


@router.delete("/platform/users/{user_id}")
async def api_delete_platform_user(
    token_payload_user_managing: TokenUserManagingDepends = Depends(
        DependsUserPermissions(
            [Permission.DELETE_PLATFORM_USER], "depends_user_managing"
        )
    ),
    db: DatabaseBase = Depends(depend_db),
) -> Response:
    """Delete a platform user."""

    if (
        get_role_permissions(token_payload_user_managing.target_user.role).auth_level
        > get_role_permissions(token_payload_user_managing.user.role).auth_level
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "You do not have permission to update a user to a role "
                + "with a higher auth level than yours"
            ),
        )

    target_user_id = token_payload_user_managing.user.id
    success = await run_as_coro(
        delete_user,
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
