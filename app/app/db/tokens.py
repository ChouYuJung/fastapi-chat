from typing import TYPE_CHECKING, Optional, Text

from app.utils.common import run_as_coro

if TYPE_CHECKING:
    from app.db._base import DatabaseBase
    from app.schemas.oauth import Token, TokenInDB


async def caching_token(
    db: "DatabaseBase", *, username: Text, token: "Token"
) -> Optional["Token"]:
    """Create a new token for the given user."""

    return await run_as_coro(db.caching_token, username=username, token=token)


async def retrieve_cached_token(
    db: "DatabaseBase", *, username: Text
) -> Optional["TokenInDB"]:
    """Get the token for the given user."""

    return await run_as_coro(db.retrieve_cached_token, username)


async def invalidate_token(db: "DatabaseBase", *, token: Optional["Token"]):
    """Invalidate the token for the given user."""

    await run_as_coro(db.invalidate_token, token)


async def is_token_blocked(db: "DatabaseBase", *, token: Text) -> bool:
    """Check if the token is in the blacklist."""

    return await run_as_coro(db.is_token_blocked, token)
