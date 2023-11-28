from typing import Text

from app.config import settings
from app.db.users import fake_users_db, get_user
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=settings.token_url)


def fake_decode_token(token):
    user = get_user(fake_users_db, token)
    return user


def fake_hash_password(password: Text):
    return "fake-hashed-" + password
