"""Test the sender plugin's worker key nonce synchronization."""

from unittest.mock import MagicMock

import pytest

from execution_testing.base_types import Account, Number
from execution_testing.rpc.rpc_types import JSONRPCError
from execution_testing.test_types import EOA

from ..sender import sync_worker_key_nonce


@pytest.fixture
def mock_eth_rpc() -> MagicMock:
    """Create a mock EthRPC instance."""
    return MagicMock()


@pytest.fixture
def mock_eoa() -> EOA:
    """Create a mock EOA with a known nonce."""
    return EOA(
        key=b"\x01" * 32,
        nonce=0,
    )


@pytest.mark.parametrize(
    "initial_nonce,rpc_nonce",
    [
        pytest.param(
            5,
            10,
            id="rpc_nonce_higher_than_local",
        ),
        pytest.param(
            10,
            5,
            id="rpc_nonce_lower_than_local_chain_revert",
        ),
        pytest.param(
            7,
            0,
            id="rpc_nonce_reset_to_zero_full_revert",
        ),
    ],
)
def test_worker_key_nonce_sync(
    mock_eth_rpc: MagicMock,
    mock_eoa: EOA,
    initial_nonce: int,
    rpc_nonce: int,
) -> None:
    """Test worker key nonce is updated whenever it differs from RPC."""
    mock_eoa.nonce = Number(initial_nonce)
    mock_eth_rpc.get_account.return_value = Account(
        nonce=rpc_nonce, balance=10**18
    )

    sync_worker_key_nonce(mock_eth_rpc, mock_eoa)

    assert mock_eoa.nonce == Number(rpc_nonce), (
        f"Expected nonce to be synced to {rpc_nonce}, got {mock_eoa.nonce}"
    )


def test_worker_key_nonce_unchanged_when_matching(
    mock_eth_rpc: MagicMock,
    mock_eoa: EOA,
) -> None:
    """Test worker key nonce is not modified when it matches RPC."""
    mock_eoa.nonce = Number(5)
    mock_eth_rpc.get_account.return_value = Account(nonce=5, balance=10**18)

    sync_worker_key_nonce(mock_eth_rpc, mock_eoa)

    assert mock_eoa.nonce == Number(5)


def test_sync_falls_back_to_pending_on_jsonrpc_error(
    mock_eth_rpc: MagicMock,
    mock_eoa: EOA,
) -> None:
    """Test fallback to pending block when latest is unavailable."""
    mock_eoa.nonce = Number(3)
    pending_account = Account(nonce=5, balance=10**18)
    mock_eth_rpc.get_account.side_effect = [
        JSONRPCError(code=-32000, message="not available"),
        pending_account,
    ]

    result = sync_worker_key_nonce(mock_eth_rpc, mock_eoa)

    assert mock_eoa.nonce == Number(5)
    assert result is pending_account
    assert mock_eth_rpc.get_account.call_count == 2
