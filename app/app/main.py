from app.utils.common import get_system_info
from fastapi import FastAPI


def create_app():
    app = FastAPI()

    @app.get("/")
    async def root():
        return "OK"

    @app.get("/health")
    async def health():
        return {"status": "OK"}

    @app.get("/stats")
    async def stats():
        return get_system_info()

    return app


app = create_app()
