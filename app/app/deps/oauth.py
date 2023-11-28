from typing import Annotated

from app.utils.oauth import fake_decode_token, oauth2_scheme
from fastapi import Depends


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    user = fake_decode_token(token)
    return user
