from enum import Enum
from typing import Literal, Optional, Text

import uuid_utils as uuid
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class Role(str, Enum):
    ADMIN = "admin"
    CONTRIBUTOR = "contributor"
    VIEWER = "viewer"


ROLE_PERMISSIONS = {
    Role.ADMIN: ("read", "write", "delete"),
    Role.CONTRIBUTOR: ("read", "write"),
    Role.VIEWER: ("read",),
}


class Token(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    access_token: Text
    token_type: Literal["bearer"] | Text


class TokenData(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    username: Optional[Text] = None


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
