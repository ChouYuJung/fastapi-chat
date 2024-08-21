from typing import Generic, List, Literal, Text, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class Pagination(BaseModel, Generic[T]):
    object: Literal["list"] = Field(default="list")
    data: List[T]
    first_id: Text | None = Field(default=None)
    last_id: Text | None = Field(default=None)
    has_more: bool = Field(default=False)
