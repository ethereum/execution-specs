from _pytest.config import Config
from _pytest.config.argparsing import Parser


def pytest_addoption(parser: Parser) -> None:
    """
    Accept --evm-trace option in pytest.
    """
    parser.addoption(
        "--optimized",
        dest="optimized",
        default=False,
        action="store_const",
        const=True,
        help="Use optimized state and ethash",
    )

    parser.addoption(
        "--evm_trace",
        dest="evm_trace",
        default=False,
        action="store_const",
        const=True,
        help="Create an evm trace",
    )


def pytest_configure(config: Config) -> None:
    """
    Configure the ethereum module and log levels to output evm trace.
    """
    if config.getoption("optimized"):
        import ethereum_optimized

        ethereum_optimized.monkey_patch(None)

    if config.getoption("evm_trace"):
        import ethereum.trace
        from ethereum_spec_tools.evm_tools.t8n.evm_trace import (
            evm_trace as new_trace_function,
        )

        # Replace the function in the module
        ethereum.trace.set_evm_trace(new_trace_function)


# def pytest_sessionstart() -> None:
# TODO do we still need to do something here?
#    return
