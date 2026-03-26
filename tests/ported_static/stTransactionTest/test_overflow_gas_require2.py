"""
test_overflow_gas_require2

Ported from:
state_tests/stTransactionTest/OverflowGasRequire2Filler.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post_fork,
)

REFERENCE_SPEC_GIT_PATH = "N/A"

REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stTransactionTest/OverflowGasRequire2Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.pre_alloc_mutable
def test_overflow_gas_require2(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """test_overflow_gas_require2"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x50eadfb1030587ab3a993a6ecc073041fc3b45e119daa31a13d78c7e209631a5
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    pre[sender] = Account(balance=0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff)

    expect_entries_: list[dict] = [
        {
            "network": ['Cancun'],
            "result": {
        sender: Account(
                balance=0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe6357f,
                nonce=1,
            ),
    },
        },
        {
            "network": ['Prague'],
            "result": {
        sender: Account(
                balance=0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe5f97f,
                nonce=1,
            ),
    },
        },
    ]

    post, _exc = resolve_expect_post_fork(expect_entries_, fork)

    tx = Transaction(
        sender=sender,
        to=Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b"),
        data=bytes.fromhex("3240349548983454"),
        gas_limit=1152921504606846976,
        nonce=0,
        gas_price=80,
        error=_exc,
    )


    state_test(env=env, pre=pre, post=post, tx=tx)
