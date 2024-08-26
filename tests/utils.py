from typing import Dict, Text, TypedDict

from app.schemas.oauth import Token
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
