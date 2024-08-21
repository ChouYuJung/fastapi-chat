from enum import Enum
from typing import Text

from app.schemas.oauth import UserInDB

fake_users_db = {
    "admin": {
        "id": "01917074-e006-7df3-b00b-d5daa3631291",
        "username": "admin",
        "full_name": "Admin User",
        "email": "admin@example.com",
        "role": "admin",
        "hashed_password": "$2b$12$vju9EMyn.CE80h88pErZNuSC.0EZOH/rqw2RpCLdCeEVLRPfhDlYS",  # 'pass1234', ignore E501
        "disabled": False,
    },
    "team": {
        "id": "0191740f-261f-77d2-9342-43d1e9f33e15",
        "username": "team",
        "full_name": "Team User",
        "email": "team@example.com",
        "role": "contributor",
        "hashed_password": "$2b$12$vju9EMyn.CE80h88pErZNuSC.0EZOH/rqw2RpCLdCeEVLRPfhDlYS",  # 'pass1234', ignore E501
        "disabled": False,
    },
    "guest": {
        "id": "0191740f-f0a1-7b32-812a-45e20f12ed6b",
        "username": "guest",
        "full_name": "Guest User",
        "email": "guest@example.com",
        "role": "viewer",
        "hashed_password": "$2b$12$vju9EMyn.CE80h88pErZNuSC.0EZOH/rqw2RpCLdCeEVLRPfhDlYS",  # 'pass1234', ignore E501
        "disabled": False,
    },
}


class Role(str, Enum):
    ADMIN = "admin"
    CONTRIBUTOR = "contributor"
    VIEWER = "viewer"


def get_user(db, username: Text):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)
