"""Tests for live-client RPC post-state verification."""

from unittest.mock import Mock

import pytest

from execution_testing.base_types import Address, Hash
from execution_testing.fixtures import AccountCheck, PostVerifications
from execution_testing.rpc import EthRPC

from ..simulators.helpers.exceptions import LoggedError
from ..simulators.helpers.post_state import (
    prime_post_verification_queries,
    verify_post_verification_queries,
)

ADDRESS = Address(0x1234)


def _rpc_with_expected_state() -> Mock:
    """Return an EthRPC-shaped mock with one deterministic account state."""
    rpc = Mock(spec=EthRPC)
    rpc.get_balance.return_value = 7
    rpc.get_transaction_count.return_value = 3
    rpc.get_code.return_value = b"\x60\x00"
    rpc.get_storage_at.return_value = Hash(2)
    return rpc


def _post_verifications() -> PostVerifications:
    """Return checks spanning every state field observable through RPC."""
    return PostVerifications(
        accounts={
            ADDRESS: AccountCheck(
                nonce=3,
                balance=7,
                code=b"\x60\x00",
                storage={1: 2},
            )
        }
    )


def test_prime_reads_exact_fields_that_will_be_verified() -> None:
    """Priming touches each checked RPC key without asserting its old value."""
    rpc = _rpc_with_expected_state()

    prime_post_verification_queries(rpc, _post_verifications())

    rpc.get_balance.assert_called_once_with(ADDRESS)
    rpc.get_transaction_count.assert_called_once_with(ADDRESS)
    rpc.get_code.assert_called_once_with(ADDRESS)
    rpc.get_storage_at.assert_called_once_with(ADDRESS, Hash(1))


def test_verify_accepts_live_state_matching_fill_assertions() -> None:
    """All explicitly asserted post-state fields must match the live client."""
    rpc = _rpc_with_expected_state()

    verify_post_verification_queries(rpc, _post_verifications())


def test_verify_rejects_stale_storage_cache_value() -> None:
    """A stale storage value returned after execution fails verification."""
    rpc = _rpc_with_expected_state()
    rpc.get_storage_at.return_value = Hash(1)

    with pytest.raises(LoggedError, match="storage mismatch"):
        verify_post_verification_queries(rpc, _post_verifications())


def test_verify_rejects_observable_state_for_deleted_account() -> None:
    """A deleted account must not expose stale balance, nonce, or code."""
    rpc = _rpc_with_expected_state()
    rpc.get_balance.return_value = 1
    post = PostVerifications(accounts={ADDRESS: None})

    with pytest.raises(LoggedError, match="nonexistent/empty account"):
        verify_post_verification_queries(rpc, post)
