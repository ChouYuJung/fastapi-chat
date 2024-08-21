from typing import Set, Text

fake_token_blacklist: Set[Text] = set()


def invalidate_token(db=fake_token_blacklist, *, token: Text):
    """Invalidate the token for the given user."""
    db.add(token)


def is_token_invalid(db=fake_token_blacklist, *, token: Text) -> bool:
    """Check if the token is in the blacklist."""

    return token in db
