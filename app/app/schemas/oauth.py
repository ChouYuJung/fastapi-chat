import hashlib
import json
import time
from enum import Enum
from typing import Annotated, List, Literal, Optional, Required, Text, TypedDict

import uuid_utils as uuid
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class Permission(str, Enum):
    MANAGE_ALL_RESOURCES = "manage_all_resources"
    MANAGE_PLATFORM = "manage_platform"
    MANAGE_ORGANIZATIONS = "manage_organizations"
    MANAGE_ORG_CONTENT = "manage_org_content"
    MANAGE_ORG_USERS = "manage_org_users"
    USE_ORG_CONTENT = "use_org_content"


class Role(BaseModel):
    name: Text
    permissions: List[Permission]


PREDEFINED_ROLES = {
    "SUPER_ADMIN": Role(
        name="Super Admin", permissions=[Permission.MANAGE_ALL_RESOURCES]
    ),
    "PLATFORM_ADMIN": Role(
        name="Platform Admin",
        permissions=[
            Permission.MANAGE_PLATFORM,
            Permission.MANAGE_ORGANIZATIONS,
            Permission.MANAGE_ORG_USERS,
        ],
    ),
    "ORG_ADMIN": Role(
        name="Organization Admin",
        permissions=[
            Permission.MANAGE_ORG_CONTENT,
            Permission.MANAGE_ORG_USERS,
            Permission.USE_ORG_CONTENT,
        ],
    ),
    "ORG_USER": Role(
        name="Organization User", permissions=[Permission.USE_ORG_CONTENT]
    ),
}


class Organization(BaseModel):
    id: Text = Field(..., description="Organization ID in UUID Version 7 format")
    name: Text = Field(..., description="Organization name")
    owner_id: Text = Field(..., description="The initial admin user's ID")


class User(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, use_enum_values=True)
    id: Text = Field(..., description="User ID in UUID Version 7 format")
    username: Text = Field(..., min_length=4, max_length=32, pattern="^[a-zA-Z0-9_-]+$")
    email: Optional[EmailStr] = Field(default=None)
    full_name: Optional[Text] = Field(default=None)
    organization_id: Optional[Text] = Field(
        ..., description="None for Super Admin and Platform Admin"
    )
    role: Role
    disabled: bool = Field(default=False)

    def to_db_model(self, *, hashed_password: Text) -> "UserInDB":
        data = self.model_dump()
        data["hashed_password"] = hashed_password
        return UserInDB.model_validate(data)


class UserInDB(User):
    hashed_password: Text


class UserUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    email: Optional[EmailStr] = Field(default=None)
    full_name: Optional[Text] = Field(default=None)
    role: Optional[Role] = Field(default=None)
    disabled: Optional[bool] = Field(default=None)

    def apply_user(self, user: User) -> User:
        user_data = user.model_dump()
        user_data.update(
            self.model_dump(
                exclude_none=True, exclude={"id", "username", "hashed_password"}
            )
        )
        return User.model_validate(user_data)


class UserCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    username: Text
    email: EmailStr
    password: Text
    full_name: Text
    role: Role = Field(default=Role.VIEWER)

    def to_user(
        self, *, user_id: Optional[Text] = None, disabled: bool = False
    ) -> User:
        return User.model_validate(
            {
                "id": user_id or str(uuid.uuid7()),
                "username": self.username,
                "email": self.email,
                "full_name": self.full_name,
                "role": self.role,
                "disabled": disabled,
            }
        )


class UserGuestRegister(UserCreate):
    model_config = ConfigDict(str_strip_whitespace=True)
    role: Literal[Role.VIEWER] = Field(default=Role.VIEWER)


class Token(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    access_token: Text
    refresh_token: Text
    token_type: Literal["bearer"] | Text
    expires_at: int

    @classmethod
    def from_bearer_token(
        cls, access_token: Text, refresh_token: Text, expires_at: int
    ) -> "Token":
        return cls.model_validate(
            {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_at": expires_at,
            }
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return self.md5() == other.md5()

    def md5(self) -> Text:
        return hashlib.md5(
            json.dumps(self.model_dump(), sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()

    def to_db_model(self, *, username: Text) -> "TokenInDB":
        token_data = self.model_dump()
        token_data["username"] = username
        return TokenInDB.model_validate(token_data)


class TokenInDB(Token):
    model_config = ConfigDict(str_strip_whitespace=True)
    username: Text


class TokenBlacklisted(BaseModel):
    token: Text
    created_at: int = Field(default_factory=lambda: int(time.time()))


class RefreshTokenRequest(BaseModel):
    grant_type: Literal["refresh_token"] = Field(...)
    refresh_token: Text = Field(...)
    client_id: Optional[Text] = Field(default=None)
    client_secret: Optional[Text] = Field(default=None)


class TokenData(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    username: Optional[Text] = None


class PayloadParam(TypedDict, total=False):
    sub: Required[Annotated[Text, "subject or username"]]
    exp: Required[Annotated[int, "expiration time in seconds"]]
