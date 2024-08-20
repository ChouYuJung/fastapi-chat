from typing import Text

from app.schemas.oauth import UserInDB

fake_users_db = {
    "admin": {
        "username": "admin",
        "full_name": "Admin User",
        "email": "admin@example.com",
        "hashed_password": "$2b$12$vju9EMyn.CE80h88pErZNuSC.0EZOH/rqw2RpCLdCeEVLRPfhDlYS",  # 'pass1234', ignore E501
        "disabled": False,
    }
}


def get_user(db, username: Text):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)
