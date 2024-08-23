from typing import TYPE_CHECKING, Optional, Text

if TYPE_CHECKING:
    from app.db._base import DatabaseBase
    from app.schemas.oauth import Token, TokenInDB


def caching_token(
    db: "DatabaseBase", *, username: Text, token: "Token"
) -> Optional["Token"]:
    """Create a new token for the given user."""

    return db.caching_token(username=username, token=token)


def retrieve_cached_token(
    db: "DatabaseBase", *, username: Text
) -> Optional["TokenInDB"]:
    """Get the token for the given user."""

    return db.retrieve_cached_token(username)


def invalidate_token(db: "DatabaseBase", *, token: Optional["Token"]):
    """Invalidate the token for the given user."""

    db.invalidate_token(token)


def is_token_blocked(db: "DatabaseBase", *, token: Text) -> bool:
    """Check if the token is in the blacklist."""

    return db.is_token_blocked(token)
