from typing import Optional

from pydantic import BaseModel


class Token(BaseModel):
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_type: str
    mfa_required: bool = False
    mfa_token: Optional[str] = None


class TokenPayload(BaseModel):
    sub: Optional[str] = None
