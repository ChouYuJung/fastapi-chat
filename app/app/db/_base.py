from typing import TYPE_CHECKING, Literal, Optional, Sequence, Text

from yarl import URL

if TYPE_CHECKING:
    from app.schemas.conversations import (
        ConversationCreate,
        ConversationInDB,
        ConversationUpdate,
    )
    from app.schemas.oauth import (
        Organization,
        OrganizationCreate,
        OrganizationUpdate,
        Role,
        Token,
        TokenInDB,
        UserCreate,
        UserInDB,
        UserUpdate,
    )
    from app.schemas.pagination import Pagination


class DatabaseBase:
    _url: URL | Text | None

    @classmethod
    def from_url(cls, url: URL | Text | None):
        from app.db._memory import DatabaseMemory

        db: DatabaseBase
        if url is None:
            db = DatabaseMemory()
        elif isinstance(url, Text) and url.strip() == "":
            db = DatabaseMemory()
        elif str(url).startswith("memory"):
            db = DatabaseMemory()
        else:
            db = DatabaseMemory()
        return db

    @property
    def url(self) -> URL | None:
        if hasattr(self, "_url"):
            if self._url is None:
                return None
            return URL(self._url)
        return None

    @property
    def url_safe(self) -> URL | None:
        url = self.url
        if url is not None:
            url = url.with_password("****")
        return url

    @property
    def client(self):
        raise NotImplementedError

    async def touch(self):
        pass

    async def list_organizations(
        self,
        disabled: Optional[bool] = False,
        sort: Literal["asc", "desc"] = "asc",
        start: Optional[Text] = None,
        before: Optional[Text] = None,
        limit: Optional[int] = 10,
    ) -> "Pagination[Organization]":
        raise NotImplementedError

    async def retrieve_organization(
        self, organization_id: Text
    ) -> Optional["Organization"]:
        raise NotImplementedError

    async def create_organization(
        self, *, organization_create: "OrganizationCreate", owner_id: Text
    ) -> Optional["Organization"]:
        raise NotImplementedError

    async def update_organization(
        self, *, organization_id: Text, organization_update: "OrganizationUpdate"
    ) -> Optional["Organization"]:
        raise NotImplementedError

    async def delete_organization(
        self, *, organization_id: Text, soft_delete: bool = True
    ) -> Optional["Organization"]:
        raise NotImplementedError

    async def retrieve_user(
        self, user_id: Text, *, organization_id: Optional[Text] = None
    ) -> Optional["UserInDB"]:
        raise NotImplementedError

    async def retrieve_user_by_username(
        self, username: Text, organization_id: Optional[Text] = None
    ) -> Optional["UserInDB"]:
        raise NotImplementedError

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
    ) -> "Pagination[UserInDB]":
        raise NotImplementedError

    async def update_user(
        self,
        *,
        organization_id: Optional[Text] = None,
        user_id: Text,
        user_update: "UserUpdate",
    ) -> Optional["UserInDB"]:
        raise NotImplementedError

    async def create_user(
        self,
        *,
        user_create: "UserCreate",
        hashed_password: Text,
        organization_id: Optional[Text] = None,
        allow_org_empty: bool = False,
    ) -> Optional["UserInDB"]:
        raise NotImplementedError

    async def delete_user(
        self,
        user_id: Text,
        *,
        organization_id: Optional[Text] = None,
        soft_delete: bool = True,
    ) -> bool:
        raise NotImplementedError

    async def retrieve_cached_token(self, username: Text) -> Optional["TokenInDB"]:
        raise NotImplementedError

    async def caching_token(
        self, username: Text, token: "Token"
    ) -> Optional["TokenInDB"]:
        raise NotImplementedError

    async def invalidate_token(self, token: Optional["Token"]):
        raise NotImplementedError

    async def is_token_blocked(self, token: Text) -> bool:
        raise NotImplementedError

    async def create_conversation(
        self, *, conversation_create: "ConversationCreate"
    ) -> "ConversationInDB":
        raise NotImplementedError

    async def list_conversations(
        self,
        *,
        participants: Optional[Sequence[Text]] = None,
        disabled: Optional[bool] = None,
        sort: Literal["asc", "desc", 1, -1] = "asc",
        start: Optional[Text] = None,
        before: Optional[Text] = None,
        limit: Optional[int] = 20,
    ) -> "Pagination[ConversationInDB]":
        raise NotImplementedError

    async def retrieve_conversation(
        self, *, conversation_id: Text
    ) -> Optional["ConversationInDB"]:
        raise NotImplementedError

    async def update_conversation(
        self, *, conversation_id: Text, conversation_update: "ConversationUpdate"
    ) -> Optional["ConversationInDB"]:
        raise NotImplementedError

    async def delete_conversation(
        self, *, conversation_id: Text, soft_delete: bool = True
    ) -> None:
        raise NotImplementedError

    def __str__(self) -> Text:
        _attr = ""
        if self.url_safe:
            _attr = f"url={self.url_safe}"
        return f"{self.__class__.__name__}({_attr})"
