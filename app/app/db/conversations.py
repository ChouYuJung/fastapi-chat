from types import MappingProxyType
from typing import Annotated, Dict, List, Literal, Optional, Set, Text, TypedDict

from app.schemas.conversations import Conversation, ConversationInDB
from app.schemas.oauth import User, UserInDB
from app.schemas.pagination import Pagination

fake_conversations_db: Annotated[
    Dict[Text, "Conversation"], "conversation_id: conversation"
] = {}
fake_user_conversations_db: Annotated[
    Dict[Text, Set[Text]], "user_id: [conversation_id]"
] = {}


def create_conversation(
    db=fake_conversations_db,
    user_db=fake_user_conversations_db,
    *,
    conversation: "Conversation",
    user_id: Optional[Text] = None,
) -> "Conversation":
    """Create a new conversation in the database."""

    # Validate conversation data
    if conversation.id in db:
        raise ValueError("Conversation already exists")
    db[conversation.id] = conversation

    # Add conversation to user's conversations
    if user_id is not None:
        if user_id not in user_db:
            user_db[user_id] = set()
        user_db[user_id].add(conversation.id)
    return conversation


def list_conversations(
    db=fake_conversations_db,
    *,
    disabled: Optional[bool] = None,
    sort: Literal["asc", "desc", 1, -1] = "asc",
    start: Optional[Text] = None,
    before: Optional[Text] = None,
    limit: Optional[int] = 20,
) -> Pagination[ConversationInDB]:
    """List conversations from the database."""

    limit = min(limit or 1000, 1000)
    conversations = [
        ConversationInDB.model_validate(conversation) for conversation in db.values()
    ]
    if disabled is not None:
        conversations = [
            conversation
            for conversation in conversations
            if conversation.disabled == disabled
        ]
    if sort in ("asc", 1):
        conversations = sorted(conversations, key=lambda conversation: conversation.id)
    else:
        conversations = sorted(
            conversations, key=lambda conversation: conversation.id, reverse=True
        )
    if start:
        conversations = [
            conversation
            for conversation in conversations
            if (
                conversation.id >= start
                if sort in ("asc", 1)
                else conversation.id <= start
            )
        ]
    if before:
        conversations = [
            conversation
            for conversation in conversations
            if (
                conversation.id < before
                if sort in ("asc", 1)
                else conversation.id > before
            )
        ]
    return Pagination[ConversationInDB].model_validate(
        {
            "object": "list",
            "data": conversations[:limit],
            "first_id": conversations[0].id if conversations else None,
            "last_id": conversations[-1].id if conversations else None,
            "has_more": len(conversations) > limit,
        }
    )


def list_user_conversations(
    db=fake_user_conversations_db,
    *,
    user_id: Text,
    disabled: Optional[bool] = None,
    sort: Literal["asc", "desc", 1, -1] = "asc",
    start: Optional[Text] = None,
    before: Optional[Text] = None,
    limit: Optional[int] = 20,
) -> Pagination[ConversationInDB]:
    """List conversations for a user from the database."""

    limit = min(limit or 1000, 1000)
    conversations_set = db.get(user_id, set())
    conversations: List["ConversationInDB"] = [c for c in conversations_set]
    if disabled is not None:
        conversations = [c for c in conversations if c.disabled == disabled]
    if sort in ("asc", 1):
        conversations = sorted(conversations, key=lambda c: c.id)
    else:
        conversations = sorted(conversations, key=lambda c: c.id, reverse=True)
    if start:
        conversations = [
            c
            for c in conversations
            if (c.id >= start if sort in ("asc", 1) else c.id <= start)
        ]
    if before:
        conversations = [
            c
            for c in conversations
            if (c.id < before if sort in ("asc", 1) else c.id > before)
        ]
    return Pagination[ConversationInDB].model_validate(
        {
            "object": "list",
            "data": conversations[:limit],
            "first_id": conversations[0].id if conversations else None,
            "last_id": conversations[-1].id if conversations else None,
            "has_more": len(conversations) > limit,
        }
    )
