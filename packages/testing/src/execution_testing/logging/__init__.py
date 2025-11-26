"""
Logging utilities for Ethereum Execution Specification Testing.

This module provides custom logging configuration with UTC timestamps,
custom log levels (VERBOSE, FAIL), and colored output support.
"""

from .logger import (
    FAIL_LEVEL,
    VERBOSE_LEVEL,
    ColorFormatter,
    EESTLogger,
    UTCFormatter,
    get_logger,
    LogLevel,
    configure_logging,
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
