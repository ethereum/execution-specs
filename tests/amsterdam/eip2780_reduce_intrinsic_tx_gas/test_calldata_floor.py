"""
EIP-2780 interaction with the EIP-7623/7976 calldata floor.

A transaction's gas accounting uses ``max(intrinsic, calldata_floor)``.
EIP-2780 decomposes the intrinsic (``TX_BASE`` + recipient access +
value-transfer charges) and lowers ``TX_BASE`` to 12_000; that lowered
base also feeds the calldata floor. These tests pin the data-heavy
regime where the floor dominates:

- The floor binds, so ``gas_used`` equals the floor and the
  recipient/value charges folded into the intrinsic are masked: the
  gas paid is identical for a zero-value and a value-bearing
  transaction of the same calldata size.
- One gas below the floor, the transaction is rejected with
  ``INTRINSIC_GAS_BELOW_FLOOR_GAS_COST`` even though it covers the
  (smaller) decomposed intrinsic.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytes,
    Fork,
    RecipientType,
    StateTestFiller,
    Transaction,
    TransactionException,
)

from ...prague.eip7623_increase_calldata_cost.helpers import (
    find_floor_cost_threshold,
)
from .helpers import EOA_INITIAL_BALANCE
from .spec import ref_spec_2780

REFERENCE_SPEC_GIT_PATH = ref_spec_2780.git_path
REFERENCE_SPEC_VERSION = ref_spec_2780.version

pytestmark = pytest.mark.valid_from("Amsterdam")


def _floor_dominating_calldata(fork: Fork) -> Bytes:
    """
    Return zero-byte calldata sized so its calldata floor strictly
    exceeds the decomposed value-transfer intrinsic for a non-create
    call to an existing EOA.

    Reuses the shared EIP-7623 ``find_floor_cost_threshold`` binary
    search against this transaction shape, then steps one byte past the
    threshold (the last size where the floor does not yet dominate) so
    the floor strictly binds.
    """
    intrinsic_calc = fork.transaction_intrinsic_cost_calculator()
    floor_calc = fork.transaction_data_floor_cost_calculator()

    def intrinsic(byte_count: int) -> int:
        return intrinsic_calc(
            calldata=b"\x00" * byte_count,
            sends_value=True,
            recipient_type=RecipientType.EOA,
            return_cost_deducted_prior_execution=True,
        )

    def floor(byte_count: int) -> int:
        return floor_calc(data=b"\x00" * byte_count)

    threshold = find_floor_cost_threshold(
        floor_data_gas_cost_calculator=floor,
        intrinsic_gas_cost_calculator=intrinsic,
    )
    byte_count = threshold + 1

    assert floor(byte_count) > intrinsic(byte_count)
    return Bytes(b"\x00" * byte_count)


@pytest.mark.parametrize(
    "outcome",
    [
        pytest.param("floor_binds", id="floor_binds"),
        pytest.param(
            "below_floor",
            id="below_floor_rejected",
            marks=pytest.mark.exception_test,
        ),
    ],
)
@pytest.mark.parametrize(
    "value",
    [
        pytest.param(0, id="zero_value"),
        pytest.param(1, id="non-zero_value"),
    ],
)
def test_calldata_floor(
    fork: Fork,
    pre: Alloc,
    state_test: StateTestFiller,
    outcome: str,
    value: int,
) -> None:
    """
    A data-heavy transaction to an existing EOA whose calldata floor
    exceeds the decomposed value-transfer intrinsic.

    - ``floor_binds``: with a gas limit above the floor, ``gas_used``
      pins to the floor, so the value-transfer charges
      (``TRANSFER_LOG_COST + TX_VALUE_COST``) folded into the intrinsic
      are masked -- the gas paid is identical at ``value == 0`` and
      ``value == 1`` and only the moved wei differs.
    - ``below_floor``: a gas limit one short of the floor still covers
      the (smaller) decomposed intrinsic, so the floor -- built on the
      EIP-2780-lowered ``TX_BASE`` -- is the only thing that can reject
      it, with ``INTRINSIC_GAS_BELOW_FLOOR_GAS_COST``.
    """
    sender_initial_balance = 10**18
    sender = pre.fund_eoa(sender_initial_balance)
    target = pre.fund_eoa(amount=EOA_INITIAL_BALANCE)

    calldata = _floor_dominating_calldata(fork)
    calldata_floor = fork.transaction_data_floor_cost_calculator()(
        data=calldata,
        sends_value=bool(value),
        recipient_type=RecipientType.EOA,
    )
    gas_price = 1_000_000_000

    post: dict[Address, Account] = {}
    if outcome == "below_floor":
        # ``gas_limit`` one short of the floor still covers the
        # decomposed intrinsic, so the floor is the only thing that can
        # reject it; the post state is empty (transaction rejected).
        intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(
            calldata=calldata,
            sends_value=bool(value),
            recipient_type=RecipientType.EOA,
            return_cost_deducted_prior_execution=True,
        )
        gas_limit = calldata_floor - 1
        assert intrinsic_gas <= gas_limit, (
            "gas_limit must still cover the decomposed intrinsic so the "
            "rejection is pinned to the calldata floor"
        )
        tx = Transaction(
            sender=sender,
            to=target,
            value=value,
            data=calldata,
            gas_limit=gas_limit,
            gas_price=gas_price,
            error=TransactionException.INTRINSIC_GAS_BELOW_FLOOR_GAS_COST,
        )
    else:
        # ``floor_binds``: no explicit gas limit (auto-fills above the
        # floor). The gas component is the floor regardless of value
        # (charges masked); only the transferred wei changes the
        # balance.
        tx = Transaction(
            sender=sender,
            to=target,
            value=value,
            data=calldata,
            gas_price=gas_price,
        )
        sender_final_balance = (
            sender_initial_balance - value - calldata_floor * gas_price
        )
        post = {
            sender: Account(nonce=1, balance=sender_final_balance),
            target: Account(balance=EOA_INITIAL_BALANCE + value),
        }

    state_test(pre=pre, tx=tx, post=post)
