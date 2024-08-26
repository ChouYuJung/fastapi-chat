from typing import Dict, Optional, Text, TypedDict

from app.schemas.oauth import Token
from fastapi.testclient import TestClient


def get_token(
    client: TestClient,
    *,
    username: Text,
    password: Text,
    reclaim: bool = False,
    cache: Optional[Dict[Text, Token]] = None
) -> Token:

    if cache is not None and username in cache and not reclaim:
        return cache[username]

    login_data = {"username": username, "password": password}
    response = client.post("/auth/login", data=login_data)
    response.raise_for_status()

    token = Token.model_validate(response.json())

    if cache is not None:
        cache[username] = token
    return token


class LoginData(TypedDict):
    username: Text
    password: Text
