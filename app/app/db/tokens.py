from typing import Annotated, Dict, Optional, Set, Text

fake_token_db: Annotated[Dict[Text, Text], "username: token"] = {}

fake_token_blacklist: Set[Text] = set()


def create_token(db=fake_token_db, *, username: Text, token: Text) -> Optional[Text]:
    """Create a new token for the given user."""

    if get_token(db, username=username) == token:
        return None  # Token already exists
    db[username] = token
    return token


def get_token(db=fake_token_db, *, username: Text) -> Optional[Text]:
    """Get the token for the given user."""

    return db.get(username)


def invalidate_token(db=fake_token_blacklist, *, token: Text):
    """Invalidate the token for the given user."""
    db.add(token)


def is_token_invalid(db=fake_token_blacklist, *, token: Text) -> bool:
    """Check if the token is in the blacklist."""

    return token in db


def logout_user(db=fake_token_db, *, username: Text):
    """Logout the user by deleting the token."""

    db.pop(username, None)
