from typing import Any, Dict, Text

from yarl import URL


class DatabaseBase:
    _url: URL | Text | None

    @classmethod
    def from_url(cls, url: URL | Text | None):
        db: DatabaseBase
        if url is None:
            db = DatabaseMemory()
        elif isinstance(url, Text) and url.strip() == "":
            db = DatabaseMemory()
        elif str(url).startswith("memory"):
            db = DatabaseMemory()
        else:
            db = DatabaseMemory()
        return db

    @property
    def url(self) -> URL | None:
        if hasattr(self, "_url"):
            if self._url is None:
                return None
            return URL(self._url)
        return None

    @property
    def url_safe(self) -> URL | None:
        url = self.url
        if url is not None:
            url = url.with_password("****")
        return url

    @property
    def client(self):
        raise NotImplementedError

    def touch(self):
        pass

    def __str__(self) -> Text:
        return f"{self.__class__.__name__}(url={self.url_safe})"


class DatabaseMemory(DatabaseBase):
    def __init__(self, *arg, **kwargs):
        self._url = None
        self._db = {}

    @property
    def client(self) -> Dict[Text, Any]:
        return self._db
