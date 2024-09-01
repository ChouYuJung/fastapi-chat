from types import MappingProxyType
from typing import List, Literal, Optional, Sequence, Text, TypedDict

from ..db._base import DatabaseBase
from ..schemas.conversations import (
    ConversationCreate,
    ConversationInDB,
    ConversationUpdate,
)
from ..schemas.oauth import Token, TokenBlacklisted, TokenInDB
from ..schemas.organizations import Organization, OrganizationCreate, OrganizationUpdate
from ..schemas.pagination import Pagination
from ..schemas.roles import Role
from ..schemas.users import UserCreate, UserInDB, UserUpdate


class _BD(TypedDict):
    cached_tokens: List["TokenInDB"]
    blacklisted_tokens: List["TokenBlacklisted"]
    organizations: List["Organization"]
    users: List["UserInDB"]
    conversations: List["ConversationInDB"]


class DatabaseMemory(DatabaseBase):

    fake_super_admin_init = MappingProxyType(
        {
            "admin": {
                "id": "01917074-e006-7df3-b00b-d5daa3631291",
                "username": "admin",
                "full_name": "Admin User",
                "organization_id": None,
                "email": "admin@example.com",
                "role": "super_admin",
                "hashed_password": "$2b$12$vju9EMyn.CE80h88pErZNuSC.0EZOH/rqw2RpCLdCeEVLRPfhDlYS",  # 'pass1234'
                "disabled": False,
            },  # noqa: E501
        }
    )

    def __init__(self, *arg, **kwargs):
        self._url = None
        self._db = _BD(
            cached_tokens=[],
            blacklisted_tokens=[],
            organizations=[],
            users=[
                UserInDB.model_validate(u)
                for u in dict(self.fake_super_admin_init).values()
            ],
            conversations=[],
        )

    @property
    def client(self) -> _BD:
        return self._db

    async def list_organizations(
        self,
        organization_id: Optional[Text] = None,
        organization_ids: Optional[Sequence[Text]] = None,
        disabled: Optional[bool] = False,
        sort: Literal["asc", "desc"] = "asc",
        start: Optional[Text] = None,
        before: Optional[Text] = None,
        limit: Optional[int] = 10,
    ) -> "Pagination[Organization]":
        limit = min(limit or 1000, 1000)
        organizations = self._db["organizations"]
        if organization_id is not None:
            organizations = [org for org in organizations if org.id == organization_id]
        if organization_ids is not None:
            organizations = [org for org in organizations if org.id in organization_ids]
        if disabled is not None:
            organizations = [org for org in organizations if org.disabled == disabled]
        if sort in ("asc", 1):
            organizations = sorted(organizations, key=lambda org: org.id)
        else:
            organizations = sorted(organizations, key=lambda org: org.id, reverse=True)
        if start:
            organizations = [
                org
                for org in organizations
                if (org.id >= start if sort in ("asc", 1) else org.id <= start)
            ]
        if before:
            organizations = [
                org
                for org in organizations
                if (org.id < before if sort in ("asc", 1) else org.id > before)
            ]
        return Pagination[Organization].model_validate(
            {
                "object": "list",
                "data": organizations[:limit],
                "first_id": organizations[0].id if organizations else None,
                "last_id": organizations[-1].id if organizations else None,
                "has_more": len(organizations) > limit,
            }
        )

    async def retrieve_organization(
        self, organization_id: Text
    ) -> Optional["Organization"]:
        for org in self._db["organizations"]:
            if org.id == organization_id:
                return org
        return None

    async def create_organization(
        self, *, organization_create: "OrganizationCreate", owner_id: Text
    ) -> Optional["Organization"]:
        org = organization_create.to_organization(owner_id=owner_id)
        self._db["organizations"].append(org)
        return org

    async def update_organization(
        self, *, organization_id: Text, organization_update: "OrganizationUpdate"
    ) -> Optional["Organization"]:
        org = await self.retrieve_organization(organization_id)
        if org is None:
            return None
        updated_org = organization_update.apply_organization(org)
        for i, o in enumerate(self._db["organizations"]):
            if o.id == organization_id:
                self._db["organizations"][i] = updated_org
                break
        return updated_org

    async def delete_organization(
        self, *, organization_id: Text, soft_delete: bool = True
    ) -> Optional["Organization"]:
        org = await self.retrieve_organization(organization_id)
        if org is None:
            return None

        if soft_delete:
            org.disabled = True
            return org
        else:
            self._db["organizations"] = [
                o for o in self._db["organizations"] if o.id != organization_id
            ]
            return org

    async def retrieve_user(
        self, user_id: Text, *, organization_id: Optional[Text] = None
    ) -> Optional["UserInDB"]:
        for user in self._db["users"]:
            if organization_id is not None and user.organization_id != organization_id:
                continue
            if user.id == user_id:
                return user
        return None

    async def retrieve_user_by_username(
        self, username: Text, organization_id: Optional[Text] = None
    ) -> Optional["UserInDB"]:
        for user in self._db["users"]:
            if organization_id is not None and user.organization_id != organization_id:
                continue
            if user.username == username:
                return user
        return None

    async def list_users(
        self,
        *,
        organization_id: Optional[Text] = None,
        role: Optional["Role"] = None,
        roles: Optional[Sequence["Role"]] = None,
        disabled: Optional[bool] = None,
        sort: Literal["asc", "desc", 1, -1] = "asc",
        start: Optional[Text] = None,
        before: Optional[Text] = None,
        limit: Optional[int] = 20,
    ) -> Pagination[UserInDB]:
        limit = min(limit or 1000, 1000)
        users = self._db["users"]
        if organization_id is not None:
            users = [user for user in users if user.organization_id == organization_id]
        if role is not None:
            users = [user for user in users if user.role == role]
        if roles is not None:
            users = [user for user in users if user.role in roles]
        if disabled is not None:
            users = [user for user in users if user.disabled == disabled]
        if sort in ("asc", 1):
            users = sorted(users, key=lambda user: user.id)
        else:
            users = sorted(users, key=lambda user: user.id, reverse=True)
        if start:
            users = [
                user
                for user in users
                if (user.id >= start if sort in ("asc", 1) else user.id <= start)
            ]
        if before:
            users = [
                user
                for user in users
                if (user.id < before if sort in ("asc", 1) else user.id > before)
            ]
        return Pagination[UserInDB].model_validate(
            {
                "object": "list",
                "data": users[:limit],
                "first_id": users[0].id if users else None,
                "last_id": users[-1].id if users else None,
                "has_more": len(users) > limit,
            }
        )

    async def update_user(
        self,
        *,
        organization_id: Optional[Text] = None,
        user_id: Text,
        user_update: "UserUpdate",
    ) -> Optional["UserInDB"]:
        user = await self.retrieve_user(
            organization_id=organization_id, user_id=user_id
        )
        if user is None:
            return None
        updated_user = user_update.apply_user(user)
        updated_user_db = updated_user.to_db_model(hashed_password=user.hashed_password)
        for i, u in enumerate(self._db["users"]):
            if u.id == user_id:
                self._db["users"][i] = updated_user_db
                break
        return updated_user_db

    async def create_user(
        self,
        *,
        user_create: "UserCreate",
        hashed_password: Text,
        organization_id: Optional[Text] = None,
        allow_org_empty: bool = False,
    ) -> Optional["UserInDB"]:
        user = user_create.to_user(
            organization_id=organization_id,
            allow_org_empty=allow_org_empty,
        )
        if await self.retrieve_user_by_username(user.username):
            return None
        user_db = user.to_db_model(hashed_password=hashed_password)
        self._db["users"].append(user_db)
        return user_db

    async def delete_user(
        self,
        user_id: Text,
        *,
        organization_id: Optional[Text] = None,
        soft_delete: bool = True,
    ) -> bool:
        out = True
        user = await self.retrieve_user(
            organization_id=organization_id, user_id=user_id
        )
        if user is None:
            return False
        if soft_delete:
            for i, u in enumerate(self._db["users"]):
                if u.id == user_id:
                    self._db["users"][i].disabled = True
                    break
        else:
            self._db["users"] = [u for u in self._db["users"] if u.id != user_id]
            user.disabled
        return out

    async def retrieve_cached_token(self, username: Text) -> Optional["TokenInDB"]:
        for token in self._db["cached_tokens"]:
            if token.username == username and not await self.is_token_blocked(
                token.access_token
            ):
                return token
        return None

    async def caching_token(
        self, username: Text, token: Token
    ) -> Optional["TokenInDB"]:
        token_db = await self.retrieve_cached_token(username)
        if token_db:
            return None
        token_db = token.to_db_model(username=username)
        self._db["cached_tokens"].append(token_db)
        return token_db

    async def invalidate_token(self, token: Optional["Token"]):
        if token is None:
            return
        for i, t in enumerate(self._db["cached_tokens"]):
            if t.md5() == token.md5():
                self._db["cached_tokens"].pop(i)
                break
        self._db["blacklisted_tokens"].append(
            TokenBlacklisted.model_validate({"token": token.access_token})
        )
        self._db["blacklisted_tokens"].append(
            TokenBlacklisted.model_validate({"token": token.refresh_token})
        )

    async def is_token_blocked(self, token: Text) -> bool:
        for blacklisted_token in self._db["blacklisted_tokens"]:
            if blacklisted_token.token == token:
                return True
        return False

    async def create_conversation(
        self, *, conversation_create: "ConversationCreate"
    ) -> "ConversationInDB":
        """Create a new conversation in the database."""

        conversation = conversation_create.to_conversation()
        conversation = ConversationInDB.model_validate(conversation)

        # Validate conversation data
        if any(c.id == conversation.id for c in self._db["conversations"]):
            raise ValueError("Conversation already exists")

        self._db["conversations"].append(conversation)
        return conversation

    async def list_conversations(
        self,
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
        conversations = self._db["conversations"]
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
            conversations = sorted(
                conversations, key=lambda conversation: conversation.id
            )
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
        self,
        *,
        conversation_id: Text,
    ) -> Optional["ConversationInDB"]:
        """Retrieve a conversation from the database."""

        for conversation in self._db["conversations"]:
            if conversation.id == conversation_id:
                return conversation
        return None

    async def update_conversation(
        self,
        *,
        conversation_id: Text,
        conversation_update: "ConversationUpdate",
    ) -> Optional["ConversationInDB"]:
        """Update a conversation in the database."""

        conversation = await self.retrieve_conversation(conversation_id=conversation_id)
        if conversation is None:
            return None
        conversation = conversation_update.apply_conversation(conversation)
        conversation = ConversationInDB.model_validate(conversation.model_dump())
        for i, c in enumerate(self._db["conversations"]):
            if c.id == conversation_id:
                self._db["conversations"][i] = conversation
                break
        return conversation

    async def delete_conversation(
        self,
        *,
        conversation_id: Text,
        soft_delete: bool = True,
    ) -> None:
        """Delete a conversation from the database."""

        if soft_delete:
            conversation = await self.retrieve_conversation(
                conversation_id=conversation_id
            )
            if conversation is not None:
                conversation.disabled = True
                for i, c in enumerate(self._db["conversations"]):
                    if c.id == conversation_id:
                        self._db["conversations"][i] = conversation
                        break
        else:
            self._db["conversations"] = [
                c for c in self._db["conversations"] if c.id != conversation_id
            ]
