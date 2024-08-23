from typing import TYPE_CHECKING, Literal, Optional, Text

from app.schemas.oauth import UserCreate, UserInDB, UserUpdate
from app.schemas.pagination import Pagination

if TYPE_CHECKING:
    from app.db._base import DatabaseBase


def get_user(db: "DatabaseBase", *, username: Text) -> Optional["UserInDB"]:
    return db.retrieve_user_by_username(username)


def get_user_by_id(db: "DatabaseBase", *, user_id: Text) -> Optional["UserInDB"]:
    return db.retrieve_user(user_id)


def list_users(
    db: "DatabaseBase",
    *,
    disabled: Optional[bool] = None,
    sort: Literal["asc", "desc", 1, -1] = "asc",
    start: Optional[Text] = None,
    before: Optional[Text] = None,
    limit: Optional[int] = 20,
) -> Pagination[UserInDB]:
    """List users from the database."""

    return db.list_users(
        disabled=disabled, sort=sort, start=start, before=before, limit=limit
    )


def update_user(
    db: "DatabaseBase", *, user_id: Text, user_update: "UserUpdate"
) -> Optional[UserInDB]:
    """Update a user in the database."""

    return db.update_user(user_id=user_id, user_update=user_update)


def create_user(
    db: "DatabaseBase", *, user_create: "UserCreate", hashed_password: Text
) -> Optional["UserInDB"]:
    """Create a new user in the database."""

    return db.create_user(user_create=user_create, hashed_password=hashed_password)
