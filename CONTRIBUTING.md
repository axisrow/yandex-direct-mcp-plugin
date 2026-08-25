# Contributing

Thank you for your interest in improving Yandex Direct MCP Plugin. We welcome
careful contributions from people who have installed and actually used the
project.

## No automated or drive-by contributions

This project does **not** accept automated, drive-by, or AI-generated
contributions from bots or people who have not installed and used the product.
Pull requests produced by bots that sweep repositories at scale will be closed
without review.

Before opening a pull request, you must:

1. Use Python 3.11 or newer and install the plugin with
   `pip install -e '.[dev]'`.
2. Configure authentication through a `direct-cli` auth profile.
3. Use the plugin with a real Yandex Direct account and verify your change in
   the live product.

AI assistance does not replace these requirements. The contributor submitting
the pull request is responsible for understanding, testing, and validating the
change.

## Pull request requirements

In the pull request description, explain exactly how you tested the change:

- list the commands you ran;
- describe the live workflow you exercised; and
- state what you observed on the real account.

Run the following checks before submitting:

```bash
ruff format .
ruff check .
mypy .
pytest
```

All checks must pass. Keep changes focused and follow the existing architecture
and typing conventions.

## Transport boundary

The plugin must **never** call the Yandex Direct API directly. All operations
must go through `direct-cli`. Direct API access through `urllib`, raw HTTP, or
`tapi-yandex-direct` is not accepted, including as a workaround.

If `direct-cli` does not support the required operation, open an upstream issue
in [axisrow/direct-cli](https://github.com/axisrow/direct-cli) and wait for CLI
support rather than bypassing the transport boundary.

## Safe live testing

Do not run mutating operations—add, update, delete, suspend, or resume—against a
live account without explicit maintainer consent. Test such changes with
cassettes or mocks. Without that consent, live verification must be read-only.
