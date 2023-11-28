from app.config import settings
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=settings.token_url)


def fake_decode_token(token):
    from app.schemas.oauth import User

    return User(
        username=token + "-fake-decoded",
        email="allen.c@example.com",
        organization="Example Inc.",
        team="Example Team",
        full_name="Allen C",
    )
