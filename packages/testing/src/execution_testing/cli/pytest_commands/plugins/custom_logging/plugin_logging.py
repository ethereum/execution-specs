"""
A Pytest plugin to configure logging for pytest sessions.

Note: While pytest's builtin logging is generally amazing, it does not write
timestamps when log output is written to pytest's caplog (the captured output
for a test). And having timestamps in this output is the main use case for
adding logging to our plugins. This output gets shown in the `FAILURES` summary
section, which is shown as the "simulator log" in hive simulations. For this
use case, timestamps are essential to verify timing issues against the clients
log.

This module provides the pytest plugin hooks that configure logging for
pytest sessions. The core logging functionality is in execution_testing.logging.
"""

import functools
import logging
import os
import sys
from datetime import datetime, timezone
from logging import LogRecord
from pathlib import Path
from typing import Any, Optional

import pytest
from _pytest.terminal import TerminalReporter

from execution_testing.logging import (
    FAIL_LEVEL,
    LogLevel,
    configure_logging,
    get_logger,
)

file_handler: Optional[logging.FileHandler] = None

# Module logger
logger = get_logger(__name__)

# ==========================================================================
# Pytest plugin integration
# ==========================================================================


def pytest_addoption(parser: pytest.Parser) -> None:  # noqa: D103
    logging_group = parser.getgroup(
        "logging", "Arguments related to logging from test fixtures and tests."
    )
    logging_group.addoption(
        "--eest-log-level",  # --log-level is defined by pytest's built-in
        # logging
        "--eestloglevel",
        action="store",
        default="INFO",
        type=LogLevel.from_cli,
        dest="eest_log_level",
        help=(
            "The logging level to use in the test session: DEBUG, INFO, WARNING, ERROR or "
            "CRITICAL, default - INFO. An integer in [0, 50] may be also provided."
        ),
    )
    logging_group.addoption(
        "--log-to",
        action="store",
        default=None,
        dest="eest_log_dir",
        help="Directory to write log files. Defaults to ./logs if not specified.",
    )


@functools.cache
def get_log_stem(argv0: str, argv1: Optional[str]) -> str:
    """Generate the stem (prefix-subcommand-timestamp) for log files."""
    stem = Path(argv0).stem
    prefix = "pytest" if stem in ("", "-c", "__main__") else stem
    subcommand = argv1 if argv1 and not argv1.startswith("-") else None
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")

    name_parts = [prefix]
    if subcommand:
        name_parts.append(subcommand)
    name_parts.append(timestamp)

    return "-".join(name_parts)


def pytest_configure_node(node: Any) -> None:
    """Initialize a variable for use in the worker (xdist hook)."""
    potential_subcommand = None
    if len(sys.argv) > 1:
        potential_subcommand = sys.argv[1]
    node.workerinput["log_stem"] = get_log_stem(
        sys.argv[0], potential_subcommand
    )


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config: pytest.Config) -> None:
    """
    Initialize logging for pytest sessions.

    This goes to a lot of effort to ensure that a log file is created per
    worker if xdist is used and that the timestamp used in the filename is the
    same across main and all workers.
    """
    global file_handler

    # Determine log file path with consistent timestamp across workers
    potential_subcommand = None
    if len(sys.argv) > 1:
        potential_subcommand = sys.argv[1]
    log_stem = getattr(config, "workerinput", {}).get(
        "log_stem"
    ) or get_log_stem(sys.argv[0], potential_subcommand)

    worker_id = os.getenv("PYTEST_XDIST_WORKER", "main")
    log_filename = f"{log_stem}-{worker_id}.log"
    log_dir = getattr(config.option, "eest_log_dir", None)
    base_logs_dir = Path("logs") if log_dir is None else Path(log_dir)
    base_logs_dir.mkdir(parents=True, exist_ok=True)
    log_file_path = base_logs_dir / log_filename

    # Store the log file path in the pytest config
    config.option.eest_log_file_path = log_file_path

    # Configure logging using the standalone function
    file_handler = configure_logging(
        log_level=config.getoption("eest_log_level"),
        log_file=log_file_path,
        log_to_stdout=True,
    )


def pytest_report_header(config: pytest.Config) -> list[str]:
    """Show the log file path in the test session header."""
    if eest_log_file_path := config.option.eest_log_file_path:
        return [f"Log file: {eest_log_file_path}"]
    return []


def pytest_terminal_summary(terminalreporter: TerminalReporter) -> None:
    """
    Display the log file path in the terminal summary like the HTML report
    does.
    """
    if terminalreporter.config.option.collectonly:
        return
    if eest_log_file_path := terminalreporter.config.option.eest_log_file_path:
        terminalreporter.write_sep(
            "-", f"Log file: {eest_log_file_path.resolve()}", yellow=True
        )


def log_only_to_file(level: int, msg: str, *args: Any) -> None:
    """Log a message only to the file handler, bypassing stdout."""
    if not file_handler:
        return
    handler: logging.Handler = file_handler
    logger = logging.getLogger(__name__)
    if not logger.isEnabledFor(level):
        return
    record: LogRecord = logger.makeRecord(
        logger.name,
        level,
        fn=__file__,
        lno=0,
        msg=msg,
        args=args,
        exc_info=None,
        func=None,
        extra=None,
    )
    handler.handle(record)


def pytest_runtest_logstart(
    nodeid: str, location: tuple[str, int, str]
) -> None:
    """Log test start to file."""
    del location

    log_only_to_file(logging.INFO, f"ℹ️  - START TEST: {nodeid}")


def pytest_runtest_logreport(report: pytest.TestReport) -> None:
    """Log test status and duration to file after it runs."""
    if report.when != "call":
        return

    nodeid = report.nodeid
    duration = report.duration

    log_level = logging.INFO
    if hasattr(report, "wasxfail"):
        if report.skipped:
            status = "XFAIL"
            emoji = "💤"
        elif report.passed:
            status = "XPASS"
            emoji = "🚨"
        else:
            status = "XFAIL ERROR"
            emoji = "💣"
            log_level = logging.ERROR
    elif report.skipped:
        status = "SKIPPED"
        emoji = "⏭️"
    elif report.failed:
        status = "FAILED"
        emoji = "❌"
        log_level = FAIL_LEVEL
    else:
        status = "PASSED"
        emoji = "✅"

    log_only_to_file(
        log_level, f"{emoji} - {status} in {duration:.2f}s: {nodeid}"
    )


def pytest_runtest_logfinish(
    nodeid: str, location: tuple[str, int, str]
) -> None:
    """Log end of test to file."""
    del location

    log_only_to_file(logging.INFO, f"ℹ️  - END TEST: {nodeid}")
