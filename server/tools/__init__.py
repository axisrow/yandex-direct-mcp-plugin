from dataclasses import dataclass


@dataclass
class ToolError:
    error: str
    message: str
    auth_url: str | None = None
