from typing import Text

from pydantic_settings import BaseSettings

from .version import VERSION


class Settings(BaseSettings):
    app_name: Text = "fastapi-app-service"
    app_version: Text = VERSION

    # OAuth2
    token_url: Text = "token"
    SECRET_KEY: Text = (
        "ce7ea672b396d1e36d1b64d725414bee9529a84c8a73ba32fd0eb57e7298a5fa"
    )
    ALGORITHM: Text = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30


settings = Settings()
