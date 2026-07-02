"""
Test_internal_call_store_clears_success.

Ported from:
state_tests/stTransactionTest/InternalCallStoreClearsSuccessFiller.json

@manually-enhanced: Do not overwrite. The `target` contract forwards a
fixed `CALL` gas budget (0x186A0) to `addr`, which clears 10 cold
storage slots (12 -> 0). EIP-8038 raises the cold SSTORE-clear charge
from 5000 to 13000, so the 10 clears jump from 50000 to 130000 gas and
no longer fit in the forwarded budget or the transaction gas limit:
`addr` runs out of gas, its slots stay set, and the inner value
transfer rolls back, defeating the "store clears success" intent. Both
the inner `CALL` gas argument and the transaction gas limit are raised
by `10 * cold_clear_delta` so all 10 clears still succeed. The per-clear
delta is derived from the fork gas model and is exactly 0 pre-EIP-8037;
do not hardcode the Amsterdam values. The asserted balances are
fork-invariant once the clears land, and the post does not assert the
sender balance, so no balance adjustment is needed.
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
        "state_tests/stTransactionTest/InternalCallStoreClearsSuccessFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_internal_call_store_clears_success(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Test_internal_call_store_clears_success."""
    coinbase = Address(0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B)
    sender = pre.fund_eoa(amount=0x3B9ACA00)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    # EIP-8038 raises the cold SSTORE-clear charge; bump the forwarded
    # CALL gas and the transaction gas limit by the per-clear delta times
    # the 10 clears so every clear still lands instead of running out of
    # gas. The delta is 0 before the EIP-8037/8038 repricing.
    cold_clear_delta = (
        Op.SSTORE.with_metadata(
            key_warm=False, original_value=1, current_value=1, new_value=0
        ).gas_cost(fork)
        - 5000
    )
    clears_gas_bump = 10 * cold_clear_delta

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
    # { (CALL 100000 <contract:0x0000000000000000000000000000000000000000> 1 0 0 0 0) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.CALL(
            gas=0x186A0 + clears_gas_bump,
            address=addr,
            value=0x1,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        balance=10,
        nonce=0,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=160000 + clears_gas_bump,
        value=10,
    )

    post = {
        addr: Account(storage={}, balance=1),
        sender: Account(nonce=1),
        target: Account(balance=19),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
