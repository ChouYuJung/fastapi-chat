from typing import Dict, Text, TypedDict

import pytest
from app.schemas.oauth import Role, Token, User, UserCreate
from fastapi.testclient import TestClient

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

    # Create a new platform user
    new_user_create = UserCreate.model_validate(
        {
            "username": "platform_admin",
            "email": "platform_admin@example.com",
            "password": "pass1234",
            "full_name": "Platform Admin",
            "role": Role.PLATFORM_ADMIN.value,
        }
    )
    response = client.post(
        "/platform/users",
        json=new_user_create.model_dump(exclude_none=True),
        headers=get_token(
            client=client,
            **superuser_login_data,
        ).to_headers(),
    )
    response.raise_for_status()
    platform_user = User.model_validate(response.json())
    assert platform_user.role == Role.PLATFORM_ADMIN
    assert platform_user.organization_id is None
    assert platform_user.disabled is False
