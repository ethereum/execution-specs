"""
Custom logger and configuration for use within `execution_testing`.
"""

import logging
import sys
from datetime import datetime, timezone
from logging import LogRecord
from pathlib import Path
from typing import Any, ClassVar, Optional, cast

VERBOSE_LEVEL = 15  # Between INFO (10) and DEBUG (20)
FAIL_LEVEL = 35  # Between WARNING (30) and ERROR (40)

# Add custom log levels to the logging module
logging.addLevelName(VERBOSE_LEVEL, "VERBOSE")
logging.addLevelName(FAIL_LEVEL, "FAIL")


class EESTLogger(logging.Logger):
    """Define custom log levels via a dedicated Logger class."""

    def verbose(
        self,
        msg: object,
        *args: Any,
        exc_info: BaseException | bool | None = None,
        stack_info: bool = False,
        stacklevel: int = 1,
        extra: Optional[dict[str, Any]] = None,
    ) -> None:
        """
        Log a message with VERBOSE level severity (15).

        This level is between DEBUG (10) and INFO (20), intended for messages
        more detailed than INFO but less verbose than DEBUG.
        """
        if stacklevel is None:
            stacklevel = 1
        if self.isEnabledFor(VERBOSE_LEVEL):
            self._log(
                VERBOSE_LEVEL,
                msg,
                args,
                exc_info,
                extra,
                stack_info,
                stacklevel,
            )

    def fail(
        self,
        msg: object,
        *args: Any,
        exc_info: BaseException | bool | None = None,
        stack_info: bool = False,
        stacklevel: int = 1,
        extra: Optional[dict[str, Any]] = None,
    ) -> None:
        """
        Log a message with FAIL level severity (35).

        This level is between WARNING (30) and ERROR (40), intended for test
        failures and similar issues.
        """
        if stacklevel is None:
            stacklevel = 1
        if self.isEnabledFor(FAIL_LEVEL):
            self._log(
                FAIL_LEVEL, msg, args, exc_info, extra, stack_info, stacklevel
            )


# Register the custom logger class
logging.setLoggerClass(EESTLogger)


def get_logger(name: str) -> EESTLogger:
    """Get a properly-typed logger with the EEST custom logging levels."""
    return cast(EESTLogger, logging.getLogger(name))


# Module logger
logger = get_logger(__name__)


class UTCFormatter(logging.Formatter):
    """
    Log formatter that formats UTC timestamps with milliseconds and +00:00
    suffix.
    """

    def formatTime(self, record: LogRecord, datefmt: str | None = None) -> str:  # noqa: D102,N802
        # camelcase required
        del datefmt

        dt = datetime.fromtimestamp(record.created, tz=timezone.utc)
        return dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] + "+00:00"


class ColorFormatter(UTCFormatter):
    """
    Formatter that adds ANSI color codes to log level names for terminal
    output.
    """

    running_in_docker: ClassVar[bool] = Path("/.dockerenv").exists()

    COLORS = {
        logging.DEBUG: "\033[37m",  # Gray
        VERBOSE_LEVEL: "\033[36m",  # Cyan
        logging.INFO: "\033[36m",  # Cyan
        logging.WARNING: "\033[33m",  # Yellow
        FAIL_LEVEL: "\033[35m",  # Magenta
        logging.ERROR: "\033[31m",  # Red
        logging.CRITICAL: "\033[41m",  # Red background
    }
    RESET = "\033[0m"

    def format(self, record: LogRecord) -> str:
        """Apply colorful formatting only when not running in Docker."""
        # First make a copy of the record to avoid modifying the original
        record_copy = logging.makeLogRecord(record.__dict__)
        if not self.running_in_docker:
            color = self.COLORS.get(record_copy.levelno, self.RESET)
            record_copy.levelname = (
                f"{color}{record_copy.levelname}{self.RESET}"
            )
        return super().format(record_copy)


class LogLevel:
    """Help parse a log-level provided on the command-line."""

    @classmethod
    def from_cli(cls, value: str) -> int:
        """
        Parse a logging level from CLI.

        Accepts standard level names (e.g. 'INFO', 'debug') or numeric values.
        """
        try:
            return int(value)
        except ValueError:
            pass

        level_name = value.upper()
        if level_name in logging._nameToLevel:
            return logging._nameToLevel[level_name]

        valid = ", ".join(logging._nameToLevel.keys())
        raise ValueError(
            f"Invalid log level '{value}'. Expected one of: {valid} or a number."
        )


# =========================================================================
# Standalone logging configuration (usable without pytest)
# =========================================================================


def configure_logging(
    log_level: int | str = "INFO",
    log_file: Optional[str | Path] = None,
    log_to_stdout: bool = True,
    log_format: str = "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    use_color: Optional[bool] = None,
) -> Optional[logging.FileHandler]:
    """
    Configure logging with EEST custom log levels and formatters.

    This function can be used in any Python project to set up logging with the
    same settings as the pytest plugin.

    Args:
      log_level: The logging level to use (name or numeric value)
      log_file: Path to the log file (if None, no file logging is set up)
      log_to_stdout: Whether to log to stdout
      log_format: The log format string
      use_color: Whether to use colors in stdout output (auto-detected if None)

    Returns: The file handler if log_file is provided, otherwise None

    """
    # Initialize root logger
    root_logger = logging.getLogger()

    # Convert log level if it's a string
    if isinstance(log_level, str):
        log_level = LogLevel.from_cli(log_level)

    # Set log level
    root_logger.setLevel(log_level)

    # Remove any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # File handler (optional)
    file_handler_instance = None
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(exist_ok=True, parents=True)

        file_handler_instance = logging.FileHandler(log_path, mode="w")
        file_handler_instance.setFormatter(UTCFormatter(fmt=log_format))
        root_logger.addHandler(file_handler_instance)

    # Stdout handler (optional)
    if log_to_stdout:
        stream_handler = logging.StreamHandler(sys.stdout)

        # Determine whether to use color
        if use_color is None:
            use_color = not ColorFormatter.running_in_docker

        if use_color:
            stream_handler.setFormatter(ColorFormatter(fmt=log_format))
        else:
            stream_handler.setFormatter(UTCFormatter(fmt=log_format))

        root_logger.addHandler(stream_handler)

    logger.verbose("Logging configured successfully.")
    return file_handler_instance
