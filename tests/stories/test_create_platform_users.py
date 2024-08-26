from typing import Dict, Text, TypedDict

import pytest
from app.schemas.oauth import Role, Token, User, UserCreate, UserUpdate
from app.schemas.pagination import Pagination
from faker import Faker
from fastapi.testclient import TestClient

fake = Faker()

username_token: Dict[Text, Token] = {}


def get_token(
    client: TestClient, *, username: Text, password: Text, reclaim: bool = False
) -> Token:
    global username_token

    if username in username_token and not reclaim:
        return username_token[username]

    login_data = {"username": username, "password": password}
    response = client.post("/auth/login", data=login_data)
    response.raise_for_status()

    token = Token.model_validate(response.json())
    username_token[username] = token
    return token


class LoginData(TypedDict):
    username: Text
    password: Text


@pytest.mark.asyncio
async def test_create_platform_users(client: TestClient):
    superuser_login_data = LoginData(username="admin", password="pass1234")

    # Check initial database state
    response = client.get(
        "/platform/users",
        headers=get_token(client=client, **superuser_login_data).to_headers(),
    )
    response.raise_for_status()
    user_list_res = Pagination[User].model_validate(response.json())
    assert len(user_list_res.data) == 0  # No platform users in the database
    # Superuser would not be in the list of platform users

    # Create a new platform user
    new_user_create = UserCreate.model_validate(
        {
            "username": fake.user_name(),
            "email": fake.safe_email(),
            "password": "pass1234",
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

    # Use platform user to do operations
    platform_user_login_data = LoginData(
        username=new_user_create.username, password=new_user_create.password
    )
    # Create another platform user
    new_user_2_create = UserCreate.model_validate(
        {
            "username": fake.user_name(),
            "email": fake.safe_email(),
            "password": "pass1234",
            "full_name": fake.name(),
            "role": Role.PLATFORM_ADMIN.value,
        }
    )
    response = client.post(
        "/platform/users",
        json=new_user_2_create.model_dump(exclude_none=True),
        headers=get_token(client=client, **platform_user_login_data).to_headers(),
    )
    response.raise_for_status()
    platform_user_2 = User.model_validate(response.json())
    assert platform_user_2.role == Role.PLATFORM_ADMIN
    assert platform_user_2.organization_id is None
    assert platform_user_2.disabled is False
    # Update the new platform user
    user_update = UserUpdate.model_validate(
        {"email": fake.safe_email(), "disabled": True}
    )
    response = client.put(
        f"/platform/users/{platform_user_2.id}",
        json=user_update.model_dump(exclude_none=True),
        headers=get_token(client=client, **platform_user_login_data).to_headers(),
    )
    response.raise_for_status()
    updated_platform_user = User.model_validate(response.json())
    assert updated_platform_user.email == user_update.email
    assert updated_platform_user.disabled is True
    platform_user_2 = updated_platform_user
    # Check that the updated platform user is in the list of platform users
    response = client.get(
        "/platform/users",
        headers=get_token(client=client, **superuser_login_data).to_headers(),
    )
    response.raise_for_status()
    user_list_res = Pagination[User].model_validate(response.json())
    assert len(user_list_res.data) == 2
    assert any(user.id == platform_user.id for user in user_list_res.data)
    assert any(user.id == platform_user_2.id for user in user_list_res.data)
    # Check list users filtered disabled
    response = client.get(
        "/platform/users?disabled=true",
        headers=get_token(client=client, **superuser_login_data).to_headers(),
        params={"disabled": False},
    )
    response.raise_for_status()
    user_list_res = Pagination[User].model_validate(response.json())
    assert len(user_list_res.data) == 1
    assert any(user.id == platform_user.id for user in user_list_res.data)
    # Retrieve the updated platform user
    response = client.get(
        f"/platform/users/{platform_user_2.id}",
        headers=get_token(client=client, **platform_user_login_data).to_headers(),
    )
    response.raise_for_status()
    retrieved_updated_platform_user = User.model_validate(response.json())
    assert retrieved_updated_platform_user.email == platform_user_2.email
    assert retrieved_updated_platform_user.disabled is True
    assert retrieved_updated_platform_user.id == platform_user_2.id
    platform_user_2 = retrieved_updated_platform_user
