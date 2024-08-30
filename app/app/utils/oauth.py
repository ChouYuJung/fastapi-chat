import time
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Dict, Optional, Text

from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from ..config import settings
from ..db.users import get_user
from ..schemas.oauth import PayloadParam, Token
from ..schemas.users import UserInDB

if TYPE_CHECKING:
    from app.db._base import DatabaseBase

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=settings.token_url)


def verify_password(plain_password: Text, hashed_password: Text) -> bool:
    """Verify the given password with the hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: Text | bytes) -> Text:
    """Get the password hash for the given password."""
    return pwd_context.hash(password)


async def authenticate_user(
    db: "DatabaseBase", username: Text, password: Text
) -> Optional["UserInDB"]:
    """Authenticate a user with the given username and password."""

    user = await get_user(db, username=username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_token(
    data: Dict,
    *,
    expire: datetime | float | int | None = None,
    expires_delta: Optional[timedelta] = None,
    key: Text = settings.SECRET_KEY,
    algorithm: Text = settings.ALGORITHM,
) -> Text:
    """Create an access token with the given data."""

    to_encode = data.copy()
    if expire is not None:
        expires_at = (
            int(expire.timestamp()) if isinstance(expire, datetime) else int(expire)
        )
    else:
        expire_at_dt = datetime.now(UTC) + (
            expires_delta if expires_delta else timedelta(minutes=15)
        )
        expires_at = int(expire_at_dt.timestamp())
    to_encode.update({"exp": expires_at})
    encoded_jwt = jwt.encode(to_encode, key, algorithm=algorithm)
    return encoded_jwt


def create_token_model(
    data: Dict,
    access_token_expires_delta: Optional[timedelta] = None,
    refresh_token_expires_delta: Optional[timedelta] = None,
    key: Text = settings.SECRET_KEY,
    algorithm: Text = settings.ALGORITHM,
) -> Token:
    """Create an access token and a refresh token with the given data."""

    expires_at_dt = datetime.now(UTC) + (
        access_token_expires_delta
        if access_token_expires_delta
        else timedelta(minutes=15)
    )
    expires_at = int(expires_at_dt.timestamp())
    access_token = create_token(data, expire=expires_at, key=key, algorithm=algorithm)
    refresh_token = create_token(
        data, expires_delta=refresh_token_expires_delta, key=key, algorithm=algorithm
    )
    return Token.from_bearer_token(
        access_token=access_token, refresh_token=refresh_token, expires_at=expires_at
    )


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
    user_id = payload.get("user_id")
    organization_id = payload.get("organization_id")
    disabled = payload.get("disabled")

    if not isinstance(subject, Text):
        return None
    if not isinstance(expires, int):
        return None
    if not isinstance(user_id, Text):
        return None
    return PayloadParam(
        sub=subject,
        exp=expires,
        user_id=user_id,
        organization_id=organization_id,
        disabled=disabled,
    )


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


def validate_client(client_id: Optional[Text], client_secret: Optional[Text]) -> bool:
    # Replace this with your actual client validation logic
    # For example, check against a database of registered clients
    return True
