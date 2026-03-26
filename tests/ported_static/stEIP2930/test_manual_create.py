"""
Ori Pomerantz qbzzt1@gmail.com

Ported from:
state_tests/stEIP2930/manualCreateFiller.yml
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
    AccessList,
    Hash,
)
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)

REFERENCE_SPEC_GIT_PATH = "N/A"

REFERENCE_SPEC_VERSION = "N/A"

TX_DATA = [
    "5a3031505a90036001555a60ff6000555a900360005500",
    "5a3031505a90036001555a60ff6000555a900360005500",
    "5a3031505a90036001555a60ff6000555a900360005500",
]
TX_GAS = [400000]
TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])

TX_ACCESS_LISTS: dict[int, list] = {
    0: [
        AccessList(
            address=Address("0x0000000000000000000000000000000000000100"),
            storage_keys=[
                Hash("0x0000000000000000000000000000000000000000000000000000000000000000"),  # noqa: E501
            ],
        ),
    ],
    1: [
        AccessList(
            address=Address("0xec0e71ad0a90ffe1909d27dac207f7680abba42d"),
            storage_keys=[
                Hash("0x0000000000000000000000000000000000000000000000000000000000000001"),  # noqa: E501
            ],
        ),
    ],
    2: [
        AccessList(
            address=Address("0xec0e71ad0a90ffe1909d27dac207f7680abba42d"),
            storage_keys=[
                Hash("0x0000000000000000000000000000000000000000000000000000000000000000"),  # noqa: E501
            ],
        ),
    ],
}


def _tx_access_list(d: int) -> list | None:
    """Get access list for data index d. None means no access list (legacy tx)."""
    return TX_ACCESS_LISTS.get(d)


@pytest.mark.ported_from(
    ["state_tests/stEIP2930/manualCreateFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0, 0, 0,
            id="allBad",
        ),
        pytest.param(
            1, 0, 0,
            id="addrGoodCellBad",
        ),
        pytest.param(
            2, 0, 0,
            id="allGood",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_manual_create(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Ori Pomerantz qbzzt1@gmail."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=71794957647893862,
    )

    pre[sender] = Account(balance=0x1000000000000000000, nonce=1)

    expect_entries_: list[dict] = [
        {
            "indexes": {'data': [2], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        Address("0xec0e71ad0a90ffe1909d27dac207f7680abba42d"): Account(storage={0: 20008, 1: 106}),  # noqa: E501
    },
        },
        {
            "indexes": {'data': [0, 1], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        Address("0xec0e71ad0a90ffe1909d27dac207f7680abba42d"): Account(storage={0: 22108, 1: 106}),  # noqa: E501
    },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=None,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        nonce=1,
        gas_price=10,
        access_list=_tx_access_list(d),
        error=_exc,
    )


    state_test(env=env, pre=pre, post=post, tx=tx)
