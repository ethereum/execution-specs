"""
Transaction-level bound tests for
[EIP-8141: Frame Transaction](https://eips.ethereum.org/EIPS/eip-8141).

Each case sits exactly on a bound of §Constraints, or one unit past it:

- "assert tx.nonce < 2**64"
- "total_frame_gas += frame.limits.execution + frame.limits.state" and
  "assert total_frame_gas < 2**64"
- "assert max(frame_tx_intrinsic_gas + total_frame_execution_gas,
  calldata_floor_gas) <= TX_MAX_GAS_LIMIT"

These rules are decidable from the transaction alone, so each case is
pinned by a transaction test. Where a block can isolate the rule, a
state test runs alongside it, so that the reference implementation
checks the verdict at fill time; see `test_static_validity.py` for why
both formats are needed. No block can isolate the nonce bound (no
account nonce reaches `2**64`) or the rejected side of the frame gas
sum (its state budget never fits a block), so those cases are pinned by
their transaction tests only.
"""

from typing import List

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    Fork,
    Op,
    StateTestFiller,
    Transaction,
    TransactionException,
    TransactionTestFiller,
)

from .helpers import (
    APPROVE_ALL,
    BASE_FEE,
    FrameCase,
    default_frame,
    fee_budget,
    verify_frame,
)
from .spec import Spec, ref_spec_8141

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
    pytest.param(0, None, id="sum_at_bound_minus_one"),
    pytest.param(
        1,
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
        id="sum_at_bound",
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
        sender=pre.deploy_contract(code=APPROVE_ALL, balance=10**18),
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
    sender = pre.deploy_contract(code=APPROVE_ALL, balance=10**18)
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


def calldata_floor_at_cap_frames(
    fork: Fork, target: Address, excess: int
) -> List[FrameCase]:
    """
    Return frames whose calldata floor equals the per-transaction gas cap
    exactly, plus `excess` zero bytes of data at the floor price each.

    The floor is the always-paid base costs plus a fixed price per data
    byte. The per-frame cost is odd, so a suitable frame count makes the
    gap between the cap and the base costs a whole number of bytes. After
    the `VERIFY` frame, every frame calls `target` with just enough gas
    for its cold entry, and the last one carries the data.
    """
    gas_costs = fork.gas_costs()
    floor_per_byte = (
        gas_costs.TX_DATA_TOKEN_STANDARD * gas_costs.TX_DATA_TOKEN_FLOOR
    )
    floor_calculator = fork.frame_transaction_data_floor_cost_calculator()
    cap = fork.transaction_gas_limit_cap()
    assert cap is not None
    frame_count = next(
        count
        for count in range(2, Spec.MAX_FRAMES + 1)
        if (cap - floor_calculator(frames=count)) % floor_per_byte == 0
    )
    data_length = (
        cap - floor_calculator(frames=frame_count)
    ) // floor_per_byte + excess

    entry_gas = fork.frame_entry_gas_calculator()()
    frames = [verify_frame(state_gas_limit=0)] + [
        default_frame(target=target, gas_limit=entry_gas, state_gas_limit=0)
        for _ in range(frame_count - 1)
    ]
    frames[-1].data = Bytes(b"\x00" * data_length)

    floor = floor_calculator(frames=frames)
    assert floor == cap + excess * floor_per_byte
    # The intrinsic cost plus the frame execution budgets stays below
    # the cap, so only the floor can exceed it.
    standard = fork.frame_transaction_intrinsic_cost_calculator()(
        frames=frames, return_cost_deducted_prior_execution=True
    ) + sum(int(frame.gas_limit) for frame in frames)
    assert standard < cap
    return frames


CALLDATA_FLOOR_AT_CAP_CASES = [
    pytest.param(0, None, id="floor_at_cap"),
    pytest.param(
        1,
        TransactionException.GAS_LIMIT_EXCEEDS_MAXIMUM,
        id="floor_one_byte_above_cap",
        marks=pytest.mark.exception_test,
    ),
]
"""
Zero bytes of data in excess of a calldata floor equal to the cap,
with the exception the transaction must be rejected with.
"""


@pytest.mark.parametrize("excess,error", CALLDATA_FLOOR_AT_CAP_CASES)
def test_calldata_floor_at_cap(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    excess: int,
    error: TransactionException | None,
) -> None:
    """
    Make the calldata floor equal the per-transaction gas cap exactly,
    which is valid, or exceed it by one data byte, which is not, while
    the intrinsic cost plus the frame execution budgets stays far below
    the cap.

    EIP-8141 §Constraints: "assert max(frame_tx_intrinsic_gas +
    total_frame_execution_gas, calldata_floor_gas) <= TX_MAX_GAS_LIMIT".
    """
    sender = pre.deploy_contract(code=APPROVE_ALL, balance=10**18)
    target = pre.deploy_contract(code=Op.STOP)
    tx = Transaction(
        sender=sender,
        nonce=1,
        frames=calldata_floor_at_cap_frames(fork, target, excess),
        error=error,
    )

    state_test(
        pre=pre,
        tx=tx,
        post={sender: Account(nonce=1 if error else 2)},
    )


@pytest.mark.parametrize("excess,error", CALLDATA_FLOOR_AT_CAP_CASES)
def test_calldata_floor_at_cap_transaction(
    transaction_test: TransactionTestFiller,
    pre: Alloc,
    fork: Fork,
    excess: int,
    error: TransactionException | None,
) -> None:
    """
    Assert the same cap as `test_calldata_floor_at_cap` on the
    transaction itself rather than on a block containing it.
    """
    sender = pre.deploy_contract(code=APPROVE_ALL, balance=10**18)
    target = pre.deploy_contract(code=Op.STOP)
    tx = Transaction(
        sender=sender,
        nonce=1,
        frames=calldata_floor_at_cap_frames(fork, target, excess),
        error=error,
    )

    transaction_test(pre=pre, tx=tx)


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
