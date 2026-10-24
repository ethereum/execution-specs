"""Unit tests for ``spamoor_dict_to_transaction``."""

from typing import Any, Dict

import pytest

from execution_testing.base_types import Hash
from execution_testing.cli.pytest_commands.plugins.testing_build_block.tx_convert import (  # noqa: E501
    spamoor_dict_to_transaction,
)
from execution_testing.test_types import EOA

# Deterministic private key for hermetic tests.
_TEST_KEY = Hash(
    0x1234567890123456789012345678901234567890123456789012345678901234
)
_SIGNER = EOA(key=_TEST_KEY, nonce=0)


def _base_tx_dict() -> Dict[str, Any]:
    """Return a minimal spamoor-style type-2 transaction dict."""
    return {
        "type": 2,
        "to": "0x1111111111111111111111111111111111111111",
        "value": 0,
        "data": "",
        "gas": 21000,
        "maxFeePerGas": 20,
        "maxPriorityFeePerGas": 1,
        "chainId": 1,
        "accessList": [],
    }


def test_creation_tx_to_is_none() -> None:
    """Empty ``to`` maps to ``None`` (contract creation)."""
    tx_dict = _base_tx_dict()
    tx_dict["to"] = ""
    tx_dict["data"] = "0xdeadbeef"

    tx = spamoor_dict_to_transaction(
        tx_dict, _SIGNER, chain_id=17000, nonce_override=0
    )

    assert tx.to is None


def test_signed_rlp_round_trip() -> None:
    """Signed transaction recovers the configured signer address."""
    tx_dict = _base_tx_dict()

    tx = spamoor_dict_to_transaction(
        tx_dict, _SIGNER, chain_id=17000, nonce_override=7
    )

    # ``with_signature_and_sender`` must populate ``sender`` from the
    # recovered signature, matching the EOA we signed with.
    assert tx.sender is not None
    assert tx.sender == _SIGNER
    # The serialised RLP must be non-empty and include a signature.
    rlp_bytes = tx.rlp()
    assert len(rlp_bytes) > 0
    assert "v" in tx.model_fields_set
    assert "r" in tx.model_fields_set
    assert "s" in tx.model_fields_set


def test_chain_id_override() -> None:
    """Spamoor's ``chainId: 1`` is overridden by the caller's chain id."""
    tx_dict = _base_tx_dict()
    assert tx_dict["chainId"] == 1

    tx = spamoor_dict_to_transaction(
        tx_dict, _SIGNER, chain_id=17000, nonce_override=0
    )

    assert int(tx.chain_id) == 17000


def test_nonce_override_wins_over_dict() -> None:
    """``nonce_override`` trumps any nonce present in the dict."""
    tx_dict = _base_tx_dict()
    tx_dict["nonce"] = 99

    tx = spamoor_dict_to_transaction(
        tx_dict, _SIGNER, chain_id=17000, nonce_override=3
    )

    assert int(tx.nonce) == 3


if __name__ == "__main__":  # pragma: no cover - manual invocation
    pytest.main([__file__, "-v"])
