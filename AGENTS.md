# Repository Guidelines

## Project Structure & Module Organization
Core code lives in `server/`. Use `server/main.py` as the MCP entrypoint, `server/tools/` for tool handlers (`campaigns.py`, `ads.py`, `keywords.py`, `reports.py`), `server/auth/` for OAuth/PKCE and token storage, and `server/cli/` for `direct-cli` execution. Tests live in `tests/`, with cassette fixtures under `tests/recordings/` and shared setup in `tests/conftest.py` and `tests/cli_recorder.py`. Documentation is in `docs/`, and skill definitions are in `skills/`.

## Build, Test, and Development Commands
Install dev dependencies with `pip install -e '.[dev]'`. Run the server locally with `python -m server.main`. Use `pytest` for the default cassette-replay suite, `pytest --record` to refresh cassettes from the live CLI, `pytest -m mocks` for subprocess edge cases, and `pytest -m integration` for live-token checks. Run `ruff check .`, `ruff format .`, and `mypy .` before opening a PR. For docs, use `make -C docs html`.

## Coding Style & Naming Conventions
Target Python 3.11+, 4-space indentation, and type annotations on public functions. Follow the current module naming style: lowercase snake_case files, descriptive test names like `test_auth.py`, and tool functions grouped by Yandex.Direct resource. Keep transport and auth concerns separated from tool logic. Use `ruff` for linting/formatting and `mypy` for type checks; prefer fixing root causes over adding ignores.

## Testing Guidelines
The default test flow replays JSON cassettes instead of calling the API. Record only when behavior changes: `pytest --record`. After recording, sanitize sensitive values with `python -m tests.sanitize`; audit recordings with `python -m tests.audit`. Mark pure mock tests with `@pytest.mark.mocks` and live-token tests with `@pytest.mark.integration`. Do not commit raw tokens, secrets, or unsanitized cassette output.

## Commit & Pull Request Guidelines
Recent history follows Conventional Commit style, for example `fix: ...`, `refactor(auth): ...`, and issue-linked subjects such as `(#40)`. Keep commits focused and imperative. PRs should describe user-visible behavior, note auth or cassette changes, link the issue when applicable, and include command results for `pytest`, `ruff`, and `mypy`. Add screenshots only when updating docs or plugin UX text that benefits from visual context.

## Security & Configuration Tips
Keep local secrets in `.env` or generated test files such as `.env.test`, and never commit them. OAuth tokens are stored under `CLAUDE_PLUGIN_DATA`; tests already isolate this path via `tmp_path`, so preserve that pattern in new tests.
