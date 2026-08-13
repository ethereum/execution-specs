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
)

from ethereum_types.numeric import U64, U256, Uint

from ethereum_spec_tools.forks import Hardfork

W = TypeVar("W", Uint, U64, U256)

EXCEPTION_MAPS = {
    "BPO4": {
        "fork_blocks": [("osaka", 0)],
    },
    "Bogota": {
        "fork_blocks": [("amsterdam", 0)],
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


# Map testing ``Fork.transition_tool_name()`` → spec ``Hardfork.short_name``
# for cases where CamelCase → snake_case does not produce the spec
# module name:
# * ``Paris`` reports itself as ``"Merge"`` to the t8n protocol.
# * ``DAOFork`` would snake-case to ``d_a_o_fork``.
# * ``ConstantinopleFix`` is a testing-side distinction that the spec
#   folds into the ``constantinople`` module.
# * ``Bogota`` is a testing-side pseudo-fork that executes with the
#   ``amsterdam`` spec module until the spec repository grows a
#   dedicated Bogota fork module.
# TODO: Remove the ``Bogota`` alias (and its ``EXCEPTION_MAPS`` entry)
#  once a dedicated ``bogota`` fork module exists in the spec.
_SPEC_SHORT_NAME_OVERRIDES: Dict[str, str] = {
    "Merge": "paris",
    "DAOFork": "dao_fork",
    "ConstantinopleFix": "constantinople",
    "Bogota": "amsterdam",
}


def resolve_fork(fork_name: str) -> Hardfork:
    """
    Resolve a testing ``Fork.transition_tool_name()`` to its matching
    spec ``Hardfork``.

    CLI exception aliases like ``HomesteadToDaoAt5`` are resolved by
    :func:`find_fork` before the testing ``Fork`` is built, so the name
    reaching this function is always post-alias-resolution.
    """
    short = _SPEC_SHORT_NAME_OVERRIDES.get(fork_name)
    if short is None:
        short = re.sub(r"(?<!^)(?=[A-Z])", "_", fork_name).lower()
        # ``BPO1`` and friends would otherwise become ``b_p_o1``; mirror
        # the ``b_p_o → bpo`` collapse that :func:`find_fork` performs.
        short = re.sub(r"^b_p_o", "bpo", short)
    for fork in Hardfork.discover():
        if fork.short_name == short:
            return fork
    raise ValueError(
        f"No spec Hardfork matches testing fork name {fork_name!r} "
        f"(looked for short_name={short!r})"
    )


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
