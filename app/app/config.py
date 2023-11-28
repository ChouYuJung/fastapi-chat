from pydantic_settings import BaseSettings
from typing import Text


class Settings(BaseSettings):
    app_name: Text = "fastapi-app-service"
