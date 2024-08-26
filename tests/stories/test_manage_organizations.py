from typing import Dict, Text

import pytest
from app.schemas.oauth import Token, User
from app.schemas.pagination import Pagination
from faker import Faker
from fastapi.testclient import TestClient

from tests.utils import LoginData, get_token

fake = Faker()

superuser_login_data = LoginData(username="admin", password="pass1234")
platform_user_login_data = LoginData(
    username=fake.user_name(), password=fake.password()
)
org_user_login_data = LoginData(username=fake.user_name(), password=fake.password())

cache_tokens: Dict[Text, Token] = {}


@pytest.mark.asyncio
async def test_init_platform_status(client: TestClient):
    # Check initial database state
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
