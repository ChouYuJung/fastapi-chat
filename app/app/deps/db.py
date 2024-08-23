from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.db._base import DatabaseBase
    from fastapi import FastAPI


def depend_db(app: "FastAPI") -> "DatabaseBase":
    return app.state.db
