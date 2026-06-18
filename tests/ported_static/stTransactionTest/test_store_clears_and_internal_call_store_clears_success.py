"""
Test_store_clears_and_internal_call_store_clears_success.

Ported from:
state_tests/stTransactionTest/StoreClearsAndInternalCallStoreClearsSuccessFiller.json

@manually-enhanced: Do not overwrite. The outer contract `target` clears 4
cold storage slots then `CALL`s the inner contract `addr`, which clears 10
cold storage slots; the value transfer and clears must all succeed.
EIP-8037/8038 raise the cold SSTORE-clear charge from 5000 to 13000 at
Amsterdam, so both gas budgets must rise by that charge delta or the inner
frame runs out of gas (clearing only 4 of its 10 slots) and the value
transfer rolls back. The inner `CALL` only forwards a fixed gas amount, so
its budget is bumped by the 10 inner clears; the transaction gas limit is
bumped by all 14 clears (10 inner plus 4 outer) so the outer frame can both
pay its own clears and forward the larger amount. Both bumps are derived
from the fork gas model and are exactly 0 pre-EIP-8037; do not hardcode the
Amsterdam values.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stTransactionTest/StoreClearsAndInternalCallStoreClearsSuccessFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_store_clears_and_internal_call_store_clears_success(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Test_store_clears_and_internal_call_store_clears_success."""
    coinbase = Address(0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B)
    sender = pre.fund_eoa(amount=0x1DCD6500)

    # EIP-8037/8038 raise the cold SSTORE-clear charge; derive the per-clear
    # delta (0 pre-EIP-8037) so both gas budgets keep every clear landing.
    sstore_charge = Op.SSTORE.with_metadata(
        key_warm=False, original_value=1, current_value=1, new_value=0
    ).gas_cost(fork)
    cold_clear_delta = sstore_charge - 5000

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    # Source: lll
    # {(SSTORE 0 0)(SSTORE 1 0)(SSTORE 2 0)(SSTORE 3 0)(SSTORE 4 0)(SSTORE 5 0)(SSTORE 6 0)(SSTORE 7 0)(SSTORE 8 0)(SSTORE 9 0)}  # noqa: E501
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x0)
        + Op.SSTORE(key=0x1, value=0x0)
        + Op.SSTORE(key=0x2, value=0x0)
        + Op.SSTORE(key=0x3, value=0x0)
        + Op.SSTORE(key=0x4, value=0x0)
        + Op.SSTORE(key=0x5, value=0x0)
        + Op.SSTORE(key=0x6, value=0x0)
        + Op.SSTORE(key=0x7, value=0x0)
        + Op.SSTORE(key=0x8, value=0x0)
        + Op.SSTORE(key=0x9, value=0x0)
        + Op.STOP,
        storage={
            0: 12,
            1: 12,
            2: 12,
            3: 12,
            4: 12,
            5: 12,
            6: 12,
            7: 12,
            8: 12,
            9: 12,
        },
        nonce=0,
    )
    # Source: lll
    # {(SSTORE 0 0)(SSTORE 1 0)(SSTORE 2 0)(SSTORE 3 0) (CALL 50000 <contract:0x0000000000000000000000000000000000000000> 1 0 0 0 0) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x0)
        + Op.SSTORE(key=0x1, value=0x0)
        + Op.SSTORE(key=0x2, value=0x0)
        + Op.SSTORE(key=0x3, value=0x0)
        + Op.CALL(
            # The inner frame clears 10 cold slots; forward its extra
            # charge so all 10 clears land at Amsterdam (delta is 0
            # pre-EIP-8037).
            gas=0xC350 + 10 * cold_clear_delta,
            address=addr,
            value=0x1,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        storage={0: 12, 1: 12, 2: 12, 3: 12, 4: 12},
        balance=10,
        nonce=0,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        # The whole transaction clears 14 cold slots (4 in the outer frame,
        # 10 in the inner frame); bump the limit by all of them so the outer
        # frame can pay its own clears and forward the larger inner budget.
        gas_limit=200000 + 14 * cold_clear_delta,
        value=10,
    )

    post = {
        addr: Account(storage={}, balance=1),
        target: Account(storage={4: 12}, balance=19),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
