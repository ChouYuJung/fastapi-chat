from typing import Annotated

from app.utils.common import get_system_info
from app.utils.oauth import oauth2_scheme
from fastapi import Depends, FastAPI


def create_app():
    app = FastAPI()

    @app.get("/")
    async def root():
        return "OK"

    @app.get("/health")
    async def health():
        return {"status": "OK"}

    @app.get("/stats")
    async def stats(token: Annotated[str, Depends(oauth2_scheme)]):
        return get_system_info()

    return app


app = create_app()
