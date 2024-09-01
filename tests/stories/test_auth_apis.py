from typing import Dict, Text

import httpx
import pytest
from faker import Faker
from fastapi.testclient import TestClient

from fastapi_chat.schemas.oauth import Token
from fastapi_chat.schemas.pagination import Pagination
from fastapi_chat.schemas.roles import Role
from fastapi_chat.schemas.users import User, UserCreate, UserUpdate
from tests.utils import LoginData, auth_me, get_token

fake = Faker()

superuser_login_data = LoginData(username="admin", password="pass1234")


@pytest.mark.asyncio
async def test_init_platform_status(client: TestClient):

    print(client.app.routes)
    # # Check initial database state
    # response = client.get(
    #     "/platform/users",
    #     headers=get_token(
    #         client=client, **superuser_login_data, cache=cache_tokens
    #     ).to_headers(),
    # )
    # response.raise_for_status()
    # user_list_res = Pagination[User].model_validate(response.json())
    # assert len(user_list_res.data) == 0  # No platform users in the database
    # # Superuser would not be in the list of platform users
