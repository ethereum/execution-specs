"""
Utilities for the EVM tools
"""

import logging
from typing import Any, Callable, Tuple, TypeVar

import coincurve

from ethereum.base_types import U64, U256, Uint
from ethereum.utils.hexadecimal import Hash32

W = TypeVar("W", Uint, U64, U256)


def parse_hex_or_int(value: str, to_type: Callable[[int], W]) -> W:
    """Read a Uint type from a hex string or int"""
    # find the function based on the type
    # if the value is a hex string, convert it
    if isinstance(value, str) and value.startswith("0x"):
        return to_type(int(value[2:], 16))
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

    try:
        return exception_maps[state_fork]
    except KeyError:
        pass

    for fork in forks:
        value = fork.name.split(".")[-1]
        key = "".join(x.title() for x in value.split("_"))

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


def secp256k1_sign(msg_hash: Hash32, secret_key: int) -> Tuple[U256, ...]:
    """
    Returns the signature of a message hash given the secret key.
    """
    private_key = coincurve.PrivateKey.from_int(secret_key)
    signature = private_key.sign_recoverable(msg_hash, hasher=None)

    return (
        U256.from_be_bytes(signature[0:32]),
        U256.from_be_bytes(signature[32:64]),
        U256(signature[64]),
    )
