import httpx
import pytest
from app.schemas.oauth import Role, User, UserCreate, UserUpdate
from app.schemas.pagination import Pagination
from faker import Faker
from fastapi.testclient import TestClient

from tests.utils import LoginData, get_token

fake = Faker()

superuser_login_data = LoginData(username="admin", password="pass1234")
platform_user_1_login_data = LoginData(
    username=fake.user_name(), password=fake.password()
)
platform_user_2_login_data = LoginData(
    username=fake.user_name(), password=fake.password()
)


@pytest.mark.asyncio
async def test_init_platform_status(client: TestClient):
    # Check initial database state
    response = client.get(
        "/platform/users",
        headers=get_token(client=client, **superuser_login_data).to_headers(),
    )
    response.raise_for_status()
    user_list_res = Pagination[User].model_validate(response.json())
    assert len(user_list_res.data) == 0  # No platform users in the database
    # Superuser would not be in the list of platform users


@pytest.mark.asyncio
async def test_create_platform_users(client: TestClient):
    # Create the first new platform user by superuser
    new_user_create = UserCreate.model_validate(
        {
            "username": platform_user_1_login_data["username"],
            "email": fake.safe_email(),
            "password": platform_user_1_login_data["password"],
            "full_name": fake.name(),
            "role": Role.PLATFORM_ADMIN.value,
        }
    )
    response = client.post(
        "/platform/users",
        json=new_user_create.model_dump(exclude_none=True),
        headers=get_token(client=client, **superuser_login_data).to_headers(),
    )
    response.raise_for_status()
    platform_user = User.model_validate(response.json())
    assert platform_user.role == Role.PLATFORM_ADMIN
    assert platform_user.organization_id is None
    assert platform_user.disabled is False

    # Check that the new platform user is in the list of platform users
    response = client.get(
        "/platform/users",
        headers=get_token(client=client, **superuser_login_data).to_headers(),
    )
    response.raise_for_status()
    user_list_res = Pagination[User].model_validate(response.json())
    assert len(user_list_res.data) == 1
    assert user_list_res.data[0].id == platform_user.id

    # Retrieve the new platform user
    response = client.get(
        f"/platform/users/{platform_user.id}",
        headers=get_token(client=client, **superuser_login_data).to_headers(),
    )
    response.raise_for_status()
    retrieved_platform_user = User.model_validate(response.json())
    assert retrieved_platform_user.role == Role.PLATFORM_ADMIN
    assert retrieved_platform_user.organization_id is None
    assert retrieved_platform_user.disabled is False
    assert platform_user.id == retrieved_platform_user.id
    platform_user = retrieved_platform_user


@pytest.mark.asyncio
async def test_platform_user_operations(client: TestClient):
    # Create another platform user
    new_user_2_create = UserCreate.model_validate(
        {
            "username": platform_user_2_login_data["username"],
            "email": fake.safe_email(),
            "password": platform_user_2_login_data["password"],
            "full_name": fake.name(),
            "role": Role.PLATFORM_ADMIN.value,
        }
    )
    response = client.post(
        "/platform/users",
        json=new_user_2_create.model_dump(exclude_none=True),
        headers=get_token(client=client, **platform_user_1_login_data).to_headers(),
    )
    response.raise_for_status()
    platform_user_2 = User.model_validate(response.json())
    assert platform_user_2.role == Role.PLATFORM_ADMIN
    assert platform_user_2.organization_id is None
    assert platform_user_2.disabled is False

    # Check that the new platform user is in the list of platform users
    response = client.get(
        "/platform/users",
        headers=get_token(client=client, **platform_user_1_login_data).to_headers(),
    )
    response.raise_for_status()
    user_list_res = Pagination[User].model_validate(response.json())
    assert len(user_list_res.data) == 2
    assert any(user.id == platform_user_2.id for user in user_list_res.data)

    # Update the new platform user
    user_update = UserUpdate.model_validate({"email": fake.safe_email()})
    response = client.put(
        f"/platform/users/{platform_user_2.id}",
        json=user_update.model_dump(exclude_none=True),
        headers=get_token(client=client, **platform_user_1_login_data).to_headers(),
    )
    response.raise_for_status()
    updated_platform_user = User.model_validate(response.json())
    assert updated_platform_user.email == user_update.email
    platform_user_2 = updated_platform_user

    # Retrieve the updated platform user
    response = client.get(
        f"/platform/users/{platform_user_2.id}",
        headers=get_token(client=client, **platform_user_1_login_data).to_headers(),
    )
    response.raise_for_status()
    retrieved_updated_platform_user = User.model_validate(response.json())
    assert retrieved_updated_platform_user.email == platform_user_2.email

    assert retrieved_updated_platform_user.id == platform_user_2.id
    platform_user_2 = retrieved_updated_platform_user

    # Delete the new platform user (soft delete)
    response = client.delete(
        f"/platform/users/{platform_user_2.id}",
        headers=get_token(client=client, **platform_user_1_login_data).to_headers(),
    )
    response.raise_for_status()
    response = client.get(
        f"/platform/users/{platform_user_2.id}",
        headers=get_token(client=client, **platform_user_1_login_data).to_headers(),
    )
    response.raise_for_status()
    platform_user_2 = User.model_validate(response.json())
    assert platform_user_2.disabled is True
    # Check list users filtered disabled
    response = client.get(
        "/platform/users",
        headers=get_token(client=client, **platform_user_1_login_data).to_headers(),
        params={"disabled": False},
    )
    response.raise_for_status()
    user_list_res = Pagination[User].model_validate(response.json())
    assert len(user_list_res.data) == 1
    assert not any(user.id == platform_user_2.id for user in user_list_res.data)


@pytest.mark.asyncio
async def test_platform_user_failures(client: TestClient):
    user_me = User.model_validate(
        client.get(
            "/auth/me",
            headers=get_token(client=client, **platform_user_1_login_data).to_headers(),
        ).json()
    )

    # Try modify self as platform user
    with pytest.raises(httpx.HTTPStatusError):
        response = client.put(
            f"/platform/users/{user_me.id}",
            json={"role": Role.SUPER_ADMIN.value},
            headers=get_token(client=client, **platform_user_1_login_data).to_headers(),
        )
        response.raise_for_status()

    # Try modify the superuser as platform user
    superuser = User.model_validate(
        client.get(
            "/auth/me",
            headers=get_token(client=client, **superuser_login_data).to_headers(),
        ).json()
    )
    with pytest.raises(httpx.HTTPStatusError):
        response = client.put(
            f"/platform/users/{superuser.id}",
            json={"role": Role.PLATFORM_ADMIN.value},
            headers=get_token(client=client, **platform_user_1_login_data).to_headers(),
        )
        response.raise_for_status()
