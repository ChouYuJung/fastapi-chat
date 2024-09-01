from typing import Dict, Text, Union

from fastapi.testclient import TestClient
from pydantic import BaseModel

from fastapi_chat.schemas.oauth import Token
from fastapi_chat.schemas.users import User


def login(
    client: TestClient,
    *,
    username: Text,
    password: Text,
) -> Token:
    login_data = {"username": username, "password": password}
    response = client.post("/auth/login", data=login_data)
    response.raise_for_status()

    token = Token.model_validate(response.json())
    return token


def get_headers(
    client: TestClient,
    auth: Union["Token", "LoginData", Dict[Text, Text]],
) -> Dict[Text, Text]:
    headers = {}
    if isinstance(auth, Token):
        headers = auth.to_headers()
    elif isinstance(auth, Dict):
        headers = auth
    elif isinstance(auth, LoginData):
        auth = login(client=client, **auth.model_dump())
        headers = auth.to_headers()
    return headers


def get_me(
    client: TestClient,
    auth: Union["Token", "LoginData", Dict[Text, Text]],
) -> "User":
    headers = {}
    if isinstance(auth, Token):
        headers = auth.to_headers()
    elif isinstance(auth, Dict):
        headers = auth
    elif isinstance(auth, LoginData):
        auth = login(client=client, **auth.model_dump())
        headers = auth.to_headers()

    user = User.model_validate(client.get("/me", headers=headers).json())
    assert user
    return user


class LoginData(BaseModel):
    username: Text
    password: Text
