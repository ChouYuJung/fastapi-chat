from types import MappingProxyType
from typing import Dict, Literal, Optional, Text

from app.schemas.oauth import User, UserInDB
from app.schemas.pagination import Pagination

fake_users_db_init = MappingProxyType(
    {
        "admin": {
            "id": "01917074-e006-7df3-b00b-d5daa3631291",
            "username": "admin",
            "full_name": "Admin User",
            "email": "admin@example.com",
            "role": "admin",
            "hashed_password": "$2b$12$vju9EMyn.CE80h88pErZNuSC.0EZOH/rqw2RpCLdCeEVLRPfhDlYS",  # 'pass1234', noqa: E501
            "disabled": False,
        },
        "team": {
            "id": "0191740f-261f-77d2-9342-43d1e9f33e15",
            "username": "team",
            "full_name": "Team User",
            "email": "team@example.com",
            "role": "contributor",
            "hashed_password": "$2b$12$vju9EMyn.CE80h88pErZNuSC.0EZOH/rqw2RpCLdCeEVLRPfhDlYS",  # 'pass1234', noqa: E501
            "disabled": False,
        },
        "guest": {
            "id": "0191740f-f0a1-7b32-812a-45e20f12ed6b",
            "username": "guest",
            "full_name": "Guest User",
            "email": "guest@example.com",
            "role": "viewer",
            "hashed_password": "$2b$12$vju9EMyn.CE80h88pErZNuSC.0EZOH/rqw2RpCLdCeEVLRPfhDlYS",  # 'pass1234', noqa: E501
            "disabled": False,
        },
    }
)
fake_users_db = dict(fake_users_db_init)


def get_user(db, username: Text):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)


def get_user_by_id(db=fake_users_db, *, user_id: Text) -> Optional["UserInDB"]:
    for user in db.values():
        if user["id"] == user_id:
            return UserInDB.model_validate(user)


def list_users(
    db=fake_users_db,
    *,
    disabled: Optional[bool] = None,
    sort: Literal["asc", "desc", 1, -1] = "asc",
    start: Optional[Text] = None,
    before: Optional[Text] = None,
    limit: Optional[int] = 20,
) -> Pagination[UserInDB]:
    """List users from the database."""

    limit = min(limit or 1000, 1000)
    users = [UserInDB.model_validate(user) for user in db.values()]
    if disabled is not None:
        users = [user for user in users if user.disabled == disabled]
    if sort in ("asc", 1):
        users = sorted(users, key=lambda user: user.id)
    else:
        users = sorted(users, key=lambda user: user.id, reverse=True)
    if start:
        users = [
            user
            for user in users
            if (user.id >= start if sort in ("asc", 1) else user.id <= start)
        ]
    if before:
        users = [
            user
            for user in users
            if (user.id < before if sort in ("asc", 1) else user.id > before)
        ]
    return Pagination[UserInDB].model_validate(
        {
            "object": "list",
            "data": users[:limit],
            "first_id": users[0].id if users else None,
            "last_id": users[-1].id if users else None,
            "has_more": len(users) > limit,
        }
    )


def update_user(
    db=fake_users_db, *, user_id: Text, update_data: Dict
) -> Optional[UserInDB]:
    """Update a user in the database."""

    user = get_user_by_id(db=db, user_id=user_id)
    if user is None:
        return None
    # Validate update data
    update_data = {k: v for k, v in update_data.items() if v is not None}
    update_data.pop("id", None)
    update_data.pop("username", None)
    update_data.pop("hashed_password", None)
    # Update user data
    user_data = user.model_dump()
    user_data.update(update_data)
    update_user = UserInDB.model_validate(user_data)
    db[user.username] = update_user.model_dump()
    return update_user


def create_user(
    db=fake_users_db, *, user: "User", hashed_password: Text
) -> Optional["UserInDB"]:
    """Create a new user in the database."""

    if user.username in db:
        return None  # User already exists
    # Validate user data
    user_data = user.model_dump()
    user_data["hashed_password"] = hashed_password
    user_db = UserInDB.model_validate(user_data)
    # Add user to the database
    db[user_db.username] = user_db.model_dump()
    return user_db
