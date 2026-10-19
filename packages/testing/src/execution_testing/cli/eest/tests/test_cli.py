"""Tests for the `eest` CLI group."""

import io
import sys

import pytest
from click.testing import CliRunner

from ..cli import eest, ensure_utf8_output

pytestmark = pytest.mark.skip(
    "Issue #3241: eest info queries github.com to get release information"
)


def test_info_runs_successfully() -> None:
    """`eest info` exits cleanly and reports the EEST banner."""
    result = CliRunner().invoke(eest, ["info"])
    assert result.exit_code == 0
    assert "EEST" in result.output


def test_info_survives_legacy_console_encoding(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    `eest info` must not crash on a non-UTF-8 console code page.

    Regression test for the Windows `cp1252` console, whose codec
    cannot encode the box-drawing characters printed by the command.
    """
    stream = io.TextIOWrapper(io.BytesIO(), encoding="cp1252")
    monkeypatch.setattr(sys, "stdout", stream)

    # Without the UTF-8 reconfiguration this raises UnicodeEncodeError.
    eest.main(["info"], standalone_mode=False)

    stream.flush()
    assert "EEST" in stream.buffer.getvalue().decode("utf-8")


def test_ensure_utf8_output_reconfigures_stream(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`ensure_utf8_output` switches a legacy stream to UTF-8."""
    stream = io.TextIOWrapper(io.BytesIO(), encoding="cp1252")
    monkeypatch.setattr(sys, "stdout", stream)

    ensure_utf8_output()

    assert stream.encoding.lower() == "utf-8"
