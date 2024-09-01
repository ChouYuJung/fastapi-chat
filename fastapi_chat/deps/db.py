from typing import TYPE_CHECKING

from fastapi import Request

if TYPE_CHECKING:
    from fastapi_chat.db._base import DatabaseBase


def depend_db(request: Request) -> "DatabaseBase":
    return request.app.state.db
