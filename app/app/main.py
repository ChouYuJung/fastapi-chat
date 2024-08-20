import json
from datetime import timedelta
from typing import Annotated

from app.config import settings
from app.db.users import fake_users_db
from app.deps.oauth import get_current_active_user
from app.schemas.oauth import Token, User
from app.utils.common import get_system_info, is_json_serializable
from app.utils.oauth import authenticate_user, create_access_token, oauth2_scheme
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm


def create_app():
    app = FastAPI(title=settings.app_name.title(), version=settings.app_version)

    @app.get("/")
    async def root():
        return "OK"

    @app.get("/health")
    async def health():
        return {"status": "OK"}

    @app.get("/echo")
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

    @app.get("/stats")
    async def stats(token: Annotated[str, Depends(oauth2_scheme)]):
        return get_system_info()

    @app.post("/token", response_model=Token)
    async def login_for_access_token(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
    ):
        user = authenticate_user(fake_users_db, form_data.username, form_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}

    @app.get("/users/me")
    async def read_users_me(
        current_user: Annotated[User, Depends(get_current_active_user)]
    ):
        return current_user

    from .api.router import router as api_router

    app.include_router(api_router, prefix="/api")

    return app


app = create_app()
