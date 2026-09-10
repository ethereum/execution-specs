"""
Shared pytest plugin for live-client CLI flags and the fee-market fixture
chain.

Historically these lived in ``plugins/execute/execute.py``. That made them
unavailable to any other pytest command that talks to a live EL client
without also dragging in execute's parametrizer/hooks — which conflict with
fill's filler plugin. This module is the common denominator: any command
that hits an actual client (execute-remote, execute-hive, fill-stateful,
...) can load it.

The fixtures compute real per-session fees from ``eth_rpc`` and feed them
into ``pre.minimum_balance_for_pending_transactions(...)``, so queued setup
transactions get live fee values via ``Transaction.set_gas_price`` without
mutating ``TransactionDefaults`` globally.
"""

import os

import pytest

from execution_testing.logging import get_logger
from execution_testing.rpc import EthRPC
from execution_testing.test_types import EnvironmentDefaults

logger = get_logger(__name__)

# Multiplier applied to a one-shot live fee-market query to absorb the gap
# between query timing and tx submission (basefee can climb a few blocks
# between the two; the bump keeps txs landing without per-tx requeries).
FEE_BUMP_MULTIPLIER = 3.0


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register live-client CLI flags."""
    group = parser.getgroup(
        "live_client", "Live-client fee market and execution controls"
    )
    group.addoption(
        "--default-gas-price",
        action="store",
        dest="default_gas_price",
        type=int,
        default=None,
        help=(
            "Default gas price used for transactions, unless overridden by "
            "the test. Default=None (1.5x current network gas price)"
        ),
    )
    group.addoption(
        "--default-max-fee-per-gas",
        action="store",
        dest="default_max_fee_per_gas",
        type=int,
        default=None,
        help=(
            "Default max fee per gas used for transactions, unless "
            "overridden by the test. Default=None (1.5x current network max "
            "fee per gas)"
        ),
    )
    group.addoption(
        "--default-max-priority-fee-per-gas",
        action="store",
        dest="default_max_priority_fee_per_gas",
        type=int,
        default=None,
        help=(
            "Default max priority fee per gas used for transactions, "
            "unless overridden by the test. "
            "Default=None (1.5x current network max priority fee per gas)"
        ),
    )
    group.addoption(
        "--default-max-fee-per-blob-gas",
        action="store",
        dest="default_max_fee_per_blob_gas",
        type=int,
        default=None,
        help=(
            "Default max fee per blob gas used for transactions, unless "
            "overridden by the test. Default=None (1.5x current network max "
            "fee per blob gas)"
        ),
    )
    group.addoption(
        "--transaction-gas-limit",
        action="store",
        dest="transaction_gas_limit",
        default=EnvironmentDefaults.gas_limit // 4,
        type=int,
        help=(
            "Maximum gas used to execute a single transaction. Will be used "
            "as ceiling for tests that attempt to consume the entire block "
            f"gas limit. (Default: {EnvironmentDefaults.gas_limit // 4})"
        ),
    )
    group.addoption(
        "--transactions-per-block",
        action="store",
        dest="transactions_per_block",
        type=int,
        default=None,
        help=(
            "Number of transactions to send before producing the next block."
        ),
    )
    group.addoption(
        "--get-payload-wait-time",
        action="store",
        dest="get_payload_wait_time",
        type=float,
        default=0.3,
        help=(
            "Time to wait after sending a forkchoice_updated before getting "
            "the payload."
        ),
    )
    group.addoption(
        "--max-gas-per-test",
        action="store",
        dest="max_gas_per_test",
        default=None,
        type=int,
        help=(
            "Maximum gas limit for all transactions in a test. Default=None "
            "(No limit)"
        ),
    )
    group.addoption(
        "--dry-run",
        action="store_true",
        dest="dry_run",
        default=False,
        help=(
            "Don't send transactions, just print the minimum balance "
            "required per test."
        ),
    )
    group.addoption(
        "--max-tx-per-batch",
        action="store",
        dest="max_tx_per_batch",
        type=int,
        default=None,
        help=(
            "Maximum number of calls to send in a single batch request to "
            "the RPC. Default=750. Higher values may cause RPC instability."
        ),
    )
    group.addoption(
        "--use-testing-build-block",
        action="store_true",
        dest="use_testing_build_block",
        default=False,
        help=(
            "Use testing_buildBlockV1 to build blocks with transactions "
            "directly, instead of the standard Engine API flow. Only for "
            "clients that implement this endpoint."
        ),
    )


# ---------------------------------------------------------------------------
# Session-scope flag readers
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def transactions_per_block(
    request: pytest.FixtureRequest,
) -> int:
    """Number of transactions per block (defaults to worker count)."""
    if transactions_per_block := request.config.getoption(
        "transactions_per_block"
    ):
        return transactions_per_block
    worker_count_env = os.environ.get("PYTEST_XDIST_WORKER_COUNT")
    if not worker_count_env:
        return 1
    return max(int(worker_count_env), 1)


@pytest.fixture(scope="session")
def default_gas_price(request: pytest.FixtureRequest) -> int | None:
    """Return default gas price (from ``--default-gas-price``)."""
    gas_price = request.config.getoption("default_gas_price")
    if gas_price is not None:
        assert gas_price > 0, "Gas price must be greater than 0"
        logger.debug(
            f"Using configured default gas price: {gas_price / 10**9:.2f} Gwei"
        )
    return gas_price


@pytest.fixture(scope="session")
def dry_run(request: pytest.FixtureRequest) -> bool:
    """Return True if the test is a dry run."""
    return request.config.getoption("dry_run")


@pytest.fixture(scope="session")
def max_batch_size(request: pytest.FixtureRequest) -> int | None:
    """Return max calls per batch request, or None for default."""
    return request.config.getoption("max_tx_per_batch")


@pytest.fixture(scope="session")
def use_testing_build_block(
    request: pytest.FixtureRequest,
) -> bool:
    """Return whether to use testing_buildBlockV1 for block building."""
    return request.config.getoption("use_testing_build_block")


@pytest.fixture(scope="session")
def default_max_fee_per_gas(
    request: pytest.FixtureRequest,
) -> int | None:
    """Return default max fee per gas (from CLI flag, or None)."""
    max_fee_per_gas = request.config.getoption("default_max_fee_per_gas")
    if max_fee_per_gas is not None:
        logger.debug(
            f"Using configured default max fee per gas: "
            f"{max_fee_per_gas / 10**9:.2f} Gwei"
        )
    return max_fee_per_gas


@pytest.fixture(scope="session")
def default_max_priority_fee_per_gas(
    request: pytest.FixtureRequest,
) -> int | None:
    """Return default max priority fee per gas (from CLI flag, or None)."""
    max_priority_fee_per_gas = request.config.getoption(
        "default_max_priority_fee_per_gas"
    )
    if max_priority_fee_per_gas is not None:
        logger.debug(
            f"Using configured default max priority fee per gas: "
            f"{max_priority_fee_per_gas / 10**9:.2f} Gwei"
        )
    return max_priority_fee_per_gas


@pytest.fixture(scope="session")
def default_max_fee_per_blob_gas(
    request: pytest.FixtureRequest,
) -> int | None:
    """Return default max fee per blob gas (from CLI flag, or None)."""
    max_fee_per_blob_gas = request.config.getoption(
        "default_max_fee_per_blob_gas"
    )
    if max_fee_per_blob_gas is not None:
        logger.debug(
            f"Using configured default max fee per blob gas: "
            f"{max_fee_per_blob_gas / 10**9:.2f} Gwei"
        )
    return max_fee_per_blob_gas


# ---------------------------------------------------------------------------
# Function-scope live-fee fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def max_priority_fee_per_gas(
    eth_rpc: EthRPC,
    default_max_priority_fee_per_gas: int | None,
) -> int:
    """Max priority fee per gas for this test (live query or CLI default)."""
    max_priority_fee_per_gas = default_max_priority_fee_per_gas
    if max_priority_fee_per_gas is None:
        network_max_priority_fee = eth_rpc.max_priority_fee_per_gas()
        max_priority_fee_per_gas = int(
            network_max_priority_fee * FEE_BUMP_MULTIPLIER
        )
    return max_priority_fee_per_gas


@pytest.fixture(scope="function")
def max_fee_per_gas(
    eth_rpc: EthRPC,
    default_max_fee_per_gas: int | None,
    max_priority_fee_per_gas: int,
) -> int:
    """Max fee per gas for this test (live query or CLI default)."""
    max_fee_per_gas = default_max_fee_per_gas
    if max_fee_per_gas is None:
        network_gas_price = eth_rpc.gas_price()
        max_fee_per_gas = int(network_gas_price * FEE_BUMP_MULTIPLIER)
    if max_priority_fee_per_gas > max_fee_per_gas:
        # Priority fee can exceed max fee due to query timing; bump.
        max_fee_per_gas = max_priority_fee_per_gas + 1
    return max_fee_per_gas


@pytest.fixture(scope="function")
def max_fee_per_blob_gas(
    eth_rpc: EthRPC,
    default_max_fee_per_blob_gas: int | None,
) -> int:
    """Max fee per blob gas for this test (live query or CLI default)."""
    max_fee_per_blob_gas = default_max_fee_per_blob_gas
    if max_fee_per_blob_gas is None:
        network_blob_base_fee = eth_rpc.blob_base_fee()
        max_fee_per_blob_gas = int(network_blob_base_fee * FEE_BUMP_MULTIPLIER)
    return max_fee_per_blob_gas


@pytest.fixture(scope="function")
def gas_price(max_fee_per_gas: int, max_priority_fee_per_gas: int) -> int:
    """Gas price = max_fee_per_gas + max_priority_fee_per_gas."""
    return max_fee_per_gas + max_priority_fee_per_gas


@pytest.fixture()
def max_gas_limit_per_test(request: pytest.FixtureRequest) -> int | None:
    """Total gas limit across all transactions in a given test (or None)."""
    return request.config.getoption("max_gas_per_test")
