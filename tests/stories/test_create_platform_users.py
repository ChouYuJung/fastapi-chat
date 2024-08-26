import pytest
from fastapi.testclient import TestClient


@pytest.mark.asyncio
async def test_create_platform_users(client: TestClient):
    res = client.get("/")
    print(res)
    print(res.text)
