import time
from enum import Enum
from typing import List, Optional, Text

import uuid_utils as uuid
from pydantic import BaseModel, ConfigDict, Field


class ConversationParticipant(BaseModel):
    user_id: Text = Field(..., description="User ID of the participant")
    joined_at: int = Field(default_factory=lambda: int(time.time()))


class ConversationType(str, Enum):
    ONE_ON_ONE = "one_on_one"
    GROUP = "group"


class Conversation(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, use_enum_values=True)
    id: str = Field(..., description="Conversation ID in UUID Version 7 format")
    type: ConversationType
    name: Optional[Text] = Field(
        None, description="Name of the conversation (for group chats)"
    )
    participants: List[ConversationParticipant]
    disabled: bool = Field(default=False)
    created_at: int = Field(default_factory=lambda: int(time.time()))
    updated_at: int = Field(default_factory=lambda: int(time.time()))
    last_message_at: Optional[int] = Field(default=None)

    @classmethod
    def update_participants(
        cls,
        participant_ids: Optional[List[Text]],
        participants_origin: Optional[List[ConversationParticipant]] = None,
        *,
        sort: bool = True,
    ) -> List[ConversationParticipant]:
        participants_origin = participants_origin or []
        if participant_ids is None:
            return participants_origin

        new_participants: List[ConversationParticipant] = []
        for user_id in participant_ids:
            existing_participant = next(
                (
                    participant
                    for participant in participants_origin
                    if participant.user_id == user_id
                ),
                None,
            )
            if existing_participant is not None:
                new_participants.append(existing_participant.model_copy(deep=True))
            else:
                new_participants.append(
                    ConversationParticipant.model_validate({"user_id": user_id})
                )

        if sort:
            new_participants = cls.sort_participants(new_participants)
        return new_participants

    @classmethod
    def sort_participants(
        cls, participants: List[ConversationParticipant]
    ) -> List[ConversationParticipant]:
        return sorted(participants, key=lambda participant: participant.joined_at)

    def sort_participants_self(self) -> None:
        self.participants = self.sort_participants(self.participants)


class ConversationCreate(BaseModel):
    type: ConversationType
    name: Optional[Text] = Field(
        None, description="Name of the conversation (for group chats)"
    )
    participant_ids: List[Text]
    disabled: Optional[bool] = Field(default=None)

    def to_conversation(self, conversation_id: Optional[Text] = None) -> Conversation:
        conversation = Conversation.model_validate(
            {
                "id": conversation_id or str(uuid.uuid7()),
                "type": self.type,
                "name": self.name,
                "participants": [
                    {"user_id": user_id} for user_id in self.participant_ids
                ],
            }
        )
        conversation.sort_participants_self()
        return conversation


class ConversationUpdate(BaseModel):
    name: Optional[Text] = Field(default=None)
    participant_ids: Optional[List[Text]] = Field(default=None)
    disabled: Optional[bool] = Field(default=None)

    def apply_conversation(self, conversation: Conversation) -> Conversation:
        conversation_date = conversation.model_dump()
        participants_models_old = conversation.participants

        # Update conversation data
        if self.name is not None:
            conversation_date["name"] = self.name

        # Update participants
        if self.participant_ids is not None:
            participants_models = Conversation.update_participants(
                self.participant_ids, participants_models_old, sort=True
            )
            conversation_date["participants"] = [
                p.model_dump() for p in participants_models
            ]

        # Validate and return the updated conversation
        conversation = Conversation.model_validate(conversation_date)
        return conversation


class ConversationInDB(Conversation):
    pass
