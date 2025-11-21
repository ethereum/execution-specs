"""Plugin that handles correct setting of chain-id and rpc-chain-id."""

import pytest

from execution_testing.test_types.chain_config_types import ChainConfigDefaults


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add command-line options to pytest."""
    execute_commands_group = parser.getgroup(
        "execute",
        "Arguments defining chain configuration for execute commands",
    )
    execute_commands_group.addoption(
        "--chain-id",
        action="store",
        dest="chain_id",
        required=False,
        type=int,
        default=None,
        help="ID of the chain where the tests will be executed.",
    )
    execute_commands_group.addoption(
        "--rpc-chain-id",
        action="store",
        dest="rpc_chain_id",
        required=False,
        type=int,
        default=None,
        help=(
            "ID of the chain where the tests will be executed. This flag "
            "is deprecated and will be removed in a future release. "
            "Use --chain-id instead."
        ),
    )


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config: pytest.Config) -> None:
    """
    Set the provided command-line arguments.
    """
    # Skip validation if we're just showing help
    if config.option.help:
        return

    chain_id = config.getoption("chain_id")
    rpc_chain_id = config.getoption("rpc_chain_id")

    if not ((chain_id is None) ^ (rpc_chain_id is None)):  # XOR
        pytest.exit(
            "ERROR: you must either pass --chain-id or --rpc-chain-id, "
            "but not both!\n"
            f"You passed: chain-id={chain_id}, rpc-chain-id={rpc_chain_id}",
            returncode=4,
        )

    # Use rpc_chain_id if chain_id is not provided (for backwards compatibility)
    if not chain_id:
        chain_id = rpc_chain_id

    # write to config
    ChainConfigDefaults.chain_id = chain_id
