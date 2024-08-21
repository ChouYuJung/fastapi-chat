from enum import Enum
from typing import Literal, Optional, Text

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
    token_type: Text


class TokenData(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    username: Optional[Text] = None


class User(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, use_enum_values=True)
    id: Text = Field(..., description="User ID in UUID Version 7 format")
    username: Text = Field(..., min_length=4, max_length=32, pattern="^[a-zA-Z0-9_-]+$")
    email: EmailStr
    full_name: Optional[Text] = Field(default=None)
    role: Role
    disabled: bool = Field(default=False)


class UserInDB(User):
    hashed_password: Text


class LoginResponse(BaseModel):
    access_token: Text
    token_type: Literal["bearer"]
