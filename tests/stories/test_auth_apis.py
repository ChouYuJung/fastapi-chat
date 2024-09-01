from typing import Dict, Text

import httpx
import pytest
from faker import Faker
from fastapi.testclient import TestClient

from fastapi_chat.schemas.oauth import Token
from fastapi_chat.schemas.pagination import Pagination
from fastapi_chat.schemas.roles import Role
from fastapi_chat.schemas.users import User, UserCreate, UserUpdate
from tests.utils import LoginData, get_me, get_token

super_admin_login_data = LoginData(username="admin", password="pass1234")


@pytest.mark.asyncio
async def test_user_me(client: TestClient):
    me = await get_me(client, super_admin_login_data)
    assert me.username == super_admin_login_data.username
    assert me.organization_id is None
    assert me.role == Role.SUPER_ADMIN
