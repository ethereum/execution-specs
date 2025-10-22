# Logging

This document describes the logging system used in the Ethereum Execution Spec Tests project. Currently, logging is only supported for `consume` commands.

## Overview

The project uses Python's standard logging module with custom extensions to provide enhanced logging capabilities. Our logging system is implemented in the `src/pytest_plugins/logging.py` module and provides the following features:

- Custom log levels between the standard Python log levels
- Timestamps with millisecond precision in UTC
- Color-coded log output (when not running in Docker)
- File logging with a consistent naming pattern
- Integration with pytest's output capture
- Support for distributed test execution with pytest-xdist

## Custom Log Levels

In addition to the standard Python log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL), we've added the following custom levels:

| Level | Numeric Value | Purpose |
|-------|--------------|---------|
| VERBOSE | 15 | For messages more detailed than INFO but less verbose than DEBUG |
| FAIL | 35 | For test failures and related issues (between WARNING and ERROR) |

## Using the Logger

### Getting a Logger

To use the custom logger in your code, import the `get_logger` function from the logging module:

```python
from pytest_plugins.logging import get_logger

# Create a logger with your module's name
logger = get_logger(__name__)
```

### Logging at Different Levels

You can use all standard Python log methods plus our custom methods:

```python
# Standard log levels
logger.debug("Detailed debug information")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error message")
logger.critical("Critical failure")

# Custom log levels
logger.verbose("More detailed than INFO, less than DEBUG")
logger.fail("Test failure or similar issue")
```

### When to Use Each Level

- **DEBUG (10)**: For very detailed diagnostic information useful for debugging
- **VERBOSE (15)**: For information that's useful during development but more detailed than INFO
- **INFO (20)**: For general information about program operation
- **WARNING (30)**: For potential issues that don't prevent program execution
- **FAIL (35)**: For test failures and related issues
- **ERROR (40)**: For errors that prevent an operation from completing
- **CRITICAL (50)**: For critical errors that may prevent the program from continuing

## Configuration

### Setting Log Level on the Command Line

You can adjust the log level when running pytest with the `--eest-log-level` option:

```bash
consume engine --input=latest@stable --eest-log-level=VERBOSE -s --sim.limit=".*chainid.*"
```

The argument accepts both log level names (e.g., "DEBUG", "VERBOSE", "INFO") and numeric values.

Adding pytest's `-s` flag writes the logging messages to the terminal; otherwise output will be written to the log file that is reported in the test session header at the end of the test session.

### Log File Output

Log files are automatically created in the `logs/` directory with a naming pattern that includes:

- The command name, e.g. `consume`,
- An optional subcommand (e.g., `engine`),
- A timestamp in UTC,
- The worker ID (when using pytest-xdist).

Example: `consume-engine-20240101-123456-main.log`

The log file path is displayed in the pytest header and summary.

### Using the Standalone Configuration in Non-Pytest Projects

The logging module can also be used in non-pytest projects by using the `configure_logging` function:

```python
from pytest_plugins.logging import configure_logging, get_logger

# Configure logging with custom settings
configure_logging(
    log_level="VERBOSE",
    log_file="my_application.log",
    log_to_stdout=True,
    log_format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    use_color=True
)

# Get a logger and use it
logger = get_logger(__name__)
logger.verbose("Logging configured in standalone application!")
```

The `configure_logging` function accepts the following parameters:

- `log_level`: A string or numeric log level (default: "INFO")
- `log_file`: Path to a log file, or None to disable file logging (default: None)
- `log_to_stdout`: Whether to log to stdout (default: True)
- `log_format`: The format string for log messages (default: "%(asctime)s [%(levelname)s] %(name)s: %(message)s")
- `use_color`: Whether to use colors in stdout output, or None to auto-detect (default: None)

## Implementation Details

### The EESTLogger Class

The `EESTLogger` class extends Python's `Logger` class to add the custom log methods. The main module logger is automatically configured to use this class.

### Formatters

Two formatter classes are available:

- `UTCFormatter`: Formats timestamps with millisecond precision in UTC
- `ColorFormatter`: Extends `UTCFormatter` to add ANSI colors to log level names in terminal output

### Pytest and Hive Integration

The logging module includes several pytest hooks to:

- Configure logging at the start of a test session
- Record logs during test execution
- Display the log file path in the test report
- Ensure logs are captured properly during fixture teardown

The `hive_pytest` plugin has been extended to propagate the logs to the `hiveview` UI via the test case's `details` ("description" in `hiveview`).

## Example Usage

A complete example of using the logging system in a `consume` test (or plugin):

```python
from pytest_plugins.logging import get_logger

# Get a properly typed logger for your module
logger = get_logger(__name__)

def test_something():
    # Use standard log levels
    logger.debug("Setting up test variables")
    logger.info("Starting test")
    
    # Use custom log levels
    logger.verbose("Additional details about test execution")
    
    # Log warnings or errors as needed
    if something_concerning:
        logger.warning("Something looks suspicious")
    
    if something_failed:
        logger.fail("Test condition not met")
        assert False, "Test failed"
    
    # Log successful completion
    logger.info("Test completed successfully")
```

All log messages will be displayed according to the configured log level and captured in the log file.
