from typing import Text

from app.schemas.oauth import UserInDB

fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "fake-hashed-secret",
        "disabled": False,
    },
    "alice": {
        "username": "alice",
        "full_name": "Alice Wonderson",
        "email": "alice@example.com",
        "hashed_password": "fake-hashed-secret2",
        "disabled": True,
    },
}


def get_user(db, username: Text):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)
