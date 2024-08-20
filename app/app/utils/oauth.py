from datetime import UTC, datetime, timedelta
from typing import Dict, Optional, Text

from app.config import settings
from app.db.users import fake_users_db, get_user
from app.schemas.oauth import UserInDB
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=settings.token_url)


def fake_decode_token(token):
    user = get_user(fake_users_db, token)
    return user


def fake_hash_password(password: Text):
    return "fake-hashed-" + password


def verify_password(plain_password: Text, hashed_password: Text) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def authenticate_user(fake_db, username: Text, password: Text) -> Optional["UserInDB"]:
    user = get_user(fake_db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(
    data: Dict,
    expires_delta: Optional[timedelta] = None,
    key: Text = settings.SECRET_KEY,
    algorithm: Text = settings.ALGORITHM,
):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, key, algorithm=algorithm)
    return encoded_jwt
