"""Tests for the chain ID a legacy transaction encodes in its v value."""

import pytest
from execution_testing import (
    Account,
    Alloc,
    ChainConfig,
    Fork,
    StateTestFiller,
    Transaction,
    TransactionException,
)

from .spec import ref_spec_155

REFERENCE_SPEC_GIT_PATH = ref_spec_155.git_path
REFERENCE_SPEC_VERSION = ref_spec_155.version


@pytest.mark.inclusion_test
@pytest.mark.valid_from("SpuriousDragon")
@pytest.mark.exception_test
@pytest.mark.eels_base_coverage
@pytest.mark.parametrize(
    "case",
    [
        "largest_64_bit_chain_id",
        "smallest_65_bit_chain_id",
        "chain_id_plus_2_64",
    ],
)
def test_legacy_chain_id_over_64_bits(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    chain_config: ChainConfig,
    case: str,
) -> None:
    """
    A legacy transaction whose v encodes a chain ID too large for 64 bits may
    be rejected as an invalid v or as a chain ID mismatch depending on client
    implementation, while one that fits in 64 bits is a chain ID mismatch.
    """
    error: TransactionException | list[TransactionException]
    if case == "largest_64_bit_chain_id":
        signed_for = encoded_in_v = 2**64 - 1
        error = TransactionException.INVALID_CHAINID
    elif case == "smallest_65_bit_chain_id":
        signed_for = encoded_in_v = 2**64
        error = [
            TransactionException.INVALID_SIGNATURE_VRS,
            TransactionException.INVALID_CHAINID,
        ]
    elif case == "chain_id_plus_2_64":
        signed_for = chain_config.chain_id
        encoded_in_v = chain_config.chain_id + 2**64
        error = [
            TransactionException.INVALID_SIGNATURE_VRS,
            TransactionException.INVALID_CHAINID,
        ]
    else:
        raise ValueError(f"Unknown case: {case}")

    to = pre.fund_eoa(0xDEADBEEE)
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=to,
        value=1,
        chain_id=signed_for,
        # Signing up front needs the final gas limit.
        gas_limit=fork.transaction_intrinsic_cost_calculator()(),
    ).with_signature_and_sender()
    tx = tx.copy(
        # EIP-155: v = 35 + 2 * chain_id + parity.
        v=tx.v + 2 * (encoded_in_v - signed_for),
        error=error,
    )

    state_test(
        pre=pre,
        post={to: Account(balance=0xDEADBEEE)},
        tx=tx,
    )
