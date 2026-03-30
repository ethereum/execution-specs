"""
Tests if CALLDATALOAD, CALLDATACOPY, CODECOPY and CODESIZE work...

call data is always empty in initcode context and "code" is initcode.

Ported from:
state_tests/stCreateTest/CreateTransactionCallDataFiller.yml
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Alloc,
    Bytes,
    Environment,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stCreateTest/CreateTransactionCallDataFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="calldataload",
        ),
        pytest.param(
            1,
            0,
            0,
            id="calldatacopy",
        ),
        pytest.param(
            2,
            0,
            0,
            id="codecopy",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_create_transaction_call_data(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Tests if CALLDATALOAD, CALLDATACOPY, CODECOPY and CODESIZE work..."""
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=sender,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre[sender] = Account(balance=0x5AF3107A4000)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": [0, 1], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                compute_create_address(address=sender, nonce=0): Account(
                    storage={}, code=b"", nonce=1
                ),
            },
        },
        {
            "indexes": {"data": [2], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                compute_create_address(address=sender, nonce=0): Account(
                    storage={},
                    code=bytes.fromhex("3860008039386000f3"),
                    nonce=1,
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Bytes("60003560005560213560015500"),
        Bytes("6001600080376000516000556020600160003760005160015500"),
        Bytes("3860008039386000f3"),
    ]
    tx_gas = [100000]
    tx_value = [0]

    tx = Transaction(
        sender=sender,
        to=None,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
