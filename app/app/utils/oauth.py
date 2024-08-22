import time
from datetime import UTC, datetime, timedelta
from typing import Dict, Optional, Text

from app.config import settings
from app.db.users import get_user
from app.schemas.oauth import PayloadParam, UserInDB
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=settings.token_url)


def verify_password(plain_password: Text, hashed_password: Text) -> bool:
    """Verify the given password with the hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: Text | bytes) -> Text:
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


def verify_token(token: Text) -> Optional[Dict]:
    """Verify the given token and return the payload if valid."""

    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None


def verify_payload(payload: Dict) -> Optional[PayloadParam]:
    """Verify the payload and return the payload if valid."""

    subject = payload.get("sub")
    expires = payload.get("exp")
    if not isinstance(subject, Text):
        return None
    if not isinstance(expires, int):
        return None
    return PayloadParam(sub=subject, exp=expires)


def is_token_expired(token_or_payload: Text | Dict | PayloadParam) -> bool:
    """Check if the token is expired."""

    payload = (
        verify_token(token_or_payload)
        if isinstance(token_or_payload, Text)
        else token_or_payload
    )
    if payload is None:
        return True
    payload = verify_payload(dict(payload))
    if payload is None:
        return True
    if time.time() > payload["exp"]:
        return True
    return False
