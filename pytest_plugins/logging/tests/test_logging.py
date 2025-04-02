"""
Tests for the logging module.

These tests verify the functionality of the custom logging system,
including both the standalone configuration and the pytest integration.
"""

import io
import logging
import re
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from ..logging import (
    FAIL_LEVEL,
    VERBOSE_LEVEL,
    ColorFormatter,
    EESTLogger,
    UTCFormatter,
    configure_logging,
    get_logger,
)


class TestLoggerSetup:
    """Test the basic setup of loggers and custom levels."""

    def test_custom_levels_registered(self):
        """Test that custom log levels are properly registered."""
        assert logging.getLevelName(VERBOSE_LEVEL) == "VERBOSE"
        assert logging.getLevelName(FAIL_LEVEL) == "FAIL"
        assert logging.getLevelName("VERBOSE") == VERBOSE_LEVEL
        assert logging.getLevelName("FAIL") == FAIL_LEVEL

    def test_get_logger(self):
        """Test that get_logger returns a properly typed logger."""
        logger = get_logger("test_logger")
        assert isinstance(logger, EESTLogger)
        assert logger.name == "test_logger"
        assert hasattr(logger, "verbose")
        assert hasattr(logger, "fail")


class TestEESTLogger:
    """Test the custom logger methods."""

    def setup_method(self):
        """Set up a logger and string stream for capturing log output."""
        self.log_output = io.StringIO()
        self.logger = get_logger("test_eest_logger")

        # Remove any existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)

        # Configure a basic handler that writes to our string stream
        handler = logging.StreamHandler(self.log_output)
        handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.DEBUG)  # Set to lowest possible level for testing

    def test_verbose_method(self):
        """Test the verbose() method logs at the expected level."""
        self.logger.verbose("This is a verbose message")
        assert "VERBOSE: This is a verbose message" in self.log_output.getvalue()

    def test_fail_method(self):
        """Test the fail() method logs at the expected level."""
        self.logger.fail("This is a fail message")
        assert "FAIL: This is a fail message" in self.log_output.getvalue()

    def test_standard_methods(self):
        """Test that standard log methods still work."""
        self.logger.debug("Debug message")
        self.logger.info("Info message")
        self.logger.warning("Warning message")

        log_output = self.log_output.getvalue()
        assert "DEBUG: Debug message" in log_output
        assert "INFO: Info message" in log_output
        assert "WARNING: Warning message" in log_output


class TestFormatters:
    """Test the custom log formatters."""

    def test_utc_formatter(self):
        """Test that UTCFormatter formats timestamps correctly."""
        formatter = UTCFormatter(fmt="%(asctime)s: %(message)s")
        record = logging.makeLogRecord(
            {
                "msg": "Test message",
                "created": 1609459200.0,  # 2021-01-01 00:00:00 UTC
            }
        )

        formatted = formatter.format(record)
        assert re.match(r"2021-01-01 00:00:00\.\d{3}\+00:00: Test message", formatted)

    def test_color_formatter(self, monkeypatch):
        """Test that ColorFormatter adds color codes to the log level."""
        # Create the formatter and test record
        formatter = ColorFormatter(fmt="[%(levelname)s] %(message)s")
        record = logging.makeLogRecord(
            {
                "levelno": logging.ERROR,
                "levelname": "ERROR",
                "msg": "Error message",
            }
        )

        # Test case 1: When not running in Docker, colors should be applied
        # Override the class variable directly with monkeypatch
        monkeypatch.setattr(ColorFormatter, "running_in_docker", False)
        formatted = formatter.format(record)
        assert "\033[31mERROR\033[0m" in formatted  # Red color for ERROR

        # Test case 2: When running in Docker, colors should not be applied
        monkeypatch.setattr(ColorFormatter, "running_in_docker", True)
        formatted = formatter.format(record)
        assert "\033[31mERROR\033[0m" not in formatted
        assert "ERROR" in formatted


class TestStandaloneConfiguration:
    """Test the standalone logging configuration function."""

    def test_configure_logging_defaults(self):
        """Test configure_logging with default parameters."""
        with patch("sys.stdout", new=io.StringIO()):
            # Configure logging with default settings
            handler = configure_logging()

            # Should log to stdout by default
            root_logger = logging.getLogger()
            assert any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers)

            # Should set INFO level by default
            assert root_logger.level == logging.INFO

            # Should not return a file handler
            assert handler is None

    def test_configure_logging_with_file(self):
        """Test configure_logging with file output."""
        # Create a temporary directory for log files
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"

            # Configure logging with a file
            handler = configure_logging(log_file=log_file, log_to_stdout=False)

            try:
                # Should return a file handler
                assert isinstance(handler, logging.FileHandler)

                # Should create the log file
                assert log_file.exists()

                # Log a message and check it appears in the file
                logger = get_logger("test_config")
                logger.info("Test log message")

                with open(log_file, "r") as f:
                    log_content = f.read()
                    assert "Test log message" in log_content
            finally:
                # Clean up
                if handler:
                    handler.close()
                logging.getLogger().handlers = []  # Remove all handlers

    def test_configure_logging_with_level(self):
        """Test configure_logging with custom log level."""
        # Test with string level name
        configure_logging(log_level="DEBUG", log_to_stdout=False)
        assert logging.getLogger().level == logging.DEBUG

        # Test with numeric level
        configure_logging(log_level=VERBOSE_LEVEL, log_to_stdout=False)
        assert logging.getLogger().level == VERBOSE_LEVEL

        # Clean up
        logging.getLogger().handlers = []


# Only the TestPytestIntegration class tests require pytest to run properly
# We'll put the skip marker on that class instead of the whole module


class TestPytestIntegration:
    """Test the pytest integration of the logging module."""

    def test_pytest_configure(self, monkeypatch, tmpdir):
        """Test that pytest_configure sets up logging correctly."""
        from pytest_plugins.logging.logging import pytest_configure

        # Create logs directory if it doesn't exist
        log_dir = Path("logs")
        if not log_dir.exists():
            log_dir.mkdir()

        # Save the original handlers to restore later
        original_handlers = logging.getLogger().handlers.copy()

        try:
            # Remove existing handlers to start clean
            for handler in logging.getLogger().handlers[:]:
                logging.getLogger().removeHandler(handler)

            # Create a mock pytest config
            class MockConfig:
                def __init__(self):
                    self.option = MagicMock()
                    self.option.eest_log_level = logging.INFO
                    self.workerinput = {}

                def getoption(self, name):
                    if name == "eest_log_level":
                        return logging.INFO

            # Set up environment
            monkeypatch.setattr("sys.argv", ["pytest"])
            monkeypatch.setenv("PYTEST_XDIST_WORKER", "worker1")

            # Call pytest_configure
            config = MockConfig()
            pytest_configure(config)

            # Check that logging is configured
            assert hasattr(config.option, "eest_log_file_path")

            # Check that a file handler was added to the root logger
            file_handlers = [
                h for h in logging.getLogger().handlers if isinstance(h, logging.FileHandler)
            ]
            assert len(file_handlers) > 0

            # Find the log file handler's file
            log_file = Path(file_handlers[0].baseFilename)

            # Check that the log file was created
            assert log_file.exists()

            # Verify the file is in the logs directory
            assert log_file.parent.resolve() == log_dir.resolve()

            # Clean up the test log file
            log_file.unlink()

        finally:
            # Clean up: Remove any handlers we added
            for handler in logging.getLogger().handlers[:]:
                handler.close()
                logging.getLogger().removeHandler(handler)

            # Restore original handlers
            for handler in original_handlers:
                logging.getLogger().addHandler(handler)
