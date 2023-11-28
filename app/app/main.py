from typing import Annotated

from app.config import settings
from app.deps.oauth import get_current_user
from app.schemas.oauth import User
from app.utils.common import get_system_info
from app.utils.oauth import oauth2_scheme
from fastapi import Depends, FastAPI


def create_app():
    app = FastAPI(title=settings.app_name.title(), version=settings.app_version)

    @app.get("/")
    async def root():
        return "OK"

    @app.get("/health")
    async def health():
        return {"status": "OK"}

    @app.get("/stats")
    async def stats(token: Annotated[str, Depends(oauth2_scheme)]):
        return get_system_info()

    @app.get("/users/me")
    async def read_users_me(current_user: Annotated[User, Depends(get_current_user)]):
        return current_user

    return app


app = create_app()
