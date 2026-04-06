from typing import TypedDict


class TokenData(TypedDict, total=False):
    access_token: str
    refresh_token: str
    expires_at: float
    scope: str
    login: str
