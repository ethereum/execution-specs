"""
Import the logging module content to make it available from
pytest_plugins.logging for backwards compatibility.

The core logging functionality has been moved to execution_testing.logging.
"""

from execution_testing.logging import (
    FAIL_LEVEL,
    VERBOSE_LEVEL,
    ColorFormatter,
    EESTLogger,
    LogLevel,
    UTCFormatter,
    configure_logging,
    get_logger,
)

__all__ = [
    "VERBOSE_LEVEL",
    "FAIL_LEVEL",
    "EESTLogger",
    "UTCFormatter",
    "ColorFormatter",
    "LogLevel",
    "get_logger",
    "configure_logging",
]
