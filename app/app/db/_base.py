from typing import Text

from yarl import URL


class DatabaseBase:
    _url: URL | Text | None

    @classmethod
    def from_url(cls, url: URL | Text | None):
        from app.db._memory import DatabaseMemory

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
        _attr = ""
        if self.url_safe:
            _attr = f"url={self.url_safe}"
        return f"{self.__class__.__name__}({_attr})"
