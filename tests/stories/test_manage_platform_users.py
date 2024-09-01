import pytest
from faker import Faker
from fastapi.testclient import TestClient

from fastapi_chat.schemas.pagination import Pagination
from fastapi_chat.schemas.roles import Role
from fastapi_chat.schemas.users import PlatformUserCreate, PlatformUserUpdate, User
from tests.utils import LoginData, get_me, login

fake = Faker()


@pytest.mark.asyncio
async def test_init_platform_status(client: TestClient, user_super_admin: LoginData):
    token = login(client, **user_super_admin.model_dump())
    # Check initial database state
    response = client.get("/platform/users", headers=token.to_headers())
    response.raise_for_status()
    user_list_res = Pagination[User].model_validate(response.json())
    assert len(user_list_res.data) == 0  # No platform users in the database
    # Superuser would not be in the list of platform users


@pytest.mark.asyncio
async def test_create_platform_admin(
    client: TestClient, user_super_admin: LoginData, user_platform_admin: LoginData
):
    token = login(client, **user_super_admin.model_dump())
    assert get_me(client, token).role == Role.SUPER_ADMIN

    # Create the first new platform user by superuser
    new_user_create = PlatformUserCreate.model_validate(
        {
            "username": user_platform_admin.username,
            "email": fake.safe_email(),
            "password": user_platform_admin.password,
            "full_name": fake.name(),
            "role": Role.PLATFORM_ADMIN.value,
        }
    )
    response = client.post(
        "/platform/users",
        json=new_user_create.model_dump(exclude_none=True),
        headers=token.to_headers(),
    )
    response.raise_for_status()
    platform_user = User.model_validate(response.json())
    assert platform_user.role == Role.PLATFORM_ADMIN
    assert platform_user.organization_id is None
    assert platform_user.disabled is False

    # Check that the new platform user is in the list of platform users
    response = client.get("/platform/users", headers=token.to_headers())
    response.raise_for_status()
    user_list_res = Pagination[User].model_validate(response.json())
    assert len(user_list_res.data) == 1
    assert user_list_res.data[0].id == platform_user.id

    # Retrieve the new platform user
    response = client.get(
        f"/platform/users/{platform_user.id}", headers=token.to_headers()
    )
    response.raise_for_status()
    retrieved_platform_user = User.model_validate(response.json())
    assert retrieved_platform_user.role == Role.PLATFORM_ADMIN
    assert retrieved_platform_user.organization_id is None
    assert retrieved_platform_user.disabled is False
    assert platform_user.id == retrieved_platform_user.id
    platform_user = retrieved_platform_user


@pytest.mark.asyncio
async def test_platform_admin_create_users(
    client: TestClient,
    user_platform_admin: LoginData,
    user_platform_editor: LoginData,
    user_platform_viewer: LoginData,
):
    token = login(client, **user_platform_admin.model_dump())
    assert get_me(client, token).role == Role.PLATFORM_ADMIN

    # Create another platform users
    platform_editor_create = PlatformUserCreate.model_validate(
        {
            "username": user_platform_editor.username,
            "email": fake.safe_email(),
            "password": user_platform_editor.password,
            "full_name": fake.name(),
            "role": Role.PLATFORM_EDITOR.value,
        }
    )
    platform_editor = User.model_validate(
        client.post(
            "/platform/users",
            json=platform_editor_create.model_dump(exclude_none=True),
            headers=token.to_headers(),
        ).json()
    )
    assert platform_editor.role == Role.PLATFORM_EDITOR
    assert platform_editor.organization_id is None
    assert platform_editor.disabled is False
    # Create a platform viewer
    platform_viewer_create = PlatformUserCreate.model_validate(
        {
            "username": user_platform_viewer.username,
            "email": fake.safe_email(),
            "password": user_platform_viewer.password,
            "full_name": fake.name(),
            "role": Role.PLATFORM_VIEWER.value,
        }
    )
    platform_viewer = User.model_validate(
        client.post(
            "/platform/users",
            json=platform_viewer_create.model_dump(exclude_none=True),
            headers=token.to_headers(),
        ).json()
    )
    assert platform_viewer.role == Role.PLATFORM_VIEWER
    assert platform_viewer.organization_id is None
    assert platform_viewer.disabled is False

    # Retrieve the list of platform users
    response = client.get("/platform/users", headers=token.to_headers())
    response.raise_for_status()
    user_list_res = Pagination[User].model_validate(response.json())
    assert len(user_list_res.data) == 3


@pytest.mark.asyncio
async def test_platform_admin_update_users(
    client: TestClient, user_platform_admin: LoginData, user_platform_viewer: LoginData
):
    token = login(client, **user_platform_admin.model_dump())
    assert get_me(client, token).role == Role.PLATFORM_ADMIN

    # Update the platform editor
    platform_update = PlatformUserUpdate.model_validate(
        {
            "full_name": fake.name(),
            "role": Role.PLATFORM_EDITOR.value,
            "disabled": False,
        }
    )
    updated_platform_viewer = User.model_validate(
        client.put(
            f"/platform/users/{get_me(client, user_platform_viewer).id}",
            json=platform_update.model_dump(exclude_none=True),
            headers=token.to_headers(),
        ).json()
    )
    assert updated_platform_viewer.role == Role.PLATFORM_EDITOR
    assert updated_platform_viewer.organization_id is None
    assert updated_platform_viewer.disabled is False


@pytest.mark.asyncio
async def test_platform_admin_delete_users(
    client: TestClient, user_platform_admin: LoginData, user_platform_viewer: LoginData
):
    token = login(client, **user_platform_admin.model_dump())
    assert get_me(client, token).role == Role.PLATFORM_ADMIN

    # Delete the platform viewer
    response = client.delete(
        f"/platform/users/{get_me(client, user_platform_viewer).id}",
        headers=token.to_headers(),
    )
    response.raise_for_status()

    # Retrieve the list of platform users
    response = client.get("/platform/users", headers=token.to_headers())
    response.raise_for_status()
    user_list_res = Pagination[User].model_validate(response.json())
    assert len(user_list_res.data) == 3
