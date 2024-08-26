from typing import Dict, Text

import pytest
from app.schemas.oauth import (
    Organization,
    OrganizationCreate,
    OrganizationUpdate,
    PlatformUserCreate,
    Token,
    User,
)
from app.schemas.pagination import Pagination
from faker import Faker
from fastapi.testclient import TestClient

from tests.utils import LoginData, auth_me, get_token

fake = Faker()

superuser_login_data = LoginData(username="admin", password="pass1234")
platform_user_login_data = LoginData(
    username=fake.user_name(), password=fake.password()
)
org_1_user_login_data = LoginData(username=fake.user_name(), password=fake.password())
org_1_name = fake.company()


cache_tokens: Dict[Text, Token] = {}


@pytest.mark.asyncio
async def test_init_platform_status(client: TestClient):
    # Check initial database state
    # Number of platform users should be 0
    response = client.get(
        "/platform/users",
        headers=get_token(
            client=client, **superuser_login_data, cache=cache_tokens
        ).to_headers(),
    )
    response.raise_for_status()
    user_list_res = Pagination[User].model_validate(response.json())
    assert len(user_list_res.data) == 0  # No platform users in the database
    # Superuser would not be in the list of platform users

    # Number of organizations should be 0
    response = client.get(
        "/organizations",
        headers=get_token(
            client=client, **superuser_login_data, cache=cache_tokens
        ).to_headers(),
    )
    response.raise_for_status()
    org_list_res = Pagination[Organization].model_validate(response.json())
    assert len(org_list_res.data) == 0


@pytest.mark.asyncio
async def test_create_platform_users(client: TestClient):
    # Create the first new platform user by superuser
    new_user_create = PlatformUserCreate.model_validate(
        {
            "username": platform_user_login_data["username"],
            "email": fake.safe_email(),
            "password": platform_user_login_data["password"],
            "full_name": fake.name(),
        }
    )
    response = client.post(
        "/platform/users",
        json=new_user_create.model_dump(exclude_none=True),
        headers=get_token(
            client=client, **superuser_login_data, cache=cache_tokens
        ).to_headers(),
    )
    response.raise_for_status()
    created_user = User.model_validate(response.json())

    # Retrieve the created user
    response = client.get(
        f"/platform/users/{created_user.id}",
        headers=get_token(
            client=client, **superuser_login_data, cache=cache_tokens
        ).to_headers(),
    )
    response.raise_for_status()
    retrieved_user = User.model_validate(response.json())
    assert created_user.id == retrieved_user.id


@pytest.mark.asyncio
async def test_platform_create_organizations(client: TestClient):
    assert await auth_me(client, platform_user_login_data, cache_tokens=cache_tokens)

    # Create Organization 1 and 2
    org_1_create = OrganizationCreate.model_validate(
        {"name": org_1_name, "description": fake.text()}
    )
    response = client.post(
        "/organizations",
        json=org_1_create.model_dump(exclude_none=True),
        headers=get_token(
            client=client, **platform_user_login_data, cache=cache_tokens
        ).to_headers(),
    )
    response.raise_for_status()
    assert Organization.model_validate(response.json())


@pytest.mark.asyncio
async def test_platform_get_organizations(client: TestClient):
    assert await auth_me(client, platform_user_login_data, cache_tokens=cache_tokens)

    # List organizations
    response = client.get(
        "/organizations",
        headers=get_token(
            client=client, **platform_user_login_data, cache=cache_tokens
        ).to_headers(),
    )
    response.raise_for_status()
    org_list_res = Pagination[Organization].model_validate(response.json())
    assert len(org_list_res.data) == 1
    org_1 = [org for org in org_list_res.data if org.name == org_1_name][0]

    # Retrieve the created organizations
    response = client.get(
        f"/organizations/{org_1.id}",
        headers=get_token(
            client=client, **platform_user_login_data, cache=cache_tokens
        ).to_headers(),
    )
    response.raise_for_status()
    retrieved_org_1 = Organization.model_validate(response.json())
    assert org_1.id == retrieved_org_1.id


@pytest.mark.asyncio
async def test_platform_update_organizations(client: TestClient):
    assert await auth_me(client, platform_user_login_data, cache_tokens=cache_tokens)

    org_1 = Organization.model_validate(
        client.get(
            "/organizations",
            headers=get_token(
                client=client, **platform_user_login_data, cache=cache_tokens
            ).to_headers(),
        ).json()["data"][0]
    )

    # Update Organization 1
    org_1_update = OrganizationUpdate.model_validate({"description": fake.text()})
    response = client.put(
        f"/organizations/{org_1.id}",
        json=org_1_update.model_dump(exclude_none=True),
        headers=get_token(
            client=client, **platform_user_login_data, cache=cache_tokens
        ).to_headers(),
    )
    response.raise_for_status()
    updated_org_1 = Organization.model_validate(response.json())
    assert updated_org_1.description == org_1_update.description


@pytest.mark.asyncio
async def test_platform_delete_organizations(client: TestClient):
    assert await auth_me(client, platform_user_login_data, cache_tokens=cache_tokens)

    org_1 = Organization.model_validate(
        client.get(
            "/organizations",
            headers=get_token(
                client=client, **platform_user_login_data, cache=cache_tokens
            ).to_headers(),
        ).json()["data"][0]
    )

    # Delete Organization 2
    response = client.delete(
        f"/organizations/{org_1.id}",
        headers=get_token(
            client=client, **platform_user_login_data, cache=cache_tokens
        ).to_headers(),
    )
    response.raise_for_status()
    # Platform user should be able to retrieve the deleted organization,
    # but org user should not
    response = client.get(
        f"/organizations/{org_1.id}",
        headers=get_token(
            client=client, **platform_user_login_data, cache=cache_tokens
        ).to_headers(),
    )
    response.raise_for_status()
    deleted_org_1 = Organization.model_validate(response.json())
    assert deleted_org_1.disabled is True

    # Recover Organization 2
    recovered_org_1 = Organization.model_validate(
        client.put(
            f"/organizations/{org_1.id}",
            json={"disabled": False},
            headers=get_token(
                client=client, **platform_user_login_data, cache=cache_tokens
            ).to_headers(),
        ).json()
    )
    assert recovered_org_1.disabled is False
