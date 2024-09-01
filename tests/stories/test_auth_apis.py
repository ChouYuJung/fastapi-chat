import httpx
import pytest
from fastapi.testclient import TestClient

from fastapi_chat.schemas.roles import Role
from tests.utils import LoginData, get_me, login

super_admin_login_data = LoginData(username="admin", password="pass1234")


@pytest.mark.asyncio
async def test_login(client: TestClient):
    login_data = super_admin_login_data
    token = login(client, **login_data.model_dump())
    assert token.access_token is not None
    assert token.refresh_token is not None
    assert token.token_type == "bearer"


@pytest.mark.asyncio
async def test_user_me(client: TestClient):
    me = await get_me(client, super_admin_login_data)
    assert me.username == super_admin_login_data.username
    assert me.organization_id is None
    assert me.role == Role.SUPER_ADMIN


@pytest.mark.asyncio
async def test_refresh_token(client: TestClient):
    token = login(client, **super_admin_login_data.model_dump())
    response = client.post(
        "/auth/refresh-token",
        json={"grant_type": "refresh_token", "refresh_token": token.refresh_token},
    )
    response.raise_for_status()

    with pytest.raises(httpx.HTTPStatusError):
        response = client.get("/me", headers=token.to_headers())
        response.raise_for_status()


@pytest.mark.asyncio
async def test_logout(client: TestClient):
    token = login(client, **super_admin_login_data.model_dump())
    response = client.post("/auth/logout", headers=token.to_headers())
    response.raise_for_status()

    # Ensure the token is invalidated
    with pytest.raises(httpx.HTTPStatusError):
        response = client.get("/users/me", headers=token.to_headers())
        response.raise_for_status()
