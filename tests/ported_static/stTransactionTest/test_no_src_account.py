"""
test_no_src_account

Ported from:
state_tests/stTransactionTest/NoSrcAccountFiller.yml
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
    "",
    "dead60a7",
    "00",
    "00",
    "00",
]
TX_GAS = [21000, 210000, 0]
TX_VALUE = [0, 1]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])

TX_ACCESS_LISTS: dict[int, list] = {
    2: [
    ],
    3: [
        AccessList(
            address=Address("0x4d7b154e5bf8310a4d8220c8eed80020e4b8f86f"),
            storage_keys=[
            ],
        ),
    ],
    4: [
        AccessList(
            address=Address("0x4d7b154e5bf8310a4d8220c8eed80020e4b8f86f"),
            storage_keys=[
                Hash("0x0000000000000000000000000000000000000000000000000000000000000000"),  # noqa: E501
                Hash("0x0000000000000000000000000000000000000000000000000000000000000001"),  # noqa: E501
            ],
        ),
    ],
}


def _tx_access_list(d: int) -> list | None:
    """Get access list for data index d. None means no access list (legacy tx)."""
    return TX_ACCESS_LISTS.get(d)


@pytest.mark.ported_from(
    ["state_tests/stTransactionTest/NoSrcAccountFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0, 0, 0,
            id="d0-g0-v0",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            0, 0, 1,
            id="d0-g0-v1",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            0, 1, 0,
            id="d0-g1-v0",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            0, 1, 1,
            id="d0-g1-v1",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            0, 2, 0,
            id="d0-g2-v0",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            0, 2, 1,
            id="d0-g2-v1",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            1, 0, 0,
            id="d1-g0-v0",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            1, 0, 1,
            id="d1-g0-v1",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            1, 1, 0,
            id="d1-g1-v0",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            1, 1, 1,
            id="d1-g1-v1",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            1, 2, 0,
            id="d1-g2-v0",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            1, 2, 1,
            id="d1-g2-v1",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            2, 0, 0,
            id="d2-g0-v0",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            2, 0, 1,
            id="d2-g0-v1",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            2, 1, 0,
            id="d2-g1-v0",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            2, 1, 1,
            id="d2-g1-v1",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            2, 2, 0,
            id="d2-g2-v0",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            2, 2, 1,
            id="d2-g2-v1",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            3, 0, 0,
            id="d3-g0-v0",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            3, 0, 1,
            id="d3-g0-v1",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            3, 1, 0,
            id="d3-g1-v0",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            3, 1, 1,
            id="d3-g1-v1",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            3, 2, 0,
            id="d3-g2-v0",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            3, 2, 1,
            id="d3-g2-v1",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            4, 0, 0,
            id="d4-g0-v0",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            4, 0, 1,
            id="d4-g0-v1",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            4, 1, 0,
            id="d4-g1-v0",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            4, 1, 1,
            id="d4-g1-v1",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            4, 2, 0,
            id="d4-g2-v0",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            4, 2, 1,
            id="d4-g2-v1",
            marks=pytest.mark.exception_test,
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_no_src_account(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """test_no_src_account"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = pre.fund_eoa(amount=0)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=89128960,
    )

    # Source: raw
    # 0x00
    target = pre.deploy_contract(
        code=Op.STOP,
        nonce=0,
        address=Address("0x4d7b154e5bf8310a4d8220c8eed80020e4b8f86f"),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {'data': 0, 'gas': [0, 1], 'value': -1},
            "network": ['>=Cancun'],
            "result": {},
            "expect_exception": {">=Frontier": TransactionException.INSUFFICIENT_ACCOUNT_FUNDS},
        },
        {
            "indexes": {'data': 1, 'gas': 0, 'value': -1},
            "network": ['>=Cancun'],
            "result": {},
            "expect_exception": {">=Frontier": [TransactionException.INSUFFICIENT_ACCOUNT_FUNDS, TransactionException.INTRINSIC_GAS_TOO_LOW]},
        },
        {
            "indexes": {'data': 1, 'gas': 1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {},
            "expect_exception": {">=Frontier": TransactionException.INSUFFICIENT_ACCOUNT_FUNDS},
        },
        {
            "indexes": {'data': [0, 1], 'gas': 2, 'value': 1},
            "network": ['>=Cancun'],
            "result": {},
            "expect_exception": {">=Frontier": [TransactionException.INSUFFICIENT_ACCOUNT_FUNDS, TransactionException.INTRINSIC_GAS_TOO_LOW]},
        },
        {
            "indexes": {'data': [0, 1], 'gas': 2, 'value': 0},
            "network": ['>=Cancun'],
            "result": {},
            "expect_exception": {">=Frontier": TransactionException.INTRINSIC_GAS_TOO_LOW},
        },
        {
            "indexes": {'data': 2, 'gas': 0, 'value': -1},
            "network": ['>=Cancun'],
            "result": {},
            "expect_exception": {">=Cancun": [TransactionException.INSUFFICIENT_ACCOUNT_FUNDS, TransactionException.INTRINSIC_GAS_TOO_LOW], ">=Frontier<MuirGlacier": TransactionException.TYPE_NOT_SUPPORTED},
        },
        {
            "indexes": {'data': 2, 'gas': 1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {},
            "expect_exception": {">=Cancun": TransactionException.INSUFFICIENT_ACCOUNT_FUNDS, ">=Frontier<MuirGlacier": TransactionException.TYPE_NOT_SUPPORTED},
        },
        {
            "indexes": {'data': 3, 'gas': 0, 'value': -1},
            "network": ['>=Cancun'],
            "result": {},
            "expect_exception": {">=Cancun": [TransactionException.INSUFFICIENT_ACCOUNT_FUNDS, TransactionException.INTRINSIC_GAS_TOO_LOW], ">=Frontier<MuirGlacier": TransactionException.TYPE_NOT_SUPPORTED},
        },
        {
            "indexes": {'data': 3, 'gas': 1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {},
            "expect_exception": {">=Cancun": TransactionException.INSUFFICIENT_ACCOUNT_FUNDS, ">=Frontier<MuirGlacier": TransactionException.TYPE_NOT_SUPPORTED},
        },
        {
            "indexes": {'data': 4, 'gas': 0, 'value': -1},
            "network": ['>=Cancun'],
            "result": {},
            "expect_exception": {">=Cancun": [TransactionException.INSUFFICIENT_ACCOUNT_FUNDS, TransactionException.INTRINSIC_GAS_TOO_LOW], ">=Frontier<MuirGlacier": TransactionException.TYPE_NOT_SUPPORTED},
        },
        {
            "indexes": {'data': 4, 'gas': 1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {},
            "expect_exception": {">=Cancun": TransactionException.INSUFFICIENT_ACCOUNT_FUNDS, ">=Frontier<MuirGlacier": TransactionException.TYPE_NOT_SUPPORTED},
        },
        {
            "indexes": {'data': [2, 3, 4], 'gas': 2, 'value': 1},
            "network": ['>=Cancun'],
            "result": {},
            "expect_exception": {">=Cancun": [TransactionException.INSUFFICIENT_ACCOUNT_FUNDS, TransactionException.INTRINSIC_GAS_TOO_LOW], ">=Frontier<MuirGlacier": TransactionException.TYPE_NOT_SUPPORTED},
        },
        {
            "indexes": {'data': [2, 3, 4], 'gas': 2, 'value': 0},
            "network": ['>=Cancun'],
            "result": {},
            "expect_exception": {">=Cancun": TransactionException.INTRINSIC_GAS_TOO_LOW, ">=Frontier<MuirGlacier": TransactionException.TYPE_NOT_SUPPORTED},
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
        gas_price=100,
        access_list=_tx_access_list(d),
        error=_exc,
    )


    state_test(env=env, pre=pre, post=post, tx=tx)
