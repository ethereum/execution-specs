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
    ChainConfig,
    Conditional,
    Environment,
    Fork,
    Op,
    StateTestFiller,
    Transaction,
    TransactionException,
    compute_create_address,
)

from .helpers import APPROVE_ALL, default_frame, verify_frame
from .spec import Spec, ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = pytest.mark.valid_from("Bogota")


ADMISSION_CASES = [
    pytest.param(
        # No budget covers a worst case of zero, since every frame
        # transaction pays a nonzero intrinsic cost at the base fee.
        dict(max_fee=0),
        TransactionException.INSUFFICIENT_MAX_FEE_PER_GAS,
        id="max_fee_zero",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        # The escrow is the worst case plus the largest tip, never the
        # budget itself, so the largest budget is includable.
        dict(max_fee=2**256 - 1),
        None,
        id="max_fee_at_max",
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


@pytest.mark.exception_test
def test_wrong_chain_id(
    state_test: StateTestFiller,
    pre: Alloc,
    chain_config: ChainConfig,
) -> None:
    """
    Reject a frame transaction signed for another chain: its chain ID is
    one above the chain's, and its signature entry is valid over its own
    signature hash, which commits to that chain ID.

    EIP-8141 §Outer transaction payload: "`chain_id` -- the chain ID in
    which the transaction is valid."
    """
    sender = pre.fund_eoa()
    tx = Transaction(
        sender=sender,
        chain_id=chain_config.chain_id + 1,
        frames=[verify_frame()],
        error=TransactionException.INVALID_CHAINID,
    )

    state_test(pre=pre, tx=tx, post={sender: Account(nonce=0)})


SENDER_NONCE = 5
"""Nonce of the sender of the nonce match cases."""


# Funding an EOA with a custom nonce mutates the shared pre-alloc.
@pytest.mark.pre_alloc_mutable
@pytest.mark.parametrize(
    "tx_nonce,error",
    [
        pytest.param(SENDER_NONCE, None, id="nonce_matches"),
        pytest.param(
            SENDER_NONCE - 1,
            TransactionException.NONCE_MISMATCH_TOO_LOW,
            id="nonce_too_low",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            SENDER_NONCE + 1,
            TransactionException.NONCE_MISMATCH_TOO_HIGH,
            id="nonce_too_high",
            marks=pytest.mark.exception_test,
        ),
    ],
)
def test_nonce_mismatch(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_nonce: int,
    error: Optional[TransactionException],
) -> None:
    """
    Send a frame transaction whose nonce is the sender's nonce, one
    below it, or one above it.

    EIP-8141 §Behavior: "Ensure `tx.nonce == state[tx.sender].nonce`".
    """
    sender = pre.fund_eoa(nonce=SENDER_NONCE)
    tx = Transaction(
        sender=sender,
        nonce=tx_nonce,
        frames=[verify_frame()],
        error=error,
    )

    state_test(
        pre=pre,
        tx=tx,
        post={sender: Account(nonce=SENDER_NONCE if error else tx_nonce + 1)},
    )


def test_nonce_checked_only_before_frames(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Let a contract sender's code create a contract in a `DEFAULT` frame
    before its `VERIFY` frame approves, so the sender's nonce has
    already moved past `tx.nonce` when `APPROVE` increments it.

    The transaction's nonce is matched once, before any frame runs, so
    the earlier increment does not invalidate it, and `APPROVE`
    increments the nonce the sender holds at that point: the sender
    ends at `tx.nonce + 2`, not `tx.nonce + 1`.

    EIP-8141 §Behavior: "To begin processing a frame transaction:
    Ensure `tx.nonce == state[tx.sender].nonce`", and §APPROVE
    Behavior: "Increment the sender's nonce, set `payer =
    resolved_target`, and collect the transaction's `max_cost` from
    `payer`."

    The EIP does not state whether `APPROVE` re-reads the nonce or
    writes `tx.nonce + 1`. This test follows the literal "Increment the
    sender's nonce", so a client that writes `tx.nonce + 1` at `APPROVE`
    fails this fixture.
    """
    sender_code = Conditional(
        condition=Op.CALLDATASIZE,
        if_true=Op.POP(Op.CREATE(0, 0, 0)) + Op.STOP,
        if_false=APPROVE_ALL,
    )
    sender = pre.deploy_contract(code=sender_code, balance=10**18)
    created = compute_create_address(address=sender, nonce=1)
    tx = Transaction(
        sender=sender,
        nonce=1,
        frames=[
            # With calldata, the sender's code creates a contract.
            default_frame(target=sender, data=b"\x01"),
            # Without calldata, it approves.
            verify_frame(),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={sender: Account(nonce=3), created: Account(nonce=1)},
    )
