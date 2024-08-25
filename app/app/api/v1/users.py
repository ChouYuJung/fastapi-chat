from datetime import timedelta
from typing import Literal, Optional, Text

from app.config import settings
from app.db._base import DatabaseBase
from app.db.tokens import caching_token
from app.db.users import create_user, get_user_by_id, list_users, update_user
from app.deps.db import depend_db
from app.deps.oauth import (
    TYPE_TOKEN_PAYLOAD_DATA_USER_ORG,
    get_user_of_org_with_required_permissions,
)
from app.schemas.oauth import (
    ROLE_PERMISSIONS,
    Permission,
    Token,
    User,
    UserCreate,
    UserGuestRegister,
    UserUpdate,
)
from app.schemas.pagination import Pagination
from app.utils.oauth import create_token_model, get_password_hash
from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi import Path as QueryPath
from fastapi import Query, status

router = APIRouter()


@router.get("/organizations/{org_id}/users/me")
async def read_users_me(
    token_payload_data_user_org: TYPE_TOKEN_PAYLOAD_DATA_USER_ORG = Depends(
        get_user_of_org_with_required_permissions([Permission.USE_ORG_CONTENT])
    ),
) -> User:
    """Retrieve the current user."""

    org_id = token_payload_data_user_org[4]
    user = token_payload_data_user_org[3]
    if user.organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this organization",
        )
    return user


@router.post("/organizations/{org_id}/users/register", response_model=Token)
async def api_register(
    user_guest_register: UserGuestRegister = Body(
        ...,
        openapi_examples={
            "guest_user": {
                "summary": "Create a new guest user",
                "value": {
                    "username": "new_guest",
                    "password": "pass1234",
                    "full_name": "Guest User",
                    "email": "guest@example.com",
                },
            },
        },
    ),
    token_payload_data_user_org: TYPE_TOKEN_PAYLOAD_DATA_USER_ORG = Depends(
        get_user_of_org_with_required_permissions([Permission.MANAGE_ORG_USERS])
    ),
    db: DatabaseBase = Depends(depend_db),
) -> Token:
    """Register a new user with the given username and password."""

    org_id = token_payload_data_user_org[4]
    api_user = token_payload_data_user_org[3]

    # API user could not register a user with a role higher or equal to their own.
    if (
        ROLE_PERMISSIONS[user_guest_register.role].authority_level
        >= ROLE_PERMISSIONS[api_user.role].authority_level
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to create a user with this role",
        )

    # Create a new user with the given username and password.
    created_user = create_user(
        db,
        user_create=user_guest_register,
        hashed_password=get_password_hash(user_guest_register.password),
        organization_id=org_id,
        allow_organization_empty=False,
    )
    if created_user is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="User already exists"
        )

    # Create an access token for the new user.
    token = create_token_model(
        data={"sub": created_user.username, "role": created_user.role},
        access_token_expires_delta=timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        ),
        refresh_token_expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )

    # Save the token to the database.
    caching_token(db, username=created_user.username, token=token)

    # Return the access token.
    return token


@router.get("/organizations/{org_id}/users")
async def api_list_users(
    disabled: Optional[bool] = Query(False),
    sort: Literal["asc", "desc"] = Query("asc"),
    start: Optional[Text] = Query(None),
    before: Optional[Text] = Query(None),
    limit: Optional[int] = Query(10, ge=1, le=100),
    token_payload_data_user_org: TYPE_TOKEN_PAYLOAD_DATA_USER_ORG = Depends(
        get_user_of_org_with_required_permissions([Permission.MANAGE_ORG_USERS])
    ),
    db: DatabaseBase = Depends(depend_db),
) -> Pagination[User]:
    """Search for users by username or other criteria."""

    org_id = token_payload_data_user_org[4]
    assert token_payload_data_user_org[3]
    return Pagination[User].model_validate(
        list_users(
            db,
            organization_id=org_id,
            disabled=disabled,
            sort=sort,
            start=start,
            before=before,
            limit=limit,
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
        get_user_of_org_with_required_permissions([Permission.MANAGE_ORG_USERS])
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
        get_user_of_org_with_required_permissions([Permission.MANAGE_ORG_USERS])
    ),
    db: DatabaseBase = Depends(depend_db),
) -> User:
    """Retrieve user profile information."""

    org_id = token_payload_data_user_org[4]
    assert token_payload_data_user_org[3]

    user = get_user_by_id(db, organization_id=org_id, user_id=user_id)
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
        get_user_of_org_with_required_permissions([Permission.MANAGE_ORG_USERS])
    ),
    db: DatabaseBase = Depends(depend_db),
) -> User:
    """Update user profile information."""

    org_id = token_payload_data_user_org[4]
    assert token_payload_data_user_org[3]

    user = update_user(
        db, organization_id=org_id, user_id=user_id, user_update=user_update
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user
