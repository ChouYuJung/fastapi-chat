import hashlib
import json
from enum import Enum
from typing import Annotated, Literal, Optional, Required, Text, TypedDict

import uuid_utils as uuid
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class Role(str, Enum):
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"


ROLE_PERMISSIONS = {
    Role.ADMIN: ("read", "write", "delete"),
    Role.EDITOR: ("read", "write"),
    Role.VIEWER: ("read",),
}


class Token(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    access_token: Text
    refresh_token: Text
    token_type: Literal["bearer"] | Text

    @classmethod
    def from_bearer_token(cls, access_token: Text, refresh_token: Text) -> "Token":
        return cls.model_validate(
            {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
            }
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Token):
            return False
        return self.md5() == other.md5()

    def md5(self) -> Text:
        return hashlib.md5(
            json.dumps(self.model_dump(), sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()


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


class User(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, use_enum_values=True)
    id: Text = Field(..., description="User ID in UUID Version 7 format")
    username: Text = Field(..., min_length=4, max_length=32, pattern="^[a-zA-Z0-9_-]+$")
    email: Optional[EmailStr] = Field(default=None)
    full_name: Optional[Text] = Field(default=None)
    role: Role
    disabled: bool = Field(default=False)


class UserInDB(User):
    hashed_password: Text


class UserUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    email: Optional[EmailStr] = Field(default=None)
    full_name: Optional[Text] = Field(default=None)
    role: Optional[Role] = Field(default=None)
    disabled: Optional[bool] = Field(default=None)


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
