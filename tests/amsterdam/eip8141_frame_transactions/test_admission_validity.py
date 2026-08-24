"""
Admission validity tests for
[EIP-8141: Frame Transaction](https://eips.ethereum.org/EIPS/eip-8141).

The rules here need context beyond the transaction itself — the block
environment or the sender's account state — so their verdicts are
pinned only by state tests: a client cannot generally evaluate them on
the transaction alone and may accept such a transaction at that level.
Rules decidable from the transaction alone are in
`test_static_validity.py`, where every case is also pinned at the
transaction level.
"""

from typing import Any, Dict, Optional

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    BlockException,
    Environment,
    Fork,
    Op,
    StateTestFiller,
    Transaction,
    TransactionException,
)

from .helpers import verify_frame
from .spec import Spec, ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

# EIP-8141 is slated for the fork after Amsterdam, so fixtures are
# labeled with the pseudo `Bogota` fork (Amsterdam + EIP-8141), even
# though the spec prototypes the EIP inside the Amsterdam fork module.
# Fill these tests with `--fork Bogota`.
pytestmark = pytest.mark.valid_from("Bogota")


ADMISSION_CASES = [
    pytest.param(
        dict(max_fee_per_gas=2**255),
        TransactionException.GASLIMIT_PRICE_PRODUCT_OVERFLOW,
        id="max_cost_overflow",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        # The largest fee cap whose product with the per-transaction
        # gas cap still fits the maximum cost bound, so the case is
        # includable regardless of the transaction's derived gas limit.
        dict(
            max_fee_per_gas=lambda fork: (2**256 - 1)
            // fork.transaction_gas_limit_cap()
        ),
        None,
        id="max_cost_within_bound",
    ),
    pytest.param(
        # A frame transaction's chain id is a 256-bit field, so a value
        # too wide for the 64-bit field of every other transaction type
        # still decodes and is rejected for naming another chain.
        dict(chain_id=2**64),
        TransactionException.INVALID_CHAINID,
        id="chain_id_above_64_bits",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        dict(chain_id=2**256 - 1),
        TransactionException.INVALID_CHAINID,
        id="chain_id_at_256_bit_maximum",
        marks=pytest.mark.exception_test,
    ),
]
"""
Field-level variations of a minimal frame transaction, each with the
exception a rule evaluated at admission must reject it with, or `None`
where the variation stays exactly within the rule's bound.
"""


@pytest.mark.parametrize("tx_overrides,error", ADMISSION_CASES)
def test_admission_constraints(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    tx_overrides: Dict[str, Any],
    error: Optional[TransactionException],
) -> None:
    """
    Vary one transaction-level field of a minimal frame transaction and
    check that a rule evaluated at admission rejects it, or accepts it
    exactly within the rule's bound.

    Override values that depend on the fork are expressed as callables
    taking the fork, since the parametrize table is built before the
    fork is known.
    """
    # The sender holds the largest representable balance so that even
    # the case priced at the largest includable fee cap can escrow its
    # maximum cost when a frame approves payment.
    sender = pre.fund_eoa(amount=2**256 - 1)
    tx_kwargs: Dict[str, Any] = dict(
        sender=sender,
        frames=[verify_frame()],
        error=error,
    )
    tx_kwargs.update(
        {
            key: value(fork) if callable(value) else value
            for key, value in tx_overrides.items()
        }
    )
    tx = Transaction(**tx_kwargs)

    state_test(
        pre=pre,
        tx=tx,
        # The sender's nonce only increments if the transaction is
        # valid and executes.
        post={sender: Account(nonce=0 if error else 1)},
    )


# Funding an EOA with a custom nonce mutates the shared pre-alloc.
@pytest.mark.pre_alloc_mutable
def test_nonce_at_maximum(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Accept a frame transaction whose nonce is one below the overflow
    bound: the highest nonce a frame transaction may carry, leaving
    room for the post-execution increment.
    """
    sender = pre.fund_eoa(nonce=2**64 - 2)
    tx = Transaction(
        sender=sender,
        nonce=2**64 - 2,
        frames=[verify_frame()],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={sender: Account(nonce=2**64 - 1)},
    )


BLOCK_GAS_LIMIT = 200_000
"""
Block gas limit sized so a single frame transaction's reservation can
cross it in either dimension.
"""

CAPACITY_EXECUTION_GAS = 50_000
"""Execution budget of the state-dimension capacity cases."""


@pytest.mark.parametrize(
    "dimension,excess",
    [
        pytest.param("execution", 0, id="execution_reservation_at_limit"),
        pytest.param(
            "execution",
            1,
            id="execution_reservation_above_limit",
            marks=pytest.mark.exception_test,
        ),
        pytest.param("state", 0, id="state_reservation_at_limit"),
        pytest.param(
            "state",
            1,
            id="state_reservation_above_limit",
            marks=pytest.mark.exception_test,
        ),
    ],
)
def test_block_capacity_reservations(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    dimension: str,
    excess: int,
) -> None:
    """
    Reserve a block's remaining capacity per gas dimension.

    A frame transaction's explicit budgets make its reservations exact:
    the intrinsic cost plus the frames' execution budgets in the
    execution dimension, the frames' state budgets in the state
    dimension. A reservation at the block's gas limit is includable;
    one unit above leaves the transaction unincludable and the block
    invalid.
    """
    sender = pre.deploy_contract(
        code=Op.APPROVE(0, 0, Spec.APPROVE_EXECUTION_AND_PAYMENT),
        balance=10**18,
    )
    # A contract sender carries no signature entries and the frame no
    # data, so a frame count prices the intrinsic cost exactly.
    intrinsic = fork.frame_transaction_intrinsic_cost_calculator()(
        frames=1,
        return_cost_deducted_prior_execution=True,
    )
    if dimension == "execution":
        execution_budget = BLOCK_GAS_LIMIT - intrinsic + excess
        state_budget = 0
    else:
        execution_budget = CAPACITY_EXECUTION_GAS
        state_budget = BLOCK_GAS_LIMIT + excess

    tx = Transaction(
        sender=sender,
        nonce=1,
        frames=[
            verify_frame(
                gas_limit=execution_budget, state_gas_limit=state_budget
            )
        ],
        error=(
            TransactionException.GAS_ALLOWANCE_EXCEEDED if excess else None
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                gas_limit=BLOCK_GAS_LIMIT,
                exception=(
                    [
                        BlockException.GAS_USED_OVERFLOW,
                        TransactionException.GAS_ALLOWANCE_EXCEEDED,
                    ]
                    if excess
                    else None
                ),
            )
        ],
        post={sender: Account(nonce=1 if excess else 2)},
        genesis_environment=Environment(gas_limit=BLOCK_GAS_LIMIT),
    )
