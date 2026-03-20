"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stTransactionTest/NoSrcAccountFiller.yml
"""

import pytest
from execution_testing import (
    EOA,
    AccessList,
    Address,
    Alloc,
    Environment,
    Hash,
    StateTestFiller,
    Transaction,
)
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
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    ["tests/static/state_tests/stTransactionTest/NoSrcAccountFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v, tx_access_list",
    [
        pytest.param(
            0, 0, 0, None, id="case0", marks=pytest.mark.exception_test
        ),
        pytest.param(
            0, 0, 1, None, id="case1", marks=pytest.mark.exception_test
        ),
        pytest.param(
            0, 1, 0, None, id="case2", marks=pytest.mark.exception_test
        ),
        pytest.param(
            0, 1, 1, None, id="case3", marks=pytest.mark.exception_test
        ),
        pytest.param(
            0, 2, 0, None, id="case4", marks=pytest.mark.exception_test
        ),
        pytest.param(
            0, 2, 1, None, id="case5", marks=pytest.mark.exception_test
        ),
        pytest.param(
            1, 0, 0, None, id="case6", marks=pytest.mark.exception_test
        ),
        pytest.param(
            1, 0, 1, None, id="case7", marks=pytest.mark.exception_test
        ),
        pytest.param(
            1, 1, 0, None, id="case8", marks=pytest.mark.exception_test
        ),
        pytest.param(
            1, 1, 1, None, id="case9", marks=pytest.mark.exception_test
        ),
        pytest.param(
            1, 2, 0, None, id="case10", marks=pytest.mark.exception_test
        ),
        pytest.param(
            1, 2, 1, None, id="case11", marks=pytest.mark.exception_test
        ),
        pytest.param(
            2, 0, 0, [], id="case12", marks=pytest.mark.exception_test
        ),
        pytest.param(
            2, 0, 1, [], id="case13", marks=pytest.mark.exception_test
        ),
        pytest.param(
            2, 1, 0, [], id="case14", marks=pytest.mark.exception_test
        ),
        pytest.param(
            2, 1, 1, [], id="case15", marks=pytest.mark.exception_test
        ),
        pytest.param(
            2, 2, 0, [], id="case16", marks=pytest.mark.exception_test
        ),
        pytest.param(
            2, 2, 1, [], id="case17", marks=pytest.mark.exception_test
        ),
        pytest.param(
            3,
            0,
            0,
            [
                AccessList(
                    address=Address(
                        "0x4d7b154e5bf8310a4d8220c8eed80020e4b8f86f"
                    ),
                    storage_keys=[],
                )
            ],
            id="case18",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            3,
            0,
            1,
            [
                AccessList(
                    address=Address(
                        "0x4d7b154e5bf8310a4d8220c8eed80020e4b8f86f"
                    ),
                    storage_keys=[],
                )
            ],
            id="case19",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            3,
            1,
            0,
            [
                AccessList(
                    address=Address(
                        "0x4d7b154e5bf8310a4d8220c8eed80020e4b8f86f"
                    ),
                    storage_keys=[],
                )
            ],
            id="case20",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            3,
            1,
            1,
            [
                AccessList(
                    address=Address(
                        "0x4d7b154e5bf8310a4d8220c8eed80020e4b8f86f"
                    ),
                    storage_keys=[],
                )
            ],
            id="case21",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            3,
            2,
            0,
            [
                AccessList(
                    address=Address(
                        "0x4d7b154e5bf8310a4d8220c8eed80020e4b8f86f"
                    ),
                    storage_keys=[],
                )
            ],
            id="case22",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            3,
            2,
            1,
            [
                AccessList(
                    address=Address(
                        "0x4d7b154e5bf8310a4d8220c8eed80020e4b8f86f"
                    ),
                    storage_keys=[],
                )
            ],
            id="case23",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            4,
            0,
            0,
            [
                AccessList(
                    address=Address(
                        "0x4d7b154e5bf8310a4d8220c8eed80020e4b8f86f"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000001"  # noqa: E501
                        ),
                    ],
                )
            ],
            id="case24",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            4,
            0,
            1,
            [
                AccessList(
                    address=Address(
                        "0x4d7b154e5bf8310a4d8220c8eed80020e4b8f86f"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000001"  # noqa: E501
                        ),
                    ],
                )
            ],
            id="case25",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            4,
            1,
            0,
            [
                AccessList(
                    address=Address(
                        "0x4d7b154e5bf8310a4d8220c8eed80020e4b8f86f"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000001"  # noqa: E501
                        ),
                    ],
                )
            ],
            id="case26",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            4,
            1,
            1,
            [
                AccessList(
                    address=Address(
                        "0x4d7b154e5bf8310a4d8220c8eed80020e4b8f86f"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000001"  # noqa: E501
                        ),
                    ],
                )
            ],
            id="case27",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            4,
            2,
            0,
            [
                AccessList(
                    address=Address(
                        "0x4d7b154e5bf8310a4d8220c8eed80020e4b8f86f"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000001"  # noqa: E501
                        ),
                    ],
                )
            ],
            id="case28",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            4,
            2,
            1,
            [
                AccessList(
                    address=Address(
                        "0x4d7b154e5bf8310a4d8220c8eed80020e4b8f86f"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000001"  # noqa: E501
                        ),
                    ],
                )
            ],
            id="case29",
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
    tx_access_list: list | None,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x4A2FFC8867FD8D1773481CF13F36E44F033133C579520D2745E46C3BBBF21E6A
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=89128960,
    )

    # Source: raw bytecode
    contract = pre.deploy_contract(
        code=bytes.fromhex("00"),
        nonce=0,
        address=Address("0x4d7b154e5bf8310a4d8220c8eed80020e4b8f86f"),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0 - 1, "value": -1},
            "network": [">=Cancun"],
            "result": {},
            "expect_exception": {
                ">=Frontier": "TransactionException.INSUFFICIENT_ACCOUNT_FUNDS"
            },
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {},
            "expect_exception": {
                ">=Frontier": "TransactionException.INSUFFICIENT_ACCOUNT_FUNDS|TransactionException.INTRINSIC_GAS_TOO_LOW"  # noqa: E501
            },
        },
        {
            "indexes": {"data": 1, "gas": 1, "value": -1},
            "network": [">=Cancun"],
            "result": {},
            "expect_exception": {
                ">=Frontier": "TransactionException.INSUFFICIENT_ACCOUNT_FUNDS"
            },
        },
        {
            "indexes": {"data": 0 - 1, "gas": 2, "value": 1},
            "network": [">=Cancun"],
            "result": {},
            "expect_exception": {
                ">=Frontier": "TransactionException.INSUFFICIENT_ACCOUNT_FUNDS|TransactionException.INTRINSIC_GAS_TOO_LOW"  # noqa: E501
            },
        },
        {
            "indexes": {"data": 0 - 1, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {},
            "expect_exception": {
                ">=Frontier": "TransactionException.INTRINSIC_GAS_TOO_LOW"
            },
        },
        {
            "indexes": {"data": 2, "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {},
            "expect_exception": {
                ">=Cancun": "TransactionException.INSUFFICIENT_ACCOUNT_FUNDS|TransactionException.INTRINSIC_GAS_TOO_LOW",  # noqa: E501
                "<Berlin": "TransactionException.TYPE_NOT_SUPPORTED",
            },
        },
        {
            "indexes": {"data": 2, "gas": 1, "value": -1},
            "network": [">=Cancun"],
            "result": {},
            "expect_exception": {
                ">=Cancun": "TransactionException.INSUFFICIENT_ACCOUNT_FUNDS",
                "<Berlin": "TransactionException.TYPE_NOT_SUPPORTED",
            },
        },
        {
            "indexes": {"data": 3, "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {},
            "expect_exception": {
                ">=Cancun": "TransactionException.INSUFFICIENT_ACCOUNT_FUNDS|TransactionException.INTRINSIC_GAS_TOO_LOW",  # noqa: E501
                "<Berlin": "TransactionException.TYPE_NOT_SUPPORTED",
            },
        },
        {
            "indexes": {"data": 3, "gas": 1, "value": -1},
            "network": [">=Cancun"],
            "result": {},
            "expect_exception": {
                ">=Cancun": "TransactionException.INSUFFICIENT_ACCOUNT_FUNDS",
                "<Berlin": "TransactionException.TYPE_NOT_SUPPORTED",
            },
        },
        {
            "indexes": {"data": 4, "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {},
            "expect_exception": {
                ">=Cancun": "TransactionException.INSUFFICIENT_ACCOUNT_FUNDS|TransactionException.INTRINSIC_GAS_TOO_LOW",  # noqa: E501
                "<Berlin": "TransactionException.TYPE_NOT_SUPPORTED",
            },
        },
        {
            "indexes": {"data": 4, "gas": 1, "value": -1},
            "network": [">=Cancun"],
            "result": {},
            "expect_exception": {
                ">=Cancun": "TransactionException.INSUFFICIENT_ACCOUNT_FUNDS",
                "<Berlin": "TransactionException.TYPE_NOT_SUPPORTED",
            },
        },
        {
            "indexes": {"data": 2 - 4, "gas": 2, "value": 1},
            "network": [">=Cancun"],
            "result": {},
            "expect_exception": {
                ">=Cancun": "TransactionException.INSUFFICIENT_ACCOUNT_FUNDS|TransactionException.INTRINSIC_GAS_TOO_LOW",  # noqa: E501
                "<Berlin": "TransactionException.TYPE_NOT_SUPPORTED",
            },
        },
        {
            "indexes": {"data": 2 - 4, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {},
            "expect_exception": {
                ">=Cancun": "TransactionException.INTRINSIC_GAS_TOO_LOW",
                "<Berlin": "TransactionException.TYPE_NOT_SUPPORTED",
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=contract,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        gas_price=100,
        value=TX_VALUE[v],
        access_list=tx_access_list,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
