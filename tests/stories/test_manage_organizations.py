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

from tests.utils import LoginData, get_token

fake = Faker()

superuser_login_data = LoginData(username="admin", password="pass1234")
platform_user_login_data = LoginData(
    username=fake.user_name(), password=fake.password()
)
org_1_user_login_data = LoginData(username=fake.user_name(), password=fake.password())
org_1_name = fake.company()
org_2_name = fake.company()


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
async def test_platform_manages_organizations(client: TestClient):
    platform_user = User.model_validate(
        client.get(
            "/auth/me",
            headers=get_token(
                client=client, **platform_user_login_data, cache=cache_tokens
            ).to_headers(),
        ).json()
    )
    assert platform_user

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
    created_org_1 = Organization.model_validate(response.json())
    org_2_create = OrganizationCreate.model_validate(
        {"name": org_2_name, "description": fake.text()}
    )
    response = client.post(
        "/organizations",
        json=org_2_create.model_dump(exclude_none=True),
        headers=get_token(
            client=client, **platform_user_login_data, cache=cache_tokens
        ).to_headers(),
    )
    response.raise_for_status()
    created_org_2 = Organization.model_validate(response.json())

    # Retrieve the created organizations
    response = client.get(
        f"/organizations/{created_org_1.id}",
        headers=get_token(
            client=client, **platform_user_login_data, cache=cache_tokens
        ).to_headers(),
    )
    response.raise_for_status()
    retrieved_org_1 = Organization.model_validate(response.json())
    assert created_org_1.id == retrieved_org_1.id
    response = client.get(
        f"/organizations/{created_org_2.id}",
        headers=get_token(
            client=client, **platform_user_login_data, cache=cache_tokens
        ).to_headers(),
    )
    response.raise_for_status()
    retrieved_org_2 = Organization.model_validate(response.json())
    assert created_org_2.id == retrieved_org_2.id

    # List organizations
    response = client.get(
        "/organizations",
        headers=get_token(
            client=client, **platform_user_login_data, cache=cache_tokens
        ).to_headers(),
    )
    response.raise_for_status()
    org_list_res = Pagination[Organization].model_validate(response.json())
    assert len(org_list_res.data) == 2

    # Update Organization 1
    org_1_update = OrganizationUpdate.model_validate({"description": fake.text()})
    response = client.put(
        f"/organizations/{created_org_1.id}",
        json=org_1_update.model_dump(exclude_none=True),
        headers=get_token(
            client=client, **platform_user_login_data, cache=cache_tokens
        ).to_headers(),
    )
    response.raise_for_status()
    updated_org_1 = Organization.model_validate(response.json())
    assert updated_org_1.description == org_1_update.description

    # Delete Organization 2
    response = client.delete(
        f"/organizations/{created_org_2.id}",
        headers=get_token(
            client=client, **platform_user_login_data, cache=cache_tokens
        ).to_headers(),
    )
    response.raise_for_status()
    # Platform user should be able to retrieve the deleted organization,
    # but org user should not
    response = client.get(
        f"/organizations/{created_org_2.id}",
        headers=get_token(
            client=client, **platform_user_login_data, cache=cache_tokens
        ).to_headers(),
    )
    response.raise_for_status()
    deleted_org_2 = Organization.model_validate(response.json())
    assert deleted_org_2.disabled is True

    # Recover Organization 2
    response = client.put(
        f"/organizations/{created_org_2.id}",
        json={"disabled": False},
        headers=get_token(
            client=client, **platform_user_login_data, cache=cache_tokens
        ).to_headers(),
    )
    response.raise_for_status()
    recovered_org_2 = Organization.model_validate(response.json())
    assert recovered_org_2.disabled is False
    assert recovered_org_2.id == created_org_2.id
