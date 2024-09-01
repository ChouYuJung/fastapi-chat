import json
from contextlib import asynccontextmanager
from typing import Any, Text

from fastapi import Depends, FastAPI, Request
from fastapi.routing import APIRoute
from rich.table import Table
from starlette.routing import Route as StarletteRoute

from .config import console, logger, settings
from .deps.oauth import DependsUserPermissions, TokenUserDepends, depends_active_user
from .schemas.permissions import Permission
from .schemas.users import User
from .utils.common import is_json_serializable, run_as_coro


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""

    print(f"Application '{settings.app_name}' is starting up.")

    # <SET_APP_STATE>
    # <SET_DB>
    from fastapi_chat.db._base import DatabaseBase

    _db = DatabaseBase.from_url(settings.DB_URL)
    logger.info(f"Connected to database: {_db}")
    await run_as_coro(_db.touch)
    set_app_state(app, key="db", value=_db)
    # </SET_DB>
    # </SET_APP_STATE>

    yield

    print(f"Application '{settings.app_name}' is shutting down.")


def create_app():
    app = FastAPI(
        title=settings.app_name.title(), version=settings.app_version, lifespan=lifespan
    )

    @app.get("/")
    async def root():
        return "OK"

    @app.get("/health")
    async def health():
        return {"status": "OK"}

    @app.get(
        "/echo",
        dependencies=[
            Depends(
                DependsUserPermissions(
                    [Permission.MANAGE_ALL_RESOURCES], "depends_active_user"
                )
            )
        ],
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

    @app.get("/me")
    async def api_me(
        token_payload_user: TokenUserDepends = Depends(depends_active_user),
    ) -> User:
        """Retrieve the current user."""

        return token_payload_user.user

    from .api._router import router as api_router

    app.include_router(api_router)

    pretty_print_routes(app)
    return app


def set_app_state(app: FastAPI, *, key: Text, value: Any):
    setattr(app.state, key, value)
    app.extra[key] = value


def pretty_print_routes(app: FastAPI):
    """Pretty print the FastAPI routes."""

    table = Table(title="FastAPI Routes")

    table.add_column("Methods", style="cyan")
    table.add_column("Path", style="magenta")
    table.add_column("Name", style="green")

    routes = sorted(
        app.routes,
        key=lambda x: (
            "HEAD" not in getattr(x, "methods", list()),
            getattr(x, "path", ""),
        ),
    )
    routes = [r for r in routes if isinstance(r, (APIRoute, StarletteRoute))]
    for route in routes:
        methods = (
            ", ".join(route.methods)
            if hasattr(route, "methods") and route.methods
            else "N/A"
        )
        path = route.path
        name = route.name
        table.add_row(methods, path, name)

    console.print(table)


app = create_app()
