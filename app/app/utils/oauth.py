from datetime import UTC, datetime, timedelta
from typing import Dict, Optional, Text

from app.config import settings
from app.db.users import get_user
from app.schemas.oauth import UserInDB
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=settings.token_url)


def verify_password(plain_password: Text, hashed_password: Text) -> bool:
    """Verify the given password with the hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    """Get the password hash for the given password."""
    return pwd_context.hash(password)


def authenticate_user(fake_db, username: Text, password: Text) -> Optional["UserInDB"]:
    """Authenticate a user with the given username and password."""

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
) -> Text:
    """Create an access token with the given data."""

    to_encode = data.copy()
    expire = datetime.now(UTC) + (
        expires_delta if expires_delta else timedelta(minutes=15)
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, key, algorithm=algorithm)
    return encoded_jwt


def invalidate_token(user_name: Text):
    """Invalidate the token for the given user."""

    pass  # Not implemented yet


def verify_token(token: Text) -> Optional[Dict]:
    """Verify the given token and return the payload if valid."""

    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None
