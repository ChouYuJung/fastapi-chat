from typing import TYPE_CHECKING

import pytest
from faker import Faker
from fastapi.testclient import TestClient

from fastapi_chat.main import app

if TYPE_CHECKING:
    from tests.utils import LoginData


fake = Faker()


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def user_super_admin() -> "LoginData":
    from tests.utils import LoginData

    return LoginData(username="admin", password="pass1234")


@pytest.fixture(scope="module")
def user_platform_admin() -> "LoginData":
    from tests.utils import LoginData

    return LoginData(username=fake.user_name(), password=fake.password())


@pytest.fixture(scope="module")
def user_platform_editor() -> "LoginData":
    from tests.utils import LoginData

    return LoginData(username=fake.user_name(), password=fake.password())


@pytest.fixture(scope="module")
def user_platform_viewer() -> "LoginData":
    from tests.utils import LoginData

    return LoginData(username=fake.user_name(), password=fake.password())


@pytest.fixture(scope="module")
def user_org_admin() -> "LoginData":
    from tests.utils import LoginData

    return LoginData(username=fake.user_name(), password=fake.password())


@pytest.fixture(scope="module")
def user_org_editor() -> "LoginData":
    from tests.utils import LoginData

    return LoginData(username=fake.user_name(), password=fake.password())


@pytest.fixture(scope="module")
def user_org_viewer() -> "LoginData":
    from tests.utils import LoginData

    return LoginData(username=fake.user_name(), password=fake.password())


@pytest.fixture(scope="module")
def user_org_client() -> "LoginData":
    from tests.utils import LoginData

    return LoginData(username=fake.user_name(), password=fake.password())


@pytest.fixture(scope="module")
def user_prisoner() -> "LoginData":
    from tests.utils import LoginData

    return LoginData(username=fake.user_name(), password=fake.password())
