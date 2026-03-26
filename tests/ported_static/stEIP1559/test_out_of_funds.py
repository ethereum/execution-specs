"""
Ori Pomerantz qbzzt1@gmail.com

Ported from:
state_tests/stEIP1559/outOfFundsFiller.yml
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
    TransactionException,
    AccessList,
    Hash,
)
from execution_testing.vm import Op
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)

REFERENCE_SPEC_GIT_PATH = "N/A"

REFERENCE_SPEC_VERSION = "N/A"

TX_DATA = [
    "00",
]
TX_GAS = [16777216, 40000]
TX_VALUE = [0, 1000000000000000000]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])

TX_ACCESS_LISTS: dict[int, list] = {
    0: [
    ],
}


def _tx_access_list(d: int) -> list | None:
    """Get access list for data index d. None means no access list (legacy tx)."""
    return TX_ACCESS_LISTS.get(d)


@pytest.mark.ported_from(
    ["state_tests/stEIP1559/outOfFundsFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0, 0, 0,
            id="declaredKeyWrite-g0-v0",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            0, 0, 1,
            id="declaredKeyWrite-g0-v1",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            0, 1, 0,
            id="declaredKeyWrite-g1-v0",
        ),
        pytest.param(
            0, 1, 1,
            id="declaredKeyWrite-g1-v1",
            marks=pytest.mark.exception_test,
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_out_of_funds(
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
        key=0xde0c95357363da5c1c5a73bd7c2781ca5c9fecc1014103b5e1d1e990ae8208ec
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=1000,
        gas_limit=71794957647893862,
    )

    # Source: yul
    # berlin {
    #     sstore(0, add(1,1))
    # }
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=0x2) + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0xd71b14c239fc39327f25764dd784c85ef0285fda"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=1)

    expect_entries_: list[dict] = [
        {
            "indexes": {'data': -1, 'gas': 0, 'value': -1},
            "network": ['>=Cancun'],
            "result": {},
            "expect_exception": {">=Cancun": TransactionException.INSUFFICIENT_ACCOUNT_FUNDS},
        },
        {
            "indexes": {'data': -1, 'gas': 1, 'value': 0},
            "network": ['>=Cancun'],
            "result": {},
        },
        {
            "indexes": {'data': -1, 'gas': 1, 'value': 1},
            "network": ['>=Cancun'],
            "result": {},
            "expect_exception": {">=Cancun": TransactionException.INSUFFICIENT_ACCOUNT_FUNDS},
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=target,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        value=TX_VALUE[v],
        max_fee_per_gas=100000000000,
        max_priority_fee_per_gas=100000000000,
        nonce=1,
        access_list=_tx_access_list(d),
        error=_exc,
    )


    state_test(env=env, pre=pre, post=post, tx=tx)
