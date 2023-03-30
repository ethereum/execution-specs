"""
Utilities for the EVM tools
"""

import json
import logging
import sys
from typing import Any, Callable, Dict, Optional, Tuple, TypeVar

import coincurve

from ethereum.base_types import U64, U256, Uint
from ethereum.utils.hexadecimal import Hash32

W = TypeVar("W", Uint, U64, U256)

EXCEPTION_MAPS = {
    "FrontierToHomesteadAt5": {
        "fork_blocks": [("frontier", 0), ("homestead", 5)],
    },
    "HomesteadToDaoAt5": {
        "fork_blocks": [("homestead", 0), ("dao_fork", 5)],
    },
    "HomesteadToEIP150At5": {
        "fork_blocks": [("homestead", 0), ("tangerine_whistle", 5)],
    },
    "EIP158ToByzantiumAt5": {
        "fork_blocks": [("spurious_dragon", 0), ("byzantium", 5)],
    },
    "ByzantiumToConstantinopleAt5": {
        "fork_blocks": [("byzantium", 0), ("constantinople", 5)],
    },
    "ConstantinopleToIstanbulAt5": {
        "fork_blocks": [("constantinople", 0), ("istanbul", 5)],
    },
    "BerlinToLondonAt5": {
        "fork_blocks": [("berlin", 0), ("london", 5)],
    },
    "EIP150": {
        "fork_blocks": [("tangerine_whistle", 0)],
    },
    "EIP158": {
        "fork_blocks": [("spurious_dragon", 0)],
    },
    "Merge": {
        "fork_blocks": [("paris", 0)],
    },
}


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


def get_module_name(forks: Any, options: Any) -> str:
    """
    Get the module name for the given state fork.
    """
    # If the state fork is an exception, use the exception config.
    exception_config: Optional[Dict[str, Any]] = None
    try:
        exception_config = EXCEPTION_MAPS[options.state_fork]
    except KeyError:
        pass

    if exception_config:
        with open(options.input_env, "r") as f:
            data = json.load(f)

        block_number = parse_hex_or_int(data["currentNumber"], Uint)

        for fork, fork_block in exception_config["fork_blocks"]:
            if block_number >= fork_block:
                fork_module = fork

        return fork_module

    # If the state fork is not an exception, use the fork name.
    for fork in forks:
        fork_module = fork.name.split(".")[-1]
        key = "".join(x.title() for x in fork_module.split("_"))

        if key == options.state_fork:
            return fork_module

    # Neither in exception nor a standard fork name.
    sys.exit(f"Unsupported state fork: {options.state_fork}")


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
