class OAuthError(Exception):
    def __init__(self, error: str, message: str, auth_url: str | None = None):
        self.error = error
        self.message = message
        self.auth_url = auth_url

    def to_dict(self) -> dict:
        r: dict = {"error": self.error, "message": self.message}
        if self.auth_url:
            r["auth_url"] = self.auth_url
        return r


class OAuthManager:
    def get_valid_token(self) -> str:
        raise NotImplementedError("OAuth not implemented in this unit")
