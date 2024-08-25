from types import MappingProxyType
from typing import List, Literal, Optional, Text, TypedDict

from app.db._base import DatabaseBase
from app.schemas.oauth import (
    Organization,
    OrganizationCreate,
    OrganizationUpdate,
    Token,
    TokenBlacklisted,
    TokenInDB,
    UserCreate,
    UserInDB,
    UserUpdate,
)
from app.schemas.pagination import Pagination


class _BD(TypedDict):
    organizations: List["Organization"]
    users: List["UserInDB"]
    cached_tokens: List["TokenInDB"]
    blacklisted_tokens: List["TokenBlacklisted"]


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
            organizations=[],
            users=[
                UserInDB.model_validate(u)
                for u in dict(self.fake_super_admin_init).values()
            ],
            cached_tokens=[],
            blacklisted_tokens=[],
        )

    @property
    def client(self) -> _BD:
        return self._db

    def list_organizations(
        self,
        disabled: Optional[bool] = False,
        sort: Literal["asc", "desc"] = "asc",
        start: Optional[Text] = None,
        before: Optional[Text] = None,
        limit: Optional[int] = 10,
    ) -> "Pagination[Organization]":
        limit = min(limit or 1000, 1000)
        organizations = self._db["organizations"]
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

    def retrieve_organization(self, organization_id: Text) -> Optional["Organization"]:
        for org in self._db["organizations"]:
            if org.id == organization_id:
                return org
        return None

    def create_organization(
        self, *, organization_create: "OrganizationCreate", owner_id: Text
    ) -> Optional["Organization"]:
        org = organization_create.to_organization(owner_id=owner_id)
        self._db["organizations"].append(org)
        return org

    def update_organization(
        self, *, organization_id: Text, organization_update: "OrganizationUpdate"
    ) -> Optional["Organization"]:
        org = self.retrieve_organization(organization_id)
        if org is None:
            return None
        updated_org = organization_update.apply_organization(org)
        for i, o in enumerate(self._db["organizations"]):
            if o.id == organization_id:
                self._db["organizations"][i] = updated_org
                break
        return updated_org

    def delete_organization(
        self, *, organization_id: Text, soft_delete: bool = True
    ) -> Optional["Organization"]:
        org = self.retrieve_organization(organization_id)
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

    def retrieve_user(self, user_id: Text) -> Optional["UserInDB"]:
        for user in self._db["users"]:
            if user.id == user_id:
                return user
        return None

    def retrieve_user_by_username(self, username: Text) -> Optional["UserInDB"]:
        for user in self._db["users"]:
            if user.username == username:
                return user
        return None

    def list_users(
        self,
        *,
        disabled: Optional[bool] = None,
        sort: Literal["asc", "desc", 1, -1] = "asc",
        start: Optional[Text] = None,
        before: Optional[Text] = None,
        limit: Optional[int] = 20,
    ) -> Pagination[UserInDB]:
        limit = min(limit or 1000, 1000)
        users = self._db["users"]
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

    def update_user(
        self, *, user_id: Text, user_update: "UserUpdate"
    ) -> Optional["UserInDB"]:
        user = self.retrieve_user(user_id)
        if user is None:
            return None
        updated_user = user_update.apply_user(user)
        updated_user_db = updated_user.to_db_model(hashed_password=user.hashed_password)
        for i, u in enumerate(self._db["users"]):
            if u.id == user_id:
                self._db["users"][i] = updated_user_db
                break
        return updated_user_db

    def create_user(
        self,
        *,
        user_create: "UserCreate",
        hashed_password: Text,
        organization_id: Optional[Text] = None,
        allow_organization_empty: bool = False,
    ) -> Optional["UserInDB"]:
        user = user_create.to_user(allow_organization_empty=allow_organization_empty)
        if self.retrieve_user_by_username(user.username):
            return None
        user_db = user.to_db_model(hashed_password=hashed_password)
        self._db["users"].append(user_db)
        return user_db

    def retrieve_cached_token(self, username: Text) -> Optional["TokenInDB"]:
        for token in self._db["cached_tokens"]:
            if token.username == username and not self.is_token_blocked(
                token.access_token
            ):
                return token
        return None

    def caching_token(self, username: Text, token: Token) -> Optional["TokenInDB"]:
        token_db = self.retrieve_cached_token(username)
        if token_db:
            return None
        token_db = token.to_db_model(username=username)
        self._db["cached_tokens"].append(token_db)
        return token_db

    def invalidate_token(self, token: Optional["Token"]):
        if token is None:
            return
        self._db["blacklisted_tokens"].append(
            TokenBlacklisted.model_validate({"token": token.access_token})
        )
        self._db["blacklisted_tokens"].append(
            TokenBlacklisted.model_validate({"token": token.refresh_token})
        )

    def is_token_blocked(self, token: Text) -> bool:
        for blacklisted_token in self._db["blacklisted_tokens"]:
            if blacklisted_token.token == token:
                return True
        return False
