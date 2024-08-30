from enum import Enum


class Role(str, Enum):
    # Platform roles
    SUPER_ADMIN = "super_admin"
    PLATFORM_ADMIN = "platform_admin"
    PLATFORM_EDITOR = "platform_editor"
    PLATFORM_VIEWER = "platform_viewer"
    # Organization roles
    ORG_ADMIN = "org_admin"
    ORG_EDITOR = "org_editor"
    ORG_VIEWER = "org_viewer"  # View org resources only
    # Organization client roles
    ORG_CLIENT = "org_client"  # Client of the organization
    # Other roles
    PRISONER = "prisoner"
