"""Tests for Nethermind client CLI support."""

from execution_testing.client_clis.clis.nethermind import (
    NethermindExceptionMapper,
)
from execution_testing.exceptions import TransactionException


def test_invalid_signature_vrs_mapping() -> None:
    """Map Nethermind invalid signatures to INVALID_SIGNATURE_VRS."""
    mapped_exceptions = NethermindExceptionMapper().message_to_exception(
        "InvalidTxSignature: Signature is invalid."
    )

    assert isinstance(mapped_exceptions, list)
    assert set(mapped_exceptions) == {
        TransactionException.INVALID_SIGNATURE_VRS,
        TransactionException.INVALID_CHAINID,
    }
