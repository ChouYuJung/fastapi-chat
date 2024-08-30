import hashlib
import json
import time
from typing import Annotated, Dict, Literal, Optional, Required, Text, TypedDict

from pydantic import BaseModel, ConfigDict, Field


class Token(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    access_token: Text
    refresh_token: Text
    token_type: Literal["bearer"] | Text
    expires_at: int

    @classmethod
    def from_bearer_token(
        cls, access_token: Text, refresh_token: Text, expires_at: int
    ) -> "Token":
        return cls.model_validate(
            {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_at": expires_at,
            }
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return self.md5() == other.md5()

    def md5(self) -> Text:
        return hashlib.md5(
            json.dumps(self.model_dump(), sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()

    def to_db_model(self, *, username: Text) -> "TokenInDB":
        token_data = self.model_dump()
        token_data["username"] = username
        return TokenInDB.model_validate(token_data)

    def to_headers(self) -> Dict[Text, Text]:
        return {"Authorization": f"Bearer {self.access_token}"}


class TokenInDB(Token):
    model_config = ConfigDict(str_strip_whitespace=True)
    username: Text


class TokenBlacklisted(BaseModel):
    token: Text
    created_at: int = Field(default_factory=lambda: int(time.time()))


class RefreshTokenRequest(BaseModel):
    grant_type: Literal["refresh_token"] = Field(...)
    refresh_token: Text = Field(...)
    client_id: Optional[Text] = Field(default=None)
    client_secret: Optional[Text] = Field(default=None)


class TokenData(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    username: Text
    user_id: Text
    organization_id: Optional[Text] = Field(default=None)

    @classmethod
    def from_payload(cls, payload: Dict) -> "TokenData":
        return TokenData.model_validate({"username": payload.get("sub")})


class PayloadParam(TypedDict, total=False):
    sub: Required[Annotated[Text, "subject or username"]]
    exp: Required[Annotated[int, "expiration time in seconds"]]
