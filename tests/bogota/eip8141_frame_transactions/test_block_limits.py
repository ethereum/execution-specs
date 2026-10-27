"""
Block capacity tests for a frame transaction that follows another one
in the same block, for
[EIP-8141: Frame Transaction](https://eips.ethereum.org/EIPS/eip-8141).

A block accounts for execution gas and state gas separately, and a frame
transaction is includable only if its worst case fits what the earlier
transactions left of each dimension (§Block-level gas accounting):

```
execution_reservation = max(
    frame_tx_intrinsic_gas
    + sum(frame.limits.execution for frame in tx.frames),
    calldata_floor_gas,
)
state_reservation = sum(frame.limits.state for frame in tx.frames)

assert execution_reservation <= (
    block_gas_limit - block_output.block_execution_gas_used
)
assert state_reservation <= (
    block_gas_limit - block_output.block_state_gas_used
)
```

(The EIP writes each expression on one line; it is wrapped here.)

The first transaction of each block here writes a fresh storage slot, so
it leaves both counters above zero: its execution gas is counted as
`max(gas_used_before_refund - tx_state_gas, calldata_floor_gas)` and its
state gas as `tx_state_gas`. The second transaction then reserves
exactly what is left of one dimension, or one unit more. A block holding
a transaction that does not fit is invalid.

The same reservation after a refunding first transaction is in
`test_refund_edges.py::test_next_transaction_capacity_after_refund`
(pre-refund execution), and after a refilled one in
`test_gas_settlement.py::test_state_reservation_after_refilled_transaction`
(net state gas); a single transaction's reservation against an empty
block is in `test_admission_validity.py::test_block_capacity_reservations`.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    BlockchainTestFiller,
    Bytes,
    Environment,
    Fork,
    Op,
    Transaction,
)

from .helpers import (
    APPROVE_ALL,
    FrameTransaction,
    approving_contract_sender,
    default_frame,
    reservation_block,
    reservation_error,
    reserving_frame_tx,
    verify_frame,
)
from .spec import ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = pytest.mark.valid_from("Bogota")

BLOCK_GAS_LIMIT = 400_000
"""
Block gas limit of the execution and state cases, above the first
transaction's usage in both dimensions.
"""

SECOND_TX_EXECUTION_GAS = 50_000
"""Execution budget of the second transaction in the state case."""

FLOOR_DATA_LENGTH = 4_096
"""
Zero bytes of frame data in the second transaction of the floor case:
enough for its calldata floor to exceed its intrinsic cost plus frame
execution budgets by far.
"""

WRITE_SLOT = Op.SSTORE(0, 1)
"""Code that writes one fresh storage slot."""


@pytest.mark.parametrize(
    "excess",
    [
        pytest.param(0, id="fits"),
        pytest.param(1, id="one_over", marks=pytest.mark.exception_test),
    ],
)
@pytest.mark.parametrize(
    "dimension",
    [
        pytest.param("execution", id="execution_reservation"),
        pytest.param("state", id="state_reservation"),
        pytest.param("floor", id="calldata_floor_reservation"),
    ],
)
def test_second_transaction_reservation(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    dimension: str,
    excess: int,
) -> None:
    """
    Include a frame transaction after a first frame transaction that
    used both gas dimensions, reserving exactly the block's remaining
    capacity in one dimension, or one unit more.

    - `execution_reservation`: the second transaction's intrinsic cost
      plus its frame execution budgets.
    - `state_reservation`: the second transaction's frame state budgets.
    - `calldata_floor_reservation`: the second transaction's calldata
      floor, which exceeds its intrinsic cost plus frame execution
      budgets. Here the block gas limit is set to the first
      transaction's execution gas plus that floor.

    EIP-8141 §Block-level gas accounting: "A frame transaction may be
    included in a block only if its worst case fits the remaining
    capacity of **each** dimension", with `execution_reservation <=
    block_gas_limit - block_output.block_execution_gas_used` and
    `state_reservation <= block_gas_limit -
    block_output.block_state_gas_used`.
    """
    first_sender = approving_contract_sender(pre)
    written = pre.deploy_contract(code=WRITE_SLOT)
    first_tx = FrameTransaction.build(
        fork=fork,
        sender=first_sender,
        nonce=1,
        frames=[
            verify_frame(
                code=APPROVE_ALL, gas_limit_delta=0, state_gas_limit=0
            ),
            default_frame(
                target=written,
                code=WRITE_SLOT,
                gas_limit_delta=0,
                state_gas_limit_delta=0,
            ),
        ],
    )
    # The block's counters after the first transaction.
    execution_used = max(first_tx.execution_gas, first_tx.calldata_floor)
    state_used = first_tx.state_gas
    assert state_used > 0

    error = reservation_error(excess)
    block_gas_limit = BLOCK_GAS_LIMIT
    if dimension == "execution":
        second_tx = reserving_frame_tx(
            pre,
            fork,
            execution_reservation=block_gas_limit - execution_used + excess,
            error=error,
        )
    elif dimension == "state":
        # A contract sender carries no signature entries and the frame no
        # data, so a frame count prices the intrinsic cost exactly.
        one_frame_intrinsic = (
            fork.frame_transaction_intrinsic_cost_calculator()(
                frames=1, return_cost_deducted_prior_execution=True
            )
        )
        second_tx = reserving_frame_tx(
            pre,
            fork,
            execution_reservation=one_frame_intrinsic
            + SECOND_TX_EXECUTION_GAS,
            state_reservation=block_gas_limit - state_used + excess,
            error=error,
        )
    else:
        second_sender = approving_contract_sender(pre)
        frames = [
            verify_frame(
                code=APPROVE_ALL, gas_limit_delta=0, state_gas_limit=0
            ),
            # The frame only carries the data: with no execution budget
            # it halts at entry, which a non-`VERIFY` frame may do
            # without invalidating the transaction.
            default_frame(
                target=written,
                data=Bytes(b"\x00" * FLOOR_DATA_LENGTH),
                gas_limit=0,
                state_gas_limit=0,
            ),
        ]
        for frame in frames:
            frame.settle_budgets(fork)
        floor = fork.frame_transaction_data_floor_cost_calculator()(
            frames=frames
        )
        standard = fork.frame_transaction_intrinsic_cost_calculator()(
            frames=frames, return_cost_deducted_prior_execution=True
        ) + sum(int(frame.gas_limit) for frame in frames)
        # Only the floor operand can exceed the remaining capacity.
        assert standard < floor - 1
        block_gas_limit = execution_used + floor - excess
        second_tx = Transaction(
            sender=second_sender, nonce=1, frames=frames, error=error
        )

    blockchain_test(
        pre=pre,
        blocks=[
            reservation_block(
                [first_tx, second_tx], gas_limit=block_gas_limit, excess=excess
            )
        ],
        post={
            first_sender: Account(nonce=1 if excess else 2),
            written: Account(storage={} if excess else {0: 1}),
            second_tx.sender: Account(nonce=1 if excess else 2),
        },
        genesis_environment=Environment(gas_limit=block_gas_limit),
    )
