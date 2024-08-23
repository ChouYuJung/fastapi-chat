import time
from enum import Enum
from typing import Any, Dict, List, Optional, Text

import uuid_utils as uuid
from pydantic import BaseModel, Field


class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    AUDIO = "audio"
    VIDEO = "video"
    SYSTEM = "system"


class MessageReaction(BaseModel):
    user_id: Text
    reaction: Text = Field(..., description="Reaction emoji")
    created_at: int = Field(default_factory=lambda: int(time.time()))


class Message(BaseModel):
    # IDs
    id: Text = Field(
        default_factory=lambda: str(uuid.uuid7()),
        description="Message ID in UUID Version 7 format",
    )
    conversation_id: Text = Field(..., description="ID of the conversation")
    sender_id: Text = Field(..., description="ID of the sender")
    # Metadata
    type: MessageType = Field(default=MessageType.TEXT)
    content: Text = Field(..., description="Content of the message")
    # Contents
    is_edited: bool = Field(default=False)
    is_deleted: bool = Field(default=False)
    reply_to: Optional[Text] = Field(
        default=None, description="ID of the message being replied to"
    )
    metadata: Optional[Dict[Text, Any]] = Field(
        default=None, description="Additional metadata for non-text messages"
    )
    reactions: List[MessageReaction] = Field(default_factory=list)
    # Timestamps
    created_at: int = Field(default_factory=lambda: int(time.time()))
    updated_at: int = Field(default_factory=lambda: int(time.time()))


class MessageCreate(BaseModel):
    conversation_id: Text
    content: Text
    type: MessageType = Field(default=MessageType.TEXT)
    reply_to: Optional[Text] = None
    metadata: Optional[Dict[Text, Any]] = None

    def to_message(self, sender_id: Text) -> Message:
        msg_create_data = self.model_dump()
        msg_create_data["sender_id"] = sender_id
        return Message.model_validate(msg_create_data)


class MessageUpdate(BaseModel):
    content: Optional[Text] = None
    is_deleted: Optional[bool] = None
    metadata: Optional[Dict[Text, Any]] = None
    reactions: Optional[List[MessageReaction]] = None

    def apply_to_message(self, message: Message) -> Message:
        flag_update = False
        # Update content
        if self.content is not None:
            message.content = self.content
            message.is_edited = True
        # Update deletion status
        if self.is_deleted is not None:
            message.is_deleted = self.is_deleted
        # Update metadata
        if self.metadata is not None:
            message.metadata = message.metadata or {}
            message.metadata.update(self.metadata)
        # Update reactions
        if self.reactions is not None:
            message.reactions = self.reactions

        # Update timestamps
        if flag_update:
            message.updated_at = int(time.time())
        return message
