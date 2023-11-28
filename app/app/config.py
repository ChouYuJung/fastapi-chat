from typing import Text

from pydantic_settings import BaseSettings

from .version import VERSION


class Settings(BaseSettings):
    app_name: Text = "fastapi-app-service"
    app_version: Text = VERSION

    token_url: Text = "token"


settings = Settings()
