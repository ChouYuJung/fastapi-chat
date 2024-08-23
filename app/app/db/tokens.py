from typing import TYPE_CHECKING, Annotated, Dict, Optional, Set, Text

if TYPE_CHECKING:
    from app.db._base import DatabaseBase
    from app.schemas.oauth import Token, TokenInDB

# fake_token_db: Annotated[Dict[Text, "Token"], "username: token"] = {}

# fake_token_blacklist: Set[Text] = set()


def caching_token(
    db: "DatabaseBase", *, username: Text, token: "Token"
) -> Optional["Token"]:
    """Create a new token for the given user."""

    return db.save_token(username=username, token=token)


def get_cached_token(db: "DatabaseBase", *, username: Text) -> Optional["TokenInDB"]:
    """Get the token for the given user."""

    return db.retrieve_cached_token(username)


def invalidate_token(db: "DatabaseBase", *, token: Optional["Token"]):
    """Invalidate the token for the given user."""

    db.invalidate_token(token)


def is_token_blocked(db: "DatabaseBase", *, token: Text) -> bool:
    """Check if the token is in the blacklist."""

    return db.is_token_blocked(token)
