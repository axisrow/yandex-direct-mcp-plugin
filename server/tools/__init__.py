from dataclasses import dataclass, asdict


@dataclass
class ToolError:
    error: str
    message: str
    auth_url: str | None = None

    def to_dict(self) -> dict:
        """Convert to dict, omitting None values."""
        d = asdict(self)
        return {k: v for k, v in d.items() if v is not None}
