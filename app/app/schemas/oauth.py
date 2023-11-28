from typing import Optional, Text

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# Strip any space
class User(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    username: Text = Field(..., min_length=4, max_length=32, pattern="^[a-zA-Z0-9_-]+$")
    email: EmailStr
    organization: Text
    team: Text
    full_name: Optional[Text] = None
    disabled: bool = False
