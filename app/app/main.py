import json

from app.config import settings
from app.deps.oauth import RoleChecker
from app.schemas.oauth import Role
from app.utils.common import is_json_serializable
from fastapi import Depends, FastAPI, Request


def create_app():
    app = FastAPI(title=settings.app_name.title(), version=settings.app_version)

    @app.get("/")
    async def root():
        return "OK"

    @app.get("/health")
    async def health():
        return {"status": "OK"}

    @app.get(
        "/echo",
        dependencies=[Depends(RoleChecker([Role.ADMIN]))],
    )
    async def echo(request: Request):
        body = await request.body()
        return {
            "url": str(request.url),
            "method": request.method,
            "client": request.client.host if request.client else "",
            "query_params": dict(request.query_params),
            "body": json.loads(body) if is_json_serializable(body) else "",
            "headers": dict(request.headers),
            "cookies": request.cookies,
        }

    from .api._router import router as api_router

    app.include_router(api_router, prefix="/api")

    return app


app = create_app()
