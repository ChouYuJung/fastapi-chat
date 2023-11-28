from typing import Annotated

from app.config import settings
from app.db.users import UserInDB, fake_users_db
from app.deps.oauth import get_current_active_user
from app.schemas.oauth import User
from app.utils.common import get_system_info
from app.utils.oauth import fake_hash_password, oauth2_scheme
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordRequestForm


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

    @app.post("/token")
    async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
        user_dict = fake_users_db.get(form_data.username)
        if not user_dict:
            raise HTTPException(
                status_code=400, detail="Incorrect username or password"
            )
        user = UserInDB(**user_dict)
        hashed_password = fake_hash_password(form_data.password)
        if not hashed_password == user.hashed_password:
            raise HTTPException(
                status_code=400, detail="Incorrect username or password"
            )

        return {"access_token": user.username, "token_type": "bearer"}

    @app.get("/users/me")
    async def read_users_me(
        current_user: Annotated[User, Depends(get_current_active_user)]
    ):
        return current_user

    return app


app = create_app()
