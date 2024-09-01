from typing import TYPE_CHECKING, Literal, Optional, Sequence, Text

from fastapi_chat.schemas.pagination import Pagination
from fastapi_chat.utils.common import run_as_coro

from ..schemas.roles import Role
from ..schemas.users import UserCreate, UserInDB, UserUpdate

if TYPE_CHECKING:
    from fastapi_chat.db._base import DatabaseBase


async def get_user(db: "DatabaseBase", *, username: Text) -> Optional["UserInDB"]:
    return await run_as_coro(db.retrieve_user_by_username, username)


async def get_user_by_id(
    db: "DatabaseBase", *, user_id: Text, organization_id: Optional[Text] = None
) -> Optional["UserInDB"]:
    return await run_as_coro(
        db.retrieve_user, organization_id=organization_id, user_id=user_id
    )


async def list_users(
    db: "DatabaseBase",
    *,
    organization_id: Optional[Text] = None,
    role: Optional[Role] = None,
    roles: Optional[Sequence[Role]] = None,
    disabled: Optional[bool] = None,
    sort: Literal["asc", "desc", 1, -1] = "asc",
    start: Optional[Text] = None,
    before: Optional[Text] = None,
    limit: Optional[int] = 20,
) -> Pagination[UserInDB]:
    """List users from the database."""

    return await run_as_coro(
        db.list_users,
        organization_id=organization_id,
        role=role,
        roles=roles,
        disabled=disabled,
        sort=sort,
        start=start,
        before=before,
        limit=limit,
    )


async def update_user(
    db: "DatabaseBase",
    *,
    organization_id: Optional[Text] = None,
    user_id: Text,
    user_update: "UserUpdate",
) -> Optional[UserInDB]:
    """Update a user in the database."""

    return await run_as_coro(
        db.update_user,
        organization_id=organization_id,
        user_id=user_id,
        user_update=user_update,
    )


async def create_user(
    db: "DatabaseBase",
    *,
    user_create: "UserCreate",
    hashed_password: Text,
    organization_id: Optional[Text] = None,
    allow_org_empty: bool = False,
) -> Optional["UserInDB"]:
    """Create a new user in the database."""

    return await run_as_coro(
        db.create_user,
        user_create=user_create,
        hashed_password=hashed_password,
        organization_id=organization_id,
        allow_org_empty=allow_org_empty,
    )


async def delete_user(
    db: "DatabaseBase",
    user_id: Text,
    *,
    organization_id: Optional[Text] = None,
    soft_delete: bool = True,
) -> bool:
    """Delete a user from the database."""

    return await run_as_coro(
        db.delete_user,
        user_id=user_id,
        organization_id=organization_id,
        soft_delete=soft_delete,
    )
