from typing import Annotated, Literal, Optional, Text

from app.db._base import DatabaseBase
from app.db.organizations import retrieve_organization
from app.db.users import create_user, get_user_by_id, list_users, update_user
from app.deps.db import depend_db
from app.deps.oauth import get_current_active_user, get_user_with_required_permissions
from app.schemas.oauth import (
    Organization,
    Permission,
    Role,
    User,
    UserCreate,
    UserUpdate,
)
from app.schemas.pagination import Pagination
from app.utils.oauth import get_password_hash
from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi import Path as QueryPath
from fastapi import Query, status

router = APIRouter()


async def _can_user_manage_the_org(
    db: "DatabaseBase", *, org_id: Text, user: "User"
) -> "Organization":
    """Retrieve an organization by its ID with user permission checking."""

    org = await retrieve_organization(db, organization_id=org_id)

    # Check if the organization exists
    if org is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
        )

    # Check if the current user has permission to access the organization
    if user is not None and user.organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this organization",
        )

    return org


@router.get("/organizations/{org_id}/users/me")
async def read_users_me(
    org_id: Text = QueryPath(..., min_length=4, max_length=64),
    current_user: User = Depends(get_current_active_user),
    db: DatabaseBase = Depends(depend_db),
) -> User:
    """Retrieve the current user."""

    await _can_user_manage_the_org(db, org_id=org_id, user=current_user)
    if current_user.organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this organization",
        )
    return current_user


@router.get("/organizations/{org_id}/users")
async def api_list_users(
    org_id: Text = QueryPath(..., min_length=4, max_length=64),
    disabled: Optional[bool] = Query(False),
    sort: Literal["asc", "desc"] = Query("asc"),
    start: Optional[Text] = Query(None),
    before: Optional[Text] = Query(None),
    limit: Optional[int] = Query(10, ge=1, le=100),
    current_user: User = Depends(
        get_user_with_required_permissions([Permission.MANAGE_ORG_USERS])
    ),
    db: DatabaseBase = Depends(depend_db),
) -> Pagination[User]:
    """Search for users by username or other criteria."""

    await _can_user_manage_the_org(db, org_id=org_id, user=current_user)

    return Pagination[User].model_validate(
        list_users(
            db, disabled=disabled, sort=sort, start=start, before=before, limit=limit
        ).model_dump()
    )


@router.post("/organizations/{org_id}/users")
async def api_create_user(
    org_id: Text = QueryPath(..., min_length=4, max_length=64),
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
    ),
    current_user: User = Depends(
        get_user_with_required_permissions([Permission.MANAGE_ORG_USERS])
    ),
    db: DatabaseBase = Depends(depend_db),
) -> User:
    """Create a new user."""

    await _can_user_manage_the_org(db, org_id=org_id, user=current_user)

    created_user = create_user(
        db,
        user_create=user_create,
        hashed_password=get_password_hash(user_create.password),
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
async def api_retrieve_user(
    user_id: Text = QueryPath(..., min_length=4, max_length=64),
    db: DatabaseBase = Depends(depend_db),
) -> User:
    """Retrieve user profile information."""

    user = get_user_by_id(db, user_id=user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


@router.put(
    "/users/{user_id}",
    dependencies=[Depends(RoleChecker([Role.ADMIN]))],
)
async def api_update_user(
    user_id: Text,
    user_update: UserUpdate = Body(...),
    db: DatabaseBase = Depends(depend_db),
) -> User:
    """Update user profile information."""

    user = update_user(db, user_id=user_id, user_update=user_update)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user
