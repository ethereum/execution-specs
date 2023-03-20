"""
Utilities for the EVM tools
"""

import logging
from typing import Any, Callable

from ethereum.base_types import U64, U256, Uint
from ethereum.utils.hexadecimal import hex_to_u64, hex_to_u256, hex_to_uint


def read_hex_or_int(value: str, to_type: Any) -> Any:
    """Read a Uint type from a hex string or int"""
    # find the function based on the type
    to_type_function: Callable[[str], Any]
    if to_type == Uint:
        to_type_function = hex_to_uint
    elif to_type == U256:
        to_type_function = hex_to_u256
    elif to_type == U64:
        to_type_function = hex_to_u64
    else:
        raise Exception("Unknown type")

    # if the value is a hex string, convert it
    if isinstance(value, str) and value.startswith("0x"):
        return to_type_function(value)
    # if the value is an str, convert it
    else:
        return to_type(int(value))


class FatalException(Exception):
    """Exception that causes the tool to stop"""

    pass


def ensure_success(f: Callable, *args: Any) -> Any:
    """
    Ensure that the function call succeeds.
    Raise a FatalException if it fails.
    """
    try:
        return f(*args)
    except Exception as e:
        raise FatalException(e)


def get_module_name(forks: Any, state_fork: str) -> str:
    """
    Get the module name for the given state fork.
    """
    exception_maps = {
        "EIP150": "tangerine_whistle",
        "EIP158": "spurious_dragon",
    }

    if state_fork in exception_maps:
        return exception_maps[state_fork]

    for fork in forks:
        value = fork.name.split(".")[-1]
        key_items = [x.title() for x in value.split("_")]
        key = "".join(key_items)

        if key == state_fork:
            break

    return value


def get_stream_logger(name: str) -> Any:
    """
    Get a logger that writes to stdout.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level=logging.INFO)
    stream_handler = logging.StreamHandler()
    formatter = logging.Formatter("%(levelname)s:%(name)s:%(message)s")
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger
