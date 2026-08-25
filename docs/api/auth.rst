Authentication
==============

API authentication
------------------

Authentication for ordinary Yandex.Direct API tools is delegated to ``direct``
OAuth profiles. The MCP auth tools are thin wrappers around ``direct auth``
commands. Profiles are stored separately from browser sessions in
``~/.direct-cli/auth.json``.

Masters browser authentication
------------------------------

Campaign Wizard (Masters) has no Management API. Consequently,
``masters_get`` and ``masters_targetactions_get`` use a Playwright browser
session and are **not** authenticated by the API OAuth token, ``auth_login``,
``auth_setup``, ``YANDEX_DIRECT_TOKEN``, or ``YANDEX_DIRECT_LOGIN``.

Set up the recommended browser session manually from an interactive terminal,
outside the MCP stdio process::

   direct masters login

This command opens a visible Chromium window for a manual Yandex Passport
login and stores a CLI-owned persistent profile under
``~/.direct-cli/chrome-profile/``. It does not read the user's normal Chrome
profile or macOS Keychain. Run it as the same OS user, with the same ``HOME``,
that will run the MCP server. The ``direct-cli[browser]`` extra and Playwright
Chromium must be installed for the ``direct`` executable selected by the MCP
server. If a separate system CLI provides the browser extra, set
``YANDEX_DIRECT_CLI_PATH`` to that executable and restart the MCP client.

The login command requires a TTY, a visible GUI session, and human input. It
cannot be completed from an MCP tool call, a headless or remote process without
a GUI, CI, or an ephemeral sandbox. After setup, the read-only tools may run
headlessly provided the same persistent home directory and Playwright Chromium
are available.

Chrome cookie import (alternative)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``direct playwright login`` is a separate non-OAuth alternative. It imports
only Yandex cookies from an existing Chrome profile and saves a reusable
Playwright state at ``~/.direct-cli/playwright/session.json``. On macOS,
decrypting those cookies requires access to the ``Chrome Safe Storage`` key in
the login Keychain. ``direct playwright doctor`` checks this pipeline without
logging in or writing files.

When both stores exist, ``direct`` prefers the persistent profile created by
``direct masters login``. Both stores contain a live Yandex session and must be
protected as credentials. ``direct masters logout`` removes the CLI-owned
persistent profile. Masters commands always use the account logged in to the
browser session; API profile and ``YANDEX_DIRECT_LOGIN`` selection do not apply.

.. automodule:: server.tools.auth_tools
   :members:
