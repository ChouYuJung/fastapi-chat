from typing import Literal, Optional, Text

from app.db._base import DatabaseBase
from app.db.users import create_user, get_user_by_id, list_users, update_user
from app.deps.db import depend_db
from app.deps.oauth import (
    TYPE_TOKEN_PAYLOAD_DATA_USER_ORG,
    get_user_of_org_with_required_permissions,
)
from app.schemas.oauth import User, UserCreate, UserUpdate
from app.schemas.pagination import Pagination
from app.utils.oauth import get_password_hash
from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi import Path as QueryPath
from fastapi import Query, status

router = APIRouter()


@router.get("/organizations/{org_id}/users/me")
async def read_users_me(
    token_payload_data_user_org: TYPE_TOKEN_PAYLOAD_DATA_USER_ORG = Depends(
        get_user_of_org_with_required_permissions
    ),
) -> User:
    """Retrieve the current user."""

    user = token_payload_data_user_org[3]
    return user


@router.get("/organizations/{org_id}/users")
async def api_list_users(
    disabled: Optional[bool] = Query(False),
    sort: Literal["asc", "desc"] = Query("asc"),
    start: Optional[Text] = Query(None),
    before: Optional[Text] = Query(None),
    limit: Optional[int] = Query(10, ge=1, le=100),
    token_payload_data_user_org: TYPE_TOKEN_PAYLOAD_DATA_USER_ORG = Depends(
        get_user_of_org_with_required_permissions
    ),
    db: DatabaseBase = Depends(depend_db),
) -> Pagination[User]:
    """Search for users by username or other criteria."""

    assert token_payload_data_user_org[3]
    return Pagination[User].model_validate(
        list_users(
            db, disabled=disabled, sort=sort, start=start, before=before, limit=limit
        ).model_dump()
    )


@router.post("/organizations/{org_id}/users")
async def api_create_user(
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
    token_payload_data_user_org: TYPE_TOKEN_PAYLOAD_DATA_USER_ORG = Depends(
        get_user_of_org_with_required_permissions
    ),
    db: DatabaseBase = Depends(depend_db),
) -> User:
    """Create a new user."""

    assert token_payload_data_user_org[3]
    org_id = token_payload_data_user_org[4]

    created_user = create_user(
        db,
        user_create=user_create,
        hashed_password=get_password_hash(user_create.password),
        organization_id=org_id,
        allow_organization_empty=False,
    )
    if created_user is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="User already exists"
        )
    return created_user


@router.get("/organizations/{org_id}/users/{user_id}")
async def api_retrieve_user(
    user_id: Text = QueryPath(..., min_length=4, max_length=64),
    token_payload_data_user_org: TYPE_TOKEN_PAYLOAD_DATA_USER_ORG = Depends(
        get_user_of_org_with_required_permissions
    ),
    db: DatabaseBase = Depends(depend_db),
) -> User:
    """Retrieve user profile information."""

    assert token_payload_data_user_org[3]

    user = get_user_by_id(db, user_id=user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


@router.put("/organizations/{org_id}/users/{user_id}")
async def api_update_user(
    user_id: Text,
    user_update: UserUpdate = Body(...),
    token_payload_data_user_org: TYPE_TOKEN_PAYLOAD_DATA_USER_ORG = Depends(
        get_user_of_org_with_required_permissions
    ),
    db: DatabaseBase = Depends(depend_db),
) -> User:
    """Update user profile information."""

    assert token_payload_data_user_org[3]

    user = update_user(db, user_id=user_id, user_update=user_update)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user
