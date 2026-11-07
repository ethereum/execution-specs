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


@pytest.mark.inclusion_test
@pytest.mark.valid_from("SpuriousDragon")
@pytest.mark.exception_test
@pytest.mark.eels_base_coverage
@pytest.mark.parametrize(
    "y_parity",
    [0, 1],
)
def test_legacy_chain_id_zero(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    chain_config: ChainConfig,
    y_parity: int,
) -> None:
    """
    A legacy transaction whose v encodes a chain ID of 0 (v = 35 or 36)
    is rejected with INVALID_CHAINID when executed on a network with chain
    ID >= 1.
    """
    to = pre.fund_eoa(0xDEADBEEE)
    # EIP-155: v = 35 + 2 * chain_id + parity. For chain_id=0, v is 35 or 36.
    expected_v = 35 + y_parity
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=to,
        value=1,
        chain_id=0,
        gas_limit=fork.transaction_intrinsic_cost_calculator()(),
    ).with_signature_and_sender()
    tx = tx.copy(
        v=expected_v,
        error=TransactionException.INVALID_CHAINID,
    )

    state_test(
        pre=pre,
        post={to: Account(balance=0xDEADBEEE)},
        tx=tx,
    )


@pytest.mark.inclusion_test
@pytest.mark.valid_from("SpuriousDragon")
@pytest.mark.exception_test
@pytest.mark.eels_base_coverage
@pytest.mark.parametrize(
    "v",
    [
        0,
        1,
        26,
        29,
        34,
    ],
)
def test_legacy_v_sub_35(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    chain_config: ChainConfig,
    v: int,
) -> None:
    """
    A legacy transaction with v outside the valid pre-EIP-155 set {27, 28} and
    below 35 is invalid. Clients may reject either with an invalid signature
    (INVALID_SIGNATURE_VRS) or, if they attempt to derive a chain ID via
    unsigned arithmetic underflow, with a chain ID mismatch (INVALID_CHAINID).
    """
    to = pre.fund_eoa(0xDEADBEEE)
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=to,
        value=1,
        chain_id=chain_config.chain_id,
        gas_limit=fork.transaction_intrinsic_cost_calculator()(),
    ).with_signature_and_sender()
    error: TransactionException | list[TransactionException]
    if v in (0, 1):
        error = TransactionException.INVALID_SIGNATURE_VRS
    else:
        error = [
            TransactionException.INVALID_SIGNATURE_VRS,
            TransactionException.INVALID_CHAINID,
        ]
    tx = tx.copy(
        v=v,
        error=error,
    )

    state_test(
        pre=pre,
        post={to: Account(balance=0xDEADBEEE)},
        tx=tx,
    )
