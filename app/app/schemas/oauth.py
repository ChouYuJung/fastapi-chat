from typing import Optional, Text

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class Token(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    access_token: Text
    token_type: Text


class TokenData(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    username: Optional[Text] = None


class User(
    BaseModel,
):
    model_config = ConfigDict(str_strip_whitespace=True)

    username: Text = Field(..., min_length=4, max_length=32, pattern="^[a-zA-Z0-9_-]+$")
    email: EmailStr
    full_name: Optional[Text] = None
    disabled: bool = False


class UserInDB(User):
    hashed_password: Text
