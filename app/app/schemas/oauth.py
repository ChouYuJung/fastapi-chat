import hashlib
import json
import time
from enum import Enum
from types import MappingProxyType
from typing import Annotated, Dict, List, Literal, Optional, Required, Text, TypedDict

import uuid_utils as uuid
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class Role(str, Enum):
    SUPER_ADMIN = "super_admin"
    PLATFORM_ADMIN = "platform_admin"
    ORG_ADMIN = "org_admin"
    ORG_USER = "org_user"
    ORG_GUEST = "org_guest"


class Permission(str, Enum):
    MANAGE_ALL_RESOURCES = "manage_all_resources"
    MANAGE_PLATFORM = "manage_platform"
    MANAGE_ORGANIZATIONS = "manage_organizations"
    MANAGE_ORG_CONTENT = "manage_org_content"
    MANAGE_ORG_USERS = "manage_org_users"
    USE_ORG_CONTENT = "use_org_content"


class RolePermission(BaseModel):
    name: Text
    permissions: List[Permission]
    authority_level: int = Field(
        default=0, description="The authority level of the role", ge=0, le=100
    )


class RolePermissionSuperAdmin(RolePermission):
    name: Literal[Role.SUPER_ADMIN] = Field(
        default=Role.SUPER_ADMIN, description="Super Admin"
    )
    permissions: List[Literal[Permission.MANAGE_ALL_RESOURCES]] = Field(
        default_factory=lambda: [Permission.MANAGE_ALL_RESOURCES],
        description="Super Admin has all permissions",
    )
    authority_level: Literal[100] = Field(default=100)


class RolePermissionPlatformAdmin(RolePermission):
    name: Literal[Role.PLATFORM_ADMIN] = Field(
        default=Role.PLATFORM_ADMIN, description="Platform Admin"
    )
    permissions: List[
        Literal[
            Permission.MANAGE_PLATFORM,
            Permission.MANAGE_ORGANIZATIONS,
            Permission.MANAGE_ORG_CONTENT,
            Permission.MANAGE_ORG_USERS,
            Permission.MANAGE_ORG_USERS,
            Permission.USE_ORG_CONTENT,
        ]
    ] = Field(
        default_factory=lambda: [
            Permission.MANAGE_PLATFORM,
            Permission.MANAGE_ORGANIZATIONS,
            Permission.MANAGE_ORG_CONTENT,
            Permission.MANAGE_ORG_USERS,
            Permission.MANAGE_ORG_USERS,
            Permission.USE_ORG_CONTENT,
        ],
        description="Platform Admin has platform-wide permissions",
    )
    authority_level: Literal[3] = Field(default=3)


class RolePermissionOrgAdmin(RolePermission):
    name: Literal[Role.ORG_ADMIN] = Field(
        default=Role.ORG_ADMIN, description="Organization Admin"
    )
    permissions: List[
        Literal[
            Permission.MANAGE_ORG_CONTENT,
            Permission.MANAGE_ORG_USERS,
            Permission.USE_ORG_CONTENT,
        ]
    ] = Field(
        default_factory=lambda: [
            Permission.MANAGE_ORG_CONTENT,
            Permission.MANAGE_ORG_USERS,
            Permission.USE_ORG_CONTENT,
        ],
        description="Organization Admin has organization-wide permissions",
    )
    authority_level: Literal[2] = Field(default=2)


class RolePermissionOrgUser(RolePermission):
    name: Literal[Role.ORG_USER] = Field(
        default=Role.ORG_USER, description="Organization User"
    )
    permissions: List[Literal[Permission.USE_ORG_CONTENT]] = Field(
        default_factory=lambda: [Permission.USE_ORG_CONTENT],
        description="Organization could use organization content",
    )
    authority_level: Literal[1] = Field(default=1)


class RolePermissionOrgGuest(RolePermission):
    name: Literal[Role.ORG_GUEST] = Field(
        default=Role.ORG_GUEST, description="Organization Guest"
    )
    permissions: List[Literal[Permission.USE_ORG_CONTENT]] = Field(
        default_factory=lambda: [Permission.USE_ORG_CONTENT],
        description="Organization Guest could use organization content",
    )
    authority_level: Literal[0] = Field(default=0)


_ROLE_PERMISSIONS: Dict[Role, RolePermission] = {
    Role.SUPER_ADMIN: RolePermissionSuperAdmin(),
    Role.PLATFORM_ADMIN: RolePermissionPlatformAdmin(),
    Role.ORG_ADMIN: RolePermissionOrgAdmin(),
    Role.ORG_USER: RolePermissionOrgUser(),
}
ROLE_PERMISSIONS = MappingProxyType(_ROLE_PERMISSIONS)


class Organization(BaseModel):
    id: Text = Field(..., description="Organization ID in UUID Version 7 format")
    name: Text = Field(..., description="Organization name")
    description: Optional[Text] = Field(default=None)
    owner_id: Text = Field(..., description="The initial admin user's ID")
    disabled: bool = Field(default=False)


class OrganizationCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    name: Text = Field(..., description="Organization name")
    description: Optional[Text] = Field(default=None)
    disabled: bool = Field(default=False)

    def to_organization(
        self, *, organization_id: Optional[Text] = None, owner_id: Text
    ) -> Organization:
        return Organization.model_validate(
            {
                "id": organization_id or str(uuid.uuid7()),
                "name": self.name,
                "description": self.description,
                "owner_id": owner_id,
                "disabled": self.disabled,
            }
        )


class OrganizationUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    name: Optional[Text] = Field(default=None, description="Organization name")
    description: Optional[Text] = Field(default=None)
    disabled: Optional[bool] = Field(default=None)

    def apply_organization(self, organization: Organization) -> Organization:
        organization_data = organization.model_dump()
        organization_data.update(
            self.model_dump(exclude_none=True, exclude={"id", "owner_id"})
        )
        return Organization.model_validate(organization_data)


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
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    username: Text
    email: EmailStr
    password: Text
    full_name: Text
    role: Role = Field(default=Role.ORG_GUEST)
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
    role: Literal[Role.ORG_GUEST] = Field(default=Role.ORG_GUEST)


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
    username: Text

    @classmethod
    def from_payload(cls, payload: Dict) -> "TokenData":
        return TokenData.model_validate({"username": payload.get("sub")})


class PayloadParam(TypedDict, total=False):
    sub: Required[Annotated[Text, "subject or username"]]
    exp: Required[Annotated[int, "expiration time in seconds"]]
