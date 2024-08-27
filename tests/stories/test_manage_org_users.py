from typing import Dict, Text

import pytest
from app.schemas.oauth import (
    Organization,
    OrganizationCreate,
    PlatformUserCreate,
    Role,
    Token,
    User,
    UserCreate,
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
org_1_name = fake.company()
org_1_admin_login_data = LoginData(username=fake.user_name(), password=fake.password())
org_1_user_login_data = LoginData(username=fake.user_name(), password=fake.password())
org_2_name = fake.company()
org_2_admin_login_data = LoginData(username=fake.user_name(), password=fake.password())
org_2_user_login_data = LoginData(username=fake.user_name(), password=fake.password())


cache_tokens: Dict[Text, Token] = {}


@pytest.mark.asyncio
async def test_init_platform_status(client: TestClient):
    # Check db empty
    users_res = Pagination[User].model_validate(
        client.get(
            "/platform/users",
            headers=get_token(
                client=client, **superuser_login_data, cache=cache_tokens
            ).to_headers(),
        ).json()
    )
    assert len(users_res.data) == 0
    organizations_res = Pagination[Organization].model_validate(
        client.get(
            "/organizations",
            headers=get_token(
                client=client, **superuser_login_data, cache=cache_tokens
            ).to_headers(),
        ).json()
    )
    assert len(organizations_res.data) == 0

    # Create platform user
    new_user_create = PlatformUserCreate.model_validate(
        {
            "username": platform_user_login_data["username"],
            "email": fake.safe_email(),
            "password": platform_user_login_data["password"],
            "full_name": fake.name(),
            "role": Role.PLATFORM_ADMIN.value,
        }
    )
    platform_user = User.model_validate(
        client.post(
            "/platform/users",
            json=new_user_create.model_dump(exclude_none=True),
            headers=get_token(
                client=client, **superuser_login_data, cache=cache_tokens
            ).to_headers(),
        ).json()
    )
    assert platform_user.role == Role.PLATFORM_ADMIN

    # Create organizations
    new_org_1_create = OrganizationCreate.model_validate(
        {
            "name": org_1_name,
            "description": fake.text(),
        }
    )
    org_1 = Organization.model_validate(
        client.post(
            "/organizations",
            json=new_org_1_create.model_dump(exclude_none=True),
            headers=get_token(
                client=client, **platform_user_login_data, cache=cache_tokens
            ).to_headers(),
        ).json()
    )
    assert org_1.name == org_1_name
    new_org_2_create = OrganizationCreate.model_validate(
        {
            "name": org_2_name,
            "description": fake.text(),
        }
    )
    org_2 = Organization.model_validate(
        client.post(
            "/organizations",
            json=new_org_2_create.model_dump(exclude_none=True),
            headers=get_token(
                client=client, **platform_user_login_data, cache=cache_tokens
            ).to_headers(),
        ).json()
    )
    assert org_2.name == org_2_name

    # Create organization admins
    org_1_admin_create = UserCreate.model_validate(
        {
            "username": org_1_admin_login_data["username"],
            "email": fake.safe_email(),
            "password": org_1_admin_login_data["password"],
            "full_name": fake.name(),
            "role": Role.ORG_ADMIN.value,
        }
    )
    org_1_admin = User.model_validate(
        client.post(
            f"/organizations/{org_1.id}/users",
            json=org_1_admin_create.model_dump(exclude_none=True),
            headers=get_token(
                client=client, **platform_user_login_data, cache=cache_tokens
            ).to_headers(),
        ).json()
    )
    assert org_1_admin.role == Role.ORG_ADMIN
    org_2_admin_create = UserCreate.model_validate(
        {
            "username": org_2_admin_login_data["username"],
            "email": fake.safe_email(),
            "password": org_2_admin_login_data["password"],
            "full_name": fake.name(),
            "role": Role.ORG_ADMIN.value,
        }
    )
    org_2_admin = User.model_validate(
        client.post(
            f"/organizations/{org_2.id}/users",
            json=org_2_admin_create.model_dump(exclude_none=True),
            headers=get_token(
                client=client, **platform_user_login_data, cache=cache_tokens
            ).to_headers(),
        ).json()
    )
    assert org_2_admin.role == Role.ORG_ADMIN


@pytest.mark.asyncio
async def test_org_admin_create_users(client: TestClient):
    await auth_me(client, org_1_admin_login_data, cache_tokens=cache_tokens)
    await auth_me(client, org_2_admin_login_data, cache_tokens=cache_tokens)

    org_1 = Organization.model_validate(
        client.get(
            "/organizations/me",
            headers=get_token(
                client=client, **org_1_admin_login_data, cache=cache_tokens
            ).to_headers(),
        ).json()
    )
    org_1_user_create = UserCreate.model_validate(
        {
            "username": org_1_user_login_data["username"],
            "email": fake.safe_email(),
            "password": org_1_user_login_data["password"],
            "full_name": fake.name(),
            "role": Role.ORG_USER.value,
        }
    )
    user_1 = User.model_validate(
        client.post(
            f"/organizations/{org_1.id}/users",
            json=org_1_user_create.model_dump(exclude_none=True),
            headers=get_token(
                client=client, **org_1_admin_login_data, cache=cache_tokens
            ).to_headers(),
        ).json()
    )
    assert user_1

    org_2 = Organization.model_validate(
        client.get(
            "/organizations/me",
            headers=get_token(
                client=client, **org_2_admin_login_data, cache=cache_tokens
            ).to_headers(),
        ).json()
    )
    org_2_user_create = UserCreate.model_validate(
        {
            "username": org_2_user_login_data["username"],
            "email": fake.safe_email(),
            "password": org_2_user_login_data["password"],
            "full_name": fake.name(),
            "role": Role.ORG_USER.value,
        }
    )
    user_2 = User.model_validate(
        client.post(
            f"/organizations/{org_2.id}/users",
            json=org_2_user_create.model_dump(exclude_none=True),
            headers=get_token(
                client=client, **org_2_admin_login_data, cache=cache_tokens
            ).to_headers(),
        ).json()
    )
    assert user_2


@pytest.mark.asyncio
async def test_org_admin_managing_users(client: TestClient):
    pass


@pytest.mark.asyncio
async def test_org_users_operations(client: TestClient):
    pass


@pytest.mark.asyncio
async def test_platform_users_operations(client: TestClient):
    pass
