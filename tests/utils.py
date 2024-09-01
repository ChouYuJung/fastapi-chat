from typing import Dict, Optional, Text, TypedDict, Union

from fastapi.testclient import TestClient
from pydantic import BaseModel

from fastapi_chat.schemas.oauth import Token
from fastapi_chat.schemas.users import User

token_cache: Dict[Text, Token] = {}


def get_token(
    client: TestClient,
    *,
    username: Text,
    password: Text,
    reclaim: bool = False,
    cache: Optional[Dict[Text, Token]] = token_cache
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


async def get_headers(
    client: TestClient,
    auth: Union["Token", "LoginData", Dict[Text, Text]],
) -> Dict[Text, Text]:
    headers = {}
    if isinstance(auth, Token):
        headers = auth.to_headers()
    elif isinstance(auth, Dict):
        headers = auth
    elif isinstance(auth, LoginData):
        auth = get_token(client=client, **auth.model_dump())
        headers = auth.to_headers()
    return headers


async def get_me(
    client: TestClient,
    auth: Union["Token", "LoginData", Dict[Text, Text]],
) -> "User":
    headers = {}
    if isinstance(auth, Token):
        headers = auth.to_headers()
    elif isinstance(auth, Dict):
        headers = auth
    elif isinstance(auth, LoginData):
        auth = get_token(client=client, **auth.model_dump())
        headers = auth.to_headers()

    user = User.model_validate(client.get("/me", headers=headers).json())
    assert user
    return user


class LoginData(BaseModel):
    username: Text
    password: Text
