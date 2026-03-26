"""
test_mload32bit_bound2

Ported from:
state_tests/stMemoryStressTest/mload32bitBound2Filler.json
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
from execution_testing.vm import Op
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)

REFERENCE_SPEC_GIT_PATH = "N/A"

REFERENCE_SPEC_VERSION = "N/A"

TX_DATA = [
    "",
]
TX_GAS = [150000, 16777216]
TX_VALUE = [10]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/stMemoryStressTest/mload32bitBound2Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0, 0, 0,
            id="-g0",
        ),
        pytest.param(
            0, 1, 0,
            id="-g1",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_mload32bit_bound2(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """test_mload32bit_bound2"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xd566533f0ccab46749ac8725e15da8ce513758257002a8b481f6f5f96484c5ed
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=37791080412587,
    )

    # Source: lll
    # { [[ 1 ]] (MLOAD 6294967296) }
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x177359400)) + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0xc287e277d2163771e55d630bdd96c6405a6fe251"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x157b5373e07ca)

    expect_entries_: list[dict] = [
        {
            "indexes": {'data': -1, 'gas': 0, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        target: Account(
                storage={},
                code=bytes.fromhex("6401773594005160015500"),
                nonce=0,
            ),
        sender: Account(storage={}, code=b"", nonce=1),
    },
        },
        {
            "indexes": {'data': -1, 'gas': 1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        target: Account(
                storage={},
                code=bytes.fromhex("6401773594005160015500"),
                nonce=0,
            ),
        sender: Account(storage={}, code=b"", nonce=1),
    },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=target,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        value=TX_VALUE[v],
        nonce=0,
        gas_price=10,
        error=_exc,
    )


    state_test(env=env, pre=pre, post=post, tx=tx)
