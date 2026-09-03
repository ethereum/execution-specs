"""
Terminal reporting for the ``frame_tx`` fixture-format variants.

Every state test also fills as a ``frame_tx`` variant — the same test
with its transaction rewritten as an EIP-8141 frame transaction (see
`execution_testing.specs.frame_transaction_variant`). Variants whose
transaction cannot be rewritten skip at fill time; the hooks below
keep those skips out of the per-test output and print one grouped
breakdown instead.
"""

from typing import Any

import pytest
from _pytest.terminal import TerminalReporter

from execution_testing.specs.frame_transaction_variant import (
    FRAME_SKIP_CATEGORY,
)


@pytest.hookimpl(tryfirst=True)
def pytest_report_teststatus(
    report: Any, config: pytest.Config
) -> tuple[str, str, str] | None:
    """
    Report unconvertible frame variants under their own category with
    no progress character, keeping fill output free of skip noise.

    ``tryfirst`` is required to beat ``pytest-custom-report``, whose
    ``pytest_report_teststatus`` claims every skipped report.
    """
    fixture_output = getattr(config, "fixture_output", None)
    if fixture_output is not None and fixture_output.is_stdout:
        return None
    if getattr(report, "skipped", False):
        longrepr = getattr(report, "longrepr", None)
        if isinstance(longrepr, tuple) and FRAME_SKIP_CATEGORY in longrepr[2]:
            return FRAME_SKIP_CATEGORY, "", FRAME_SKIP_CATEGORY.upper()
    return None


def pytest_terminal_summary(
    terminalreporter: TerminalReporter,
    exitstatus: int,
    config: pytest.Config,
) -> None:
    """
    Print one grouped breakdown of the frame variants that were not
    generated, in place of per-test skip lines.
    """
    del exitstatus, config
    reports = terminalreporter.stats.get(FRAME_SKIP_CATEGORY, [])
    if not reports:
        return
    reasons: dict[str, int] = {}
    for report in reports:
        reason = report.longrepr[2].split(f"{FRAME_SKIP_CATEGORY}: ")[-1]
        reasons[reason] = reasons.get(reason, 0) + 1
    terminalreporter.write_sep("-", "frame variants not generated")
    for reason, count in sorted(
        reasons.items(), key=lambda item: item[1], reverse=True
    ):
        terminalreporter.write_line(f"{count:>6}  {reason}")
