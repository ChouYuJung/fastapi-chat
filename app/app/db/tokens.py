from typing import TYPE_CHECKING, Annotated, Dict, Optional, Set, Text

if TYPE_CHECKING:
    from app.schemas.oauth import Token

fake_token_db: Annotated[Dict[Text, "Token"], "username: token"] = {}

fake_token_blacklist: Set[Text] = set()


def save_token(
    db=fake_token_db, *, username: Text, token: "Token"
) -> Optional["Token"]:
    """Create a new token for the given user."""

    if get_token(db, username=username) == token:
        return None  # Token already exists
    db[username] = token
    return token


def get_token(db=fake_token_db, *, username: Text) -> Optional["Token"]:
    """Get the token for the given user."""

    return db.get(username)


def invalidate_token(db=fake_token_blacklist, *, token: Optional["Token"]):
    """Invalidate the token for the given user."""

    if token is None:
        return
    db.add(token.access_token)
    db.add(token.refresh_token)


def is_token_invalid(db=fake_token_blacklist, *, token: Text) -> bool:
    """Check if the token is in the blacklist."""

    return token in db


def logout_user(
    db=fake_token_db, *, username: Text, with_invalidate_token: bool = True
) -> Optional["Token"]:
    """Logout the user by deleting the token."""

    should_invalid_token = db.pop(username, None)
    if with_invalidate_token is True:
        invalidate_token(token=should_invalid_token)
