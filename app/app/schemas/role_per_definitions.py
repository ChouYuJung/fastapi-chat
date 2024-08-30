from typing import Literal, Sequence

from pydantic import BaseModel, ConfigDict, Field

from ..utils.common import str_enum_value
from .permissions import Permission
from .roles import Role


def get_role_permissions(role: "Role") -> "RolePermissionsBase":
    return {
        Role.PRISONER: PrisonerPermissions,
        Role.ORG_CLIENT: OrgClientPermissions,
        Role.ORG_VIEWER: OrgViewerPermissions,
        Role.ORG_EDITOR: OrgEditorPermissions,
        Role.ORG_ADMIN: OrgAdminPermissions,
        Role.PLATFORM_VIEWER: PlatformViewerPermissions,
        Role.PLATFORM_EDITOR: PlatformEditorPermissions,
        Role.PLATFORM_ADMIN: PlatformAdminPermissions,
        Role.SUPER_ADMIN: SuperAdminPermissions,
    }[role]()


class RolePermissionsBase(BaseModel):
    model_config = ConfigDict(use_enum_values=True)
    role: Role
    auth_level: int = Field(..., ge=0, le=100)
    manage_all_resources: bool
    # Platform content
    create_platform_content: bool
    read_platform_content: bool
    update_platform_content: bool
    delete_platform_content: bool
    # Platform users
    create_platform_user: bool
    read_platform_user: bool
    update_platform_user: bool
    delete_platform_user: bool
    # Organization content
    create_org_content: bool
    read_org_content: bool
    update_org_content: bool
    delete_org_content: bool
    # Organization users
    create_org_user: bool
    read_org_user: bool
    update_org_user: bool
    delete_org_user: bool
    # Client permissions
    org_client_use_org_content: bool
    # Forbidden
    forbidden: bool

    def is_permission_granted(
        self, required_permissions: Sequence["Permission"]
    ) -> bool:
        return all(
            getattr(self, str_enum_value(per), False) for per in required_permissions
        )


class PrisonerPermissions(RolePermissionsBase):
    role: Literal[Role.PRISONER] = Field(default=Role.PRISONER)
    auth_level: Literal[0] = Field(default=0)
    manage_all_resources: Literal[False] = Field(default=False)
    create_platform_content: Literal[False] = Field(default=False)
    read_platform_content: Literal[False] = Field(default=False)
    update_platform_content: Literal[False] = Field(default=False)
    delete_platform_content: Literal[False] = Field(default=False)
    create_platform_user: Literal[False] = Field(default=False)
    read_platform_user: Literal[False] = Field(default=False)
    update_platform_user: Literal[False] = Field(default=False)
    delete_platform_user: Literal[False] = Field(default=False)
    create_org_content: Literal[False] = Field(default=False)
    read_org_content: Literal[False] = Field(default=False)
    update_org_content: Literal[False] = Field(default=False)
    delete_org_content: Literal[False] = Field(default=False)
    create_org_user: Literal[False] = Field(default=False)
    read_org_user: Literal[False] = Field(default=False)
    update_org_user: Literal[False] = Field(default=False)
    delete_org_user: Literal[False] = Field(default=False)
    org_client_use_org_content: Literal[False] = Field(default=False)
    forbidden: Literal[True] = Field(default=True)


class OrgClientPermissions(PrisonerPermissions):
    role: Literal[Role.ORG_CLIENT] = Field(default=Role.ORG_CLIENT)
    auth_level: Literal[1] = Field(default=1)
    org_client_use_org_content: Literal[True] = Field(default=True)
    forbidden: Literal[False] = Field(default=False)


class OrgViewerPermissions(OrgClientPermissions):
    role: Literal[Role.ORG_VIEWER] = Field(default=Role.ORG_VIEWER)
    auth_level: Literal[2] = Field(default=2)
    read_org_content: Literal[True] = Field(default=True)


class OrgEditorPermissions(OrgViewerPermissions):
    role: Literal[Role.ORG_EDITOR] = Field(default=Role.ORG_EDITOR)
    auth_level: Literal[3] = Field(default=3)
    create_org_content: Literal[True] = Field(default=True)
    update_org_content: Literal[True] = Field(default=True)
    delete_org_content: Literal[True] = Field(default=True)


class OrgAdminPermissions(OrgEditorPermissions):
    role: Literal[Role.ORG_ADMIN] = Field(default=Role.ORG_ADMIN)
    auth_level: Literal[4] = Field(default=4)
    create_org_user: Literal[True] = Field(default=True)
    read_org_user: Literal[True] = Field(default=True)
    update_org_user: Literal[True] = Field(default=True)
    delete_org_user: Literal[True] = Field(default=True)


class PlatformViewerPermissions(PrisonerPermissions):
    role: Literal[Role.PLATFORM_VIEWER] = Field(default=Role.PLATFORM_VIEWER)
    auth_level: Literal[5] = Field(default=5)
    read_platform_content: Literal[True] = Field(default=True)
    read_platform_user: Literal[True] = Field(default=True)
    forbidden: Literal[False] = Field(default=False)


class PlatformEditorPermissions(PlatformViewerPermissions):
    role: Literal[Role.PLATFORM_EDITOR] = Field(default=Role.PLATFORM_EDITOR)
    auth_level: Literal[6] = Field(default=6)
    create_platform_content: Literal[True] = Field(default=True)
    update_platform_content: Literal[True] = Field(default=True)
    delete_platform_content: Literal[True] = Field(default=True)


class PlatformAdminPermissions(PlatformEditorPermissions):
    role: Literal[Role.PLATFORM_ADMIN] = Field(default=Role.PLATFORM_ADMIN)
    auth_level: Literal[7] = Field(default=7)
    create_platform_user: Literal[True] = Field(default=True)
    read_platform_user: Literal[True] = Field(default=True)
    update_platform_user: Literal[True] = Field(default=True)
    delete_platform_user: Literal[True] = Field(default=True)
    create_org_user: Literal[True] = Field(default=True)
    read_org_user: Literal[True] = Field(default=True)
    update_org_user: Literal[True] = Field(default=True)
    delete_org_user: Literal[True] = Field(default=True)


class SuperAdminPermissions(PlatformAdminPermissions):
    role: Literal[Role.SUPER_ADMIN] = Field(default=Role.SUPER_ADMIN)
    auth_level: Literal[100] = Field(default=100)
    auth_level: Literal[100] = Field(default=100)
    manage_all_resources: Literal[True] = Field(default=True)
    forbidden: Literal[False] = Field(default=False)
