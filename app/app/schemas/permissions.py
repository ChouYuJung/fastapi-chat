from enum import Enum


class Permission(str, Enum):
    MANAGE_ALL_RESOURCES = "manage_all_resources"
    # Platform content
    CREATE_PLATFORM_CONTENT = "create_platform_content"
    READ_PLATFORM_CONTENT = "read_platform_content"
    UPDATE_PLATFORM_CONTENT = "update_platform_content"
    DELETE_PLATFORM_CONTENT = "delete_platform_content"
    # Platform users
    CREATE_PLATFORM_USER = "create_platform_user"
    READ_PLATFORM_USER = "read_platform_user"
    UPDATE_PLATFORM_USER = "update_platform_user"
    DELETE_PLATFORM_USER = "delete_platform_user"
    # Organizations management
    CREATE_ORG = "create_org"
    READ_ORG = "read_org"
    UPDATE_ORG = "update_org"
    DELETE_ORG = "delete_org"
    # Organization content
    CREATE_ORG_CONTENT = "create_org_content"
    READ_ORG_CONTENT = "read_org_content"
    UPDATE_ORG_CONTENT = "update_org_content"
    DELETE_ORG_CONTENT = "delete_org_content"
    # Organization users
    CREATE_ORG_USER = "create_org_user"
    READ_ORG_USER = "read_org_user"
    UPDATE_ORG_USER = "update_org_user"
    DELETE_ORG_USER = "delete_org_user"
    # Client permissions
    ORG_CLIENT_USE_ORG_CONTENT = "org_client_use_org_content"
    # Forbidden
    FORBIDDEN = "forbidden"
