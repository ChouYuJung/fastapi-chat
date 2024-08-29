from typing import Annotated, Dict, List, Literal, Optional, Sequence, Set, Text

from app.schemas.conversations import Conversation, ConversationInDB, ConversationUpdate
from app.schemas.pagination import Pagination

fake_conversations_db: Annotated[
    Dict[Text, "ConversationInDB"], "conversation_id: conversation"
] = {}
fake_user_conversations_db: Annotated[
    Dict[Text, Set[Text]], "user_id: [conversation_id]"
] = {}


async def create_conversation(
    db=fake_conversations_db,
    user_db=fake_user_conversations_db,
    *,
    conversation: "Conversation",
    user_id: Optional[Text] = None,
) -> "ConversationInDB":
    """Create a new conversation in the database."""

    conversation = ConversationInDB.model_validate(conversation)

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


async def list_conversations(
    db=fake_conversations_db,
    *,
    participants: Optional[Sequence[Text]] = None,
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
    if participants is not None:
        conversations = [
            conversation
            for conversation in conversations
            if set(participants) <= set(conversation.participants)
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


async def retrieve_conversation(
    db=fake_conversations_db,
    *,
    conversation_id: Text,
) -> Optional["ConversationInDB"]:
    """Retrieve a conversation from the database."""

    return db.get(conversation_id)


async def update_conversation(
    db=fake_conversations_db,
    *,
    conversation_id: Text,
    conversation_update: "ConversationUpdate",
) -> Optional["ConversationInDB"]:
    """Update a conversation in the database."""

    conversation = await retrieve_conversation(db, conversation_id=conversation_id)
    if conversation is None:
        return None
    conversation = conversation_update.to_conversation(conversation)
    conversation = ConversationInDB.model_validate(conversation.model_dump())
    db[conversation_id] = conversation
    return conversation


async def delete_conversation(
    db=fake_conversations_db,
    *,
    conversation_id: Text,
    soft_delete: bool = True,
) -> None:
    """Delete a conversation from the database."""

    if soft_delete:
        conversation = await retrieve_conversation(db, conversation_id=conversation_id)
        if conversation is not None:
            conversation.disabled = True
            db[conversation_id] = conversation
    else:
        db.pop(conversation_id, None)


async def list_user_conversations(
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
