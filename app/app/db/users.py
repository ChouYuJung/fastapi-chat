from typing import Text

from app.schemas.oauth import UserInDB

fake_users_db = {
    "dockhardman": {
        "username": "dockhardman",
        "full_name": "Dock Hardman",
        "email": "dockhardman@example.com",
        "hashed_password": "$2b$12$vju9EMyn.CE80h88pErZNuSC.0EZOH/rqw2RpCLdCeEVLRPfhDlYS",  # 'pass1234', ignore E501
        "disabled": False,
    }
}


def get_user(db, username: Text):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)
