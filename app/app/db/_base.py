from typing import TYPE_CHECKING, Literal, Optional, Text

from yarl import URL

if TYPE_CHECKING:
    from app.schemas.oauth import (
        Organization,
        OrganizationCreate,
        OrganizationUpdate,
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

    def touch(self):
        pass

    def list_organizations(
        self,
        disabled: Optional[bool] = False,
        sort: Literal["asc", "desc"] = "asc",
        start: Optional[Text] = None,
        before: Optional[Text] = None,
        limit: Optional[int] = 10,
    ) -> "Pagination[Organization]":
        raise NotImplementedError

    def retrieve_organization(self, organization_id: Text) -> Optional["Organization"]:
        raise NotImplementedError

    def create_organization(
        self, *, organization_create: "OrganizationCreate", owner_id: Text
    ) -> Optional["Organization"]:
        raise NotImplementedError

    def update_organization(
        self, *, organization_id: Text, organization_update: "OrganizationUpdate"
    ) -> Optional["Organization"]:
        raise NotImplementedError

    def delete_organization(
        self, *, organization_id: Text, soft_delete: bool = True
    ) -> Optional["Organization"]:
        raise NotImplementedError

    def retrieve_user(self, user_id: Text) -> Optional["UserInDB"]:
        raise NotImplementedError

    def retrieve_user_by_username(self, username: Text) -> Optional["UserInDB"]:
        raise NotImplementedError

    def list_users(
        self,
        *,
        disabled: Optional[bool] = None,
        sort: Literal["asc", "desc", 1, -1] = "asc",
        start: Optional[Text] = None,
        before: Optional[Text] = None,
        limit: Optional[int] = 20,
    ) -> "Pagination[UserInDB]":
        raise NotImplementedError

    def update_user(
        self, *, user_id: Text, user_update: "UserUpdate"
    ) -> Optional["UserInDB"]:
        raise NotImplementedError

    def create_user(
        self, *, user_create: "UserCreate", hashed_password: Text
    ) -> Optional["UserInDB"]:
        raise NotImplementedError

    def retrieve_cached_token(self, username: Text) -> Optional["TokenInDB"]:
        raise NotImplementedError

    def caching_token(self, username: Text, token: "Token") -> Optional["TokenInDB"]:
        raise NotImplementedError

    def invalidate_token(self, token: Optional["Token"]):
        raise NotImplementedError

    def is_token_blocked(self, token: Text) -> bool:
        raise NotImplementedError

    def __str__(self) -> Text:
        _attr = ""
        if self.url_safe:
            _attr = f"url={self.url_safe}"
        return f"{self.__class__.__name__}({_attr})"
