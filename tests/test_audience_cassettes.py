"""Cassette-based tests for the read-only audience_* tools (yac transport).

Cassettes here are subprocess-level (`yac` stdout/returncode), recorded by
this repo against the live Yandex Audience account (read-only calls only —
the recording script exercised segments/grants/pixels/accounts/delegates
list commands and nothing else). Mutating audience tools are mock-only by
design: no live mutating tests exist for the Audience transport.

Lifecycle (same as the Direct cassettes): record → sanitize → audit →
commit → replay. The recording for this file was one-shot; re-recording is
a manual step with the same /tmp harness pattern (CliRecorder.record).

In replay mode (default) the ``cli_recorder`` fixture patches
subprocess.run to return the saved cassette, so no token and no network
call occur — CI is safe. A missing cassette skips the test instead of
failing it.
"""

from __future__ import annotations

import pytest

from server.tools.audience_accounts import audience_accounts_list
from server.tools.audience_delegates import audience_delegates_list
from server.tools.audience_grants import audience_grants_list
from server.tools.audience_pixels import audience_pixels_list
from server.tools.audience_segments import audience_segments_list

# The grants cassette was recorded against this real segment; replay matches
# by full argv, so the id must stay in sync with tests/recordings/grants/.
GRANTS_SEGMENT_ID = "12834430"


def _run_cassette(fn, /, *args, **kwargs):
    """Call a tool, skipping the test if no cassette has been recorded yet."""
    result = fn(*args, **kwargs)
    if (
        isinstance(result, dict)
        and result.get("error") == "unknown"
        and "No cassette found" in str(result.get("message", ""))
    ):
        pytest.skip(f"No cassette recorded yet for {fn.__name__}")
    return result


class TestAudienceSegmentCassettes:
    def test_audience_segments_list(self, cli_recorder):
        result = _run_cassette(audience_segments_list)
        assert isinstance(result, dict)
        assert "segments" in result

    def test_audience_segments_list_pixel_filter(self, cli_recorder):
        result = _run_cassette(audience_segments_list, pixel=724143)
        assert isinstance(result, dict)


class TestAudienceGrantCassettes:
    def test_audience_grants_list(self, cli_recorder):
        result = _run_cassette(audience_grants_list, GRANTS_SEGMENT_ID)
        assert isinstance(result, dict)


class TestAudiencePixelCassettes:
    def test_audience_pixels_list(self, cli_recorder):
        result = _run_cassette(audience_pixels_list)
        assert isinstance(result, dict)
        assert "pixels" in result


class TestAudienceAccountCassettes:
    def test_audience_accounts_list(self, cli_recorder):
        result = _run_cassette(audience_accounts_list)
        assert isinstance(result, dict)


class TestAudienceDelegateCassettes:
    def test_audience_delegates_list(self, cli_recorder):
        result = _run_cassette(audience_delegates_list)
        assert isinstance(result, dict)
