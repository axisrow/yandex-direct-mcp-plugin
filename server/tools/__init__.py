<<<<<<< HEAD
from dataclasses import dataclass, asdict
=======
from dataclasses import dataclass
>>>>>>> origin/main


@dataclass
class ToolError:
    error: str
    message: str
    auth_url: str | None = None
<<<<<<< HEAD

    def to_dict(self) -> dict[str, str | None]:
        """Convert to dict, omitting None values."""
        d = asdict(self)
        return {k: v for k, v in d.items() if v is not None}
=======
>>>>>>> origin/main
