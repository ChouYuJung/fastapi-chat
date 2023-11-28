from typing import Text

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: Text = "fastapi-app-service"
