from datetime import timedelta
from typing import Literal, Optional, Text

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi import Path as QueryPath
from fastapi import Query, Response, status

from ..config import settings
from ..db._base import DatabaseBase
from ..db.organizations import retrieve_organization
from ..db.tokens import caching_token
from ..db.users import create_user, delete_user, get_user_by_id, list_users, update_user
from ..deps.db import depend_db
from ..deps.oauth import (
    DependsUserPermissions,
    TokenOrgDepends,
    TokenOrgUserManagingDepends,
)
from ..schemas.oauth import Token
from ..schemas.pagination import Pagination
from ..schemas.permissions import Permission
from ..schemas.users import User, UserCreate, UserGuestRegister, UserUpdate
from ..utils.common import run_as_coro
from ..utils.oauth import create_token_model, get_password_hash

router = APIRouter()


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
    org_id: Text = QueryPath(..., min_length=4, max_length=64),
    db: DatabaseBase = Depends(depend_db),
) -> Token:
    """Register a new user with the given username and password."""

    org = await retrieve_organization(db, organization_id=org_id)
    if org is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
        )

    # Create a new user with the given username and password.
    created_user = await create_user(
        db,
        user_create=user_guest_register,
        hashed_password=get_password_hash(user_guest_register.password),
        organization_id=org.id,
        allow_org_empty=False,
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
    await caching_token(db, username=created_user.username, token=token)

    # Return the access token.
    return token


@router.get("/organizations/{org_id}/users")
async def api_list_users(
    disabled: Optional[bool] = Query(False),
    sort: Literal["asc", "desc"] = Query("asc"),
    start: Optional[Text] = Query(None),
    before: Optional[Text] = Query(None),
    limit: Optional[int] = Query(10, ge=1, le=100),
    token_payload_org: TokenOrgDepends = Depends(
        DependsUserPermissions([Permission.READ_ORG_USER], "depends_org_managing")
    ),
    db: DatabaseBase = Depends(depend_db),
) -> Pagination[User]:
    """Search for users by username or other criteria."""

    org = token_payload_org.organization

    return Pagination[User].model_validate(
        (
            await list_users(
                db,
                organization_id=org.id,
                disabled=disabled,
                sort=sort,
                start=start,
                before=before,
                limit=limit,
            )
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
    token_payload_org: TokenOrgDepends = Depends(
        DependsUserPermissions([Permission.CREATE_ORG_USER], "depends_org_managing")
    ),
    db: DatabaseBase = Depends(depend_db),
) -> User:
    """Create a new user."""

    org = token_payload_org.organization

    created_user = await create_user(
        db,
        user_create=user_create,
        hashed_password=get_password_hash(user_create.password),
        organization_id=org.id,
        allow_org_empty=False,
    )
    if created_user is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="User already exists"
        )
    return created_user


@router.get("/organizations/{org_id}/users/{user_id}")
async def api_retrieve_user(
    token_payload_org_user: TokenOrgUserManagingDepends = Depends(
        DependsUserPermissions([Permission.READ_ORG_USER], "depends_org_user_managing")
    ),
    db: DatabaseBase = Depends(depend_db),
) -> User:
    """Retrieve user profile information."""

    user = await get_user_by_id(
        db,
        organization_id=token_payload_org_user.organization.id,
        user_id=token_payload_org_user.target_user.id,
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


@router.put("/organizations/{org_id}/users/{user_id}")
async def api_update_user(
    user_update: UserUpdate = Body(...),
    token_payload_org_user: TokenOrgUserManagingDepends = Depends(
        DependsUserPermissions(
            [Permission.UPDATE_ORG_USER], "depends_org_user_managing"
        )
    ),
    db: DatabaseBase = Depends(depend_db),
) -> User:
    """Update user profile information."""

    user = await update_user(
        db,
        organization_id=token_payload_org_user.organization.id,
        user_id=token_payload_org_user.target_user.id,
        user_update=user_update,
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


@router.delete(
    "/organizations/{org_id}/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def api_delete_user(
    token_payload_org_user: TokenOrgUserManagingDepends = Depends(
        DependsUserPermissions(
            [Permission.UPDATE_ORG_USER], "depends_org_user_managing"
        )
    ),
    db: DatabaseBase = Depends(depend_db),
):
    """Delete a user."""

    user = await run_as_coro(
        delete_user,
        db,
        user_id=token_payload_org_user.target_user.id,
        organization_id=token_payload_org_user.organization.id,
        soft_delete=True,
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
