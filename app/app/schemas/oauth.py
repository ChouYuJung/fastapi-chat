from typing import Optional, Text

from pydantic import BaseModel, EmailStr, Field


def fake_decode_token(token):
    return User(
        username=token + "-fake-decoded",
        email="allen.c@example.com",
        organization="Example Inc.",
        team="Example Team",
        full_name="Allen C",
    )


class User(BaseModel):
    username: Text = Field(..., min_length=4, max_length=32, pattern="^[a-zA-Z0-9_-]+$")
    email: EmailStr
    organization: Text
    team: Text
    full_name: Optional[Text] = None
    disabled: bool = False
