from collections.abc import Callable
from dataclasses import dataclass
from functools import wraps

from server.cli.runner import CliAuthError, CliNotFoundError, CliTimeoutError


@dataclass
class ToolError:
    error: str
    message: str
    auth_url: str | None = None


def _try_refresh_token() -> str | None:
    """Force-refresh the OAuth token. Returns new access token or None."""
    try:
        from server.auth.oauth import OAuthError, OAuthManager

        manager = OAuthManager()
        data = manager.refresh_token()
        return data["access_token"]
    except OAuthError:
        raise
    except Exception:
        return None


def handle_cli_errors(func):
    """Decorator that catches CLI errors and returns ToolError dicts.

    On 401, refreshes token and retries once."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except CliAuthError:
            from server.auth.oauth import OAuthError

            try:
                new_token = _try_refresh_token()
            except OAuthError as e:
                return e.to_dict()
            if new_token is not None:
                try:
                    return func(*args, **kwargs)
                except CliAuthError:
                    pass
            return ToolError(
                error="auth_expired",
                message="Token expired. Re-authorization required.",
            ).__dict__
        except CliNotFoundError as e:
            return ToolError(error="cli_not_found", message=str(e)).__dict__
        except CliTimeoutError as e:
            return ToolError(error="timeout", message=str(e)).__dict__
        except Exception as e:
            return ToolError(error="unknown", message=str(e)).__dict__

    return wrapper


_token_getter: Callable[[], str] | None = None


def set_token_getter(getter: Callable[[], str]) -> None:
    global _token_getter
    _token_getter = getter


def get_runner():
    """Create a DirectCliRunner using the configured token getter."""
    from server.cli.runner import DirectCliRunner

    if _token_getter is None:
        raise RuntimeError("Token getter not configured")
    return DirectCliRunner(token=_token_getter())
