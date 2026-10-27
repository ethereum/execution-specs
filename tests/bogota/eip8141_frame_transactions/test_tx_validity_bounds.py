"""
Transaction-level bound tests for
[EIP-8141: Frame Transaction](https://eips.ethereum.org/EIPS/eip-8141).

Each case sits exactly on a bound of §Constraints, or one unit past it:

- "assert tx.nonce < 2**64"
- "total_frame_gas += frame.limits.execution + frame.limits.state" and
  "assert total_frame_gas < 2**64"

These rules are decidable from the transaction alone, so each case is
pinned by a transaction test. No block can isolate either bound: no
account nonce reaches `2**64`, and a frame gas sum near `2**64` holds a
state budget no block fits. The valid side of the frame gas sum runs in
a block as well, which shows it passes the static bound and is rejected
for the block's state capacity instead.

The cap on the larger of the intrinsic-plus-frame gas and the calldata
floor ("assert max(frame_tx_intrinsic_gas + total_frame_execution_gas,
calldata_floor_gas) <= TX_MAX_GAS_LIMIT") is in
`test_static_validity.py`, next to the other static rules.
"""

from typing import List

import pytest
from execution_testing import (
    Account,
    Alloc,
    Environment,
    Fork,
    StateTestFiller,
    Transaction,
    TransactionException,
    TransactionTestFiller,
)

from .helpers import (
    BASE_FEE,
    FrameCase,
    approving_contract_sender,
    default_frame,
    fee_budget,
    verify_frame,
)
from .spec import ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = pytest.mark.valid_from("Bogota")

FRAME_EXECUTION_GAS = 10_000
"""Execution budget of each frame of the frame gas sum cases."""

FRAME_GAS_SUM_BOUND = 2**64
"""The bound the running sum of frame gas budgets stays below."""


def frame_gas_sum_frames(excess: int) -> List[FrameCase]:
    """
    Return two frames whose execution and state budgets sum to one below
    `FRAME_GAS_SUM_BOUND`, plus `excess`. Only the second frame's state
    budget makes the sum large, so each budget fits 64 bits on its own.
    """
    return [
        verify_frame(gas_limit=FRAME_EXECUTION_GAS, state_gas_limit=0),
        default_frame(
            gas_limit=FRAME_EXECUTION_GAS,
            state_gas_limit=FRAME_GAS_SUM_BOUND
            - 1
            - 2 * FRAME_EXECUTION_GAS
            + excess,
        ),
    ]


FRAME_GAS_SUM_CASES = [
    pytest.param(0, None, id="sum_2_pow_64_minus_one"),
    pytest.param(
        1,
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="sum_2_pow_64",
        marks=pytest.mark.exception_test,
    ),
]
"""
Excess of the frame gas sum over `2**64 - 1`, with the exception the
transaction must be rejected with, or `None` if it is valid.
"""


@pytest.mark.parametrize("excess,error", FRAME_GAS_SUM_CASES)
def test_frame_gas_sum_bound_transaction(
    transaction_test: TransactionTestFiller,
    pre: Alloc,
    excess: int,
    error: TransactionException | None,
) -> None:
    """
    Sum the frames' execution and state budgets to exactly `2**64 - 1`,
    which is valid, or to `2**64`, which is not.

    EIP-8141 §Constraints: "total_frame_gas += frame.limits.execution +
    frame.limits.state" and "assert total_frame_gas < 2**64".
    """
    tx = Transaction(
        sender=approving_contract_sender(pre),
        nonce=1,
        frames=frame_gas_sum_frames(excess),
        error=error,
    )

    transaction_test(pre=pre, tx=tx)


@pytest.mark.exception_test
def test_frame_gas_sum_bound_in_block(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Send the valid transaction of `test_frame_gas_sum_bound_transaction`
    in a block. No block holds `2**64 - 1` of state gas, so it is
    rejected, but for not fitting the block's state capacity: its frame
    gas sum passes the static bound.

    EIP-8141 §Constraints: "assert total_frame_gas < 2**64", and
    §Block-level gas accounting: "assert state_reservation <=
    block_gas_limit - block_output.block_state_gas_used".

    The `max_fee` budget covers the worst case at the base fee, so the
    fee check cannot reject the transaction either. The transaction one
    past the bound breaks both rules, which the EIP does not order, so
    it is pinned by the transaction test alone.
    """
    sender = approving_contract_sender(pre)
    frames = frame_gas_sum_frames(0)
    tx = Transaction(
        sender=sender,
        nonce=1,
        frames=frames,
        max_fee=fee_budget(fork, sender, frames).required_max_fee,
        error=TransactionException.GAS_ALLOWANCE_EXCEEDED,
    )

    state_test(
        env=Environment(base_fee_per_gas=BASE_FEE),
        pre=pre,
        tx=tx,
        post={sender: Account(nonce=1)},
    )


NONCE_BOUND = 2**64
"""The bound a frame transaction's nonce stays below."""


@pytest.mark.exception_test
def test_nonce_at_bound_transaction(
    transaction_test: TransactionTestFiller,
    pre: Alloc,
) -> None:
    """
    Reject a frame transaction whose nonce is `2**64`, the first value
    the nonce bound excludes.

    No account nonce reaches `2**64`, so in a block the transaction would
    also mismatch its sender's nonce, and the EIP does not order the two
    checks. Only the transaction itself isolates the bound.

    EIP-8141 §Constraints: "assert tx.nonce < 2**64".
    """
    tx = Transaction(
        sender=pre.fund_eoa(),
        nonce=NONCE_BOUND,
        frames=[verify_frame()],
        error=[
            TransactionException.NONCE_IS_MAX,
            TransactionException.NONCE_OVERFLOW,
        ],
    )

    transaction_test(pre=pre, tx=tx)
