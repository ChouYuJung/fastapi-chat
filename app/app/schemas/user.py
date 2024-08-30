from typing import Literal, Optional, Text

import uuid_utils as uuid
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from .roles import Role


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
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    email: Optional[EmailStr] = Field(default=None)
    full_name: Optional[Text] = Field(default=None)
    role: Optional[
        Literal[
            Role.ORG_ADMIN,
            Role.ORG_EDITOR,
            Role.ORG_VIEWER,
            Role.ORG_CLIENT,
            Role.PRISONER,
        ]
    ] = Field(default=None)
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
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    username: Text
    email: EmailStr
    password: Text
    full_name: Text
    role: Literal[
        Role.ORG_ADMIN,
        Role.ORG_EDITOR,
        Role.ORG_VIEWER,
        Role.ORG_CLIENT,
        Role.PRISONER,
    ] = Field(default=Role.ORG_CLIENT)
    disabled: bool = False

    def to_user(
        self,
        *,
        user_id: Optional[Text] = None,
        organization_id: Optional[Text] = None,
        allow_org_empty: bool = False,
    ) -> User:
        if not allow_org_empty and not organization_id:
            raise ValueError("Organization ID is required")
        return User.model_validate(
            {
                "id": user_id or str(uuid.uuid7()),
                "username": self.username,
                "email": self.email,
                "full_name": self.full_name,
                "organization_id": organization_id,
                "role": self.role,
                "disabled": self.disabled,
            }
        )


class UserGuestRegister(UserCreate):
    model_config = ConfigDict(str_strip_whitespace=True)
    role: Literal[Role.ORG_CLIENT] = Field(default=Role.ORG_CLIENT)


class PlatformUserCreate(UserCreate):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    role: Literal[
        Role.PLATFORM_ADMIN,
        Role.PLATFORM_EDITOR,
        Role.PLATFORM_VIEWER,
        Role.PRISONER,
    ] = Field(default=Role.PLATFORM_VIEWER)


class PlatformUserUpdate(UserUpdate):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    role: Optional[
        Literal[
            Role.PLATFORM_ADMIN,
            Role.PLATFORM_EDITOR,
            Role.PLATFORM_VIEWER,
            Role.PRISONER,
        ]
    ] = Field(default=None)
