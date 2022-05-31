from _pytest.config import Config
from _pytest.config.argparsing import Parser

import ethereum
from ethereum_spec_tools.evm_trace import evm_trace


def pytest_addoption(parser: Parser) -> None:
    """
    Accept --evm-trace option in pytest.
    """
    parser.addoption(
        "--evm-trace",
        dest="vmtrace",
        default=1,
        action="store_const",
        const=10,
        help="Run trace",
    )
    parser.addoption(
        "--optimized",
        dest="optimized",
        default=False,
        action="store_const",
        const=True,
        help="Use optimized state and ethash",
    )


def pytest_configure(config: Config) -> None:
    """
    Configure the ethereum module and log levels to output evm trace.
    """
    if config.getoption("vmtrace", default=1) == 10:
        config.option.__dict__["log_cli_level"] = "10"
        config.option.__dict__["log_format"] = "%(message)s"
        setattr(ethereum, "evm_trace", evm_trace)
    if config.getoption("optimized"):
        import ethereum_optimized

        ethereum_optimized.monkey_patch(None)
