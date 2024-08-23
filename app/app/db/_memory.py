from typing import Any, Dict, Text

from app.db._base import DatabaseBase


class DatabaseMemory(DatabaseBase):
    def __init__(self, *arg, **kwargs):
        self._url = None
        self._db = {}

    @property
    def client(self) -> Dict[Text, Any]:
        return self._db
