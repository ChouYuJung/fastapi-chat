from typing import Annotated, Dict, Optional, Set, Text

from app.schemas.conversations import Conversation

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
    user_id: Optional[Text] = None
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
