from typing import TYPE_CHECKING, Literal, Optional, Sequence, Text

from fastapi_chat.schemas.conversations import (
    ConversationCreate,
    ConversationInDB,
    ConversationUpdate,
)
from fastapi_chat.schemas.pagination import Pagination
from fastapi_chat.utils.common import run_as_coro

if TYPE_CHECKING:
    from fastapi_chat.db._base import DatabaseBase


async def create_conversation(
    db: "DatabaseBase", *, conversation_create: "ConversationCreate"
) -> "ConversationInDB":
    """Create a new conversation in the database."""

    return await run_as_coro(
        db.create_conversation, conversation_create=conversation_create
    )


async def list_conversations(
    db: "DatabaseBase",
    *,
    participants: Optional[Sequence[Text]] = None,
    disabled: Optional[bool] = None,
    sort: Literal["asc", "desc", 1, -1] = "asc",
    start: Optional[Text] = None,
    before: Optional[Text] = None,
    limit: Optional[int] = 20,
) -> Pagination[ConversationInDB]:
    """List conversations from the database."""

    return await run_as_coro(
        db.list_conversations,
        participants=participants,
        disabled=disabled,
        sort=sort,
        start=start,
        before=before,
        limit=limit,
    )


async def retrieve_conversation(
    db: "DatabaseBase", *, conversation_id: Text
) -> Optional["ConversationInDB"]:
    """Retrieve a conversation from the database."""

    return await run_as_coro(db.retrieve_conversation, conversation_id)


async def update_conversation(
    db: "DatabaseBase",
    *,
    conversation_id: Text,
    conversation_update: "ConversationUpdate",
) -> Optional["ConversationInDB"]:
    """Update a conversation in the database."""

    return await run_as_coro(
        db.update_conversation,
        conversation_id=conversation_id,
        conversation_update=conversation_update,
    )


async def delete_conversation(
    db: "DatabaseBase", *, conversation_id: Text, soft_delete: bool = True
) -> None:
    """Delete a conversation from the database."""
    return await run_as_coro(
        db.delete_conversation,
        conversation_id=conversation_id,
        soft_delete=soft_delete,
    )
