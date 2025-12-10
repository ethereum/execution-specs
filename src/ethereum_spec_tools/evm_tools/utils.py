"""
Utilities for the EVM tools.
"""

import json
import logging
import re
import sys
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Sequence,
    Tuple,
    TypeVar,
    Union,
)

import coincurve
from ethereum_types.numeric import U64, U256, Uint

from ethereum.crypto.hash import Hash32
from ethereum_spec_tools.forks import Hardfork

W = TypeVar("W", Uint, U64, U256)

EXCEPTION_MAPS = {
    "BPO2": {
        "fork_blocks": [("osaka", 0)],
    },
    "BPO3": {
        "fork_blocks": [("osaka", 0)],
    },
    "BPO4": {
        "fork_blocks": [("osaka", 0)],
    },
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
    "ConstantinopleFix": {
        "fork_blocks": [("constantinople", 0)],
    },
}

UNSUPPORTED_FORKS = ("constantinople",)


def parse_hex_or_int(value: str, to_type: Callable[[int], W]) -> W:
    """Read a Uint type from a hex string or int."""
    # find the function based on the type
    # if the value is a hex string, convert it
    if isinstance(value, str) and value.startswith("0x"):
        return to_type(int(value[2:], 16))
    # if the value is an str, convert it
    else:
        return to_type(int(value))


class FatalError(Exception):
    """Exception that causes the tool to stop."""

    pass


def find_fork(
    forks: Sequence[Hardfork], options: Any, stdin: Any
) -> Tuple[Hardfork, int | None]:
    """
    Get the module name and the fork block for the given state fork.
    """
    if options.state_fork.casefold() in UNSUPPORTED_FORKS:
        sys.exit(f"Unsupported state fork: {options.state_fork}")
    # If the state fork is an exception, use the exception config.
    exception_config: Optional[Dict[str, Any]] = None
    try:
        exception_config = EXCEPTION_MAPS[options.state_fork]
    except KeyError:
        pass

    current_fork_block: None | int = None
    current_fork_module = re.sub(
        r"(?<!^)(?=[A-Z])",
        "_",
        options.state_fork,
    ).lower()  # CamelCase to snake_case

    if exception_config:
        if options.input_env == "stdin":
            assert stdin is not None
            data = stdin["env"]
        else:
            with open(options.input_env, "r") as f:
                data = json.load(f)

        block_number = parse_hex_or_int(data["currentNumber"], Uint)

        for fork, fork_block in exception_config["fork_blocks"]:
            if block_number >= Uint(fork_block):
                current_fork_module = fork
                current_fork_block = fork_block

    current_fork_module = re.sub("^b_p_o", "bpo", current_fork_module)

    for fork in forks:
        if current_fork_module == fork.short_name:
            return fork, current_fork_block

    # Neither in exception nor a standard fork name.
    sys.exit(f"Unsupported state fork: {options.state_fork}")


def get_supported_forks() -> List[str]:
    """
    Get the supported forks.
    """
    supported_forks = [
        fork.title_case_name.replace(" ", "") for fork in Hardfork.discover()
    ]

    # Add the exception forks
    supported_forks.extend(EXCEPTION_MAPS.keys())

    # Remove the unsupported forks
    supported_forks = [
        fork
        for fork in supported_forks
        if fork.casefold() not in UNSUPPORTED_FORKS
    ]

    return supported_forks


def get_stream_logger(name: str) -> Any:
    """
    Get a logger that writes to stdout.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
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


def encode_to_hex(data: Union[bytes, int]) -> str:
    """
    Encode the data to a hex string.
    """
    if isinstance(data, int):
        return hex(data)
    elif isinstance(data, bytes):
        return "0x" + data.hex()
    else:
        raise Exception("Invalid data type")
