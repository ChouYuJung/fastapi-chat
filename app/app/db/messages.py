from typing import Annotated, Dict, List, Literal, Optional, Text

from app.schemas.messages import Message, MessageUpdate
from app.schemas.pagination import Pagination

fake_messages_db: Annotated[
    Dict[Text, List["Message"]], "conversation_id: messages"
] = {}


def list_messages(
    db=fake_messages_db,
    *,
    conversation_id: Text,
    sort: Literal["asc", "desc", 1, -1] = "desc",
    start: Optional[Text] = None,
    before: Optional[Text] = None,
    limit: int = 20,
) -> Pagination[Message]:
    """Retrieve messages for a specific conversation."""

    limit = min(limit or 1000, 1000)
    messages = [
        Message.model_validate(message)
        for message in fake_messages_db.get(conversation_id, [])
    ]
    if sort in ("asc", 1):
        messages = sorted(messages, key=lambda message: message.id)
    else:
        messages = sorted(messages, key=lambda message: message.id, reverse=True)
    if start:
        messages = [
            message
            for message in messages
            if (message.id >= start if sort in ("asc", 1) else message.id <= start)
        ]
    if before:
        messages = [
            message
            for message in messages
            if (message.id < before if sort in ("asc", 1) else message.id > before)
        ]
    return Pagination[Message].model_validate(
        {
            "object": "list",
            "data": messages[:limit],
            "first_id": messages[0].id if messages else None,
            "last_id": messages[-1].id if messages else None,
            "has_more": len(messages) > limit,
        }
    )


def retrieve_message(
    db=fake_messages_db,
    *,
    conversation_id: Text,
    message_id: Text,
) -> Optional["Message"]:
    """Retrieve a message from a conversation."""

    for message in db.get(conversation_id, []):
        if message.id == message_id:
            return message
    return None


def create_message(
    db=fake_messages_db,
    *,
    conversation_id: Text,
    message: "Message",
) -> "Message":
    """Create a new message in a conversation."""

    db.setdefault(conversation_id, []).append(message)
    return message


def update_message(
    db=fake_messages_db,
    *,
    conversation_id: Text,
    message_id: Text,
    message_update: "MessageUpdate",
) -> Optional["Message"]:
    """Update a message in a conversation."""

    messages = db.get(conversation_id, [])
    for i, m in enumerate(messages):
        if m.id == message_id:
            updated_msg = message_update.apply_to_message(m)
            messages[i] = updated_msg
            return messages[i]
    return None


def delete_message(
    db=fake_messages_db,
    *,
    conversation_id: Text,
    message_id: Text,
    soft_delete: bool = True,
) -> Optional["Message"]:
    """Delete a message from a conversation."""

    messages = db.get(conversation_id, [])
    for i, m in enumerate(messages):
        if m.id == message_id:
            if soft_delete:
                messages[i].is_deleted = True
                return messages[i]
            else:
                return messages.pop(i)
    return None
