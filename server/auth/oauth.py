class OAuthError(Exception):
    def __init__(self, error: str, message: str, auth_url: str | None = None):
        self.error = error
        self.message = message
        self.auth_url = auth_url
        super().__init__(message)
