"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stTransactionTest/NoSrcAccountCreate1559Filler.yml
"""

import pytest
from execution_testing import (
    EOA,
    AccessList,
    Account,
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
    [
        "tests/static/state_tests/stTransactionTest/NoSrcAccountCreate1559Filler.yml",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v, tx_access_list",
    [
        pytest.param(
            0, 0, 0, [], id="case0", marks=pytest.mark.exception_test
        ),
        pytest.param(
            0, 0, 1, [], id="case1", marks=pytest.mark.exception_test
        ),
        pytest.param(
            0, 1, 0, [], id="case2", marks=pytest.mark.exception_test
        ),
        pytest.param(
            0, 1, 1, [], id="case3", marks=pytest.mark.exception_test
        ),
        pytest.param(
            0, 2, 0, [], id="case4", marks=pytest.mark.exception_test
        ),
        pytest.param(
            0, 2, 1, [], id="case5", marks=pytest.mark.exception_test
        ),
        pytest.param(
            1,
            0,
            0,
            [
                AccessList(
                    address=Address(
                        "0xd0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0"
                    ),
                    storage_keys=[],
                )
            ],
            id="case6",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            1,
            0,
            1,
            [
                AccessList(
                    address=Address(
                        "0xd0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0"
                    ),
                    storage_keys=[],
                )
            ],
            id="case7",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            1,
            1,
            0,
            [
                AccessList(
                    address=Address(
                        "0xd0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0"
                    ),
                    storage_keys=[],
                )
            ],
            id="case8",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            1,
            1,
            1,
            [
                AccessList(
                    address=Address(
                        "0xd0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0"
                    ),
                    storage_keys=[],
                )
            ],
            id="case9",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            1,
            2,
            0,
            [
                AccessList(
                    address=Address(
                        "0xd0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0"
                    ),
                    storage_keys=[],
                )
            ],
            id="case10",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            1,
            2,
            1,
            [
                AccessList(
                    address=Address(
                        "0xd0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0"
                    ),
                    storage_keys=[],
                )
            ],
            id="case11",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            2,
            0,
            0,
            [
                AccessList(
                    address=Address(
                        "0xd0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0"
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
            id="case12",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            2,
            0,
            1,
            [
                AccessList(
                    address=Address(
                        "0xd0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0"
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
            id="case13",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            2,
            1,
            0,
            [
                AccessList(
                    address=Address(
                        "0xd0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0"
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
            id="case14",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            2,
            1,
            1,
            [
                AccessList(
                    address=Address(
                        "0xd0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0"
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
            id="case15",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            2,
            2,
            0,
            [
                AccessList(
                    address=Address(
                        "0xd0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0"
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
            id="case16",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            2,
            2,
            1,
            [
                AccessList(
                    address=Address(
                        "0xd0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0"
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
            id="case17",
            marks=pytest.mark.exception_test,
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_no_src_account_create1559(
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
    contract = Address("0xc22941800a5a392672dc35d8e088ba1bc90891b1")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=89128960,
    )

    pre[contract] = Account(balance=0, nonce=24743)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": -1, "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {},
            "expect_exception": {
                ">=Cancun": "TransactionException.INSUFFICIENT_ACCOUNT_FUNDS|TransactionException.INTRINSIC_GAS_TOO_LOW",  # noqa: E501
                "<London": "TransactionException.TYPE_NOT_SUPPORTED",
            },
        },
        {
            "indexes": {"data": -1, "gas": 1, "value": -1},
            "network": [">=Cancun"],
            "result": {},
            "expect_exception": {
                ">=Cancun": "TransactionException.INSUFFICIENT_ACCOUNT_FUNDS",
                "<London": "TransactionException.TYPE_NOT_SUPPORTED",
            },
        },
        {
            "indexes": {"data": -1, "gas": 2, "value": 1},
            "network": [">=Cancun"],
            "result": {},
            "expect_exception": {
                ">=Cancun": "TransactionException.INSUFFICIENT_ACCOUNT_FUNDS|TransactionException.INTRINSIC_GAS_TOO_LOW",  # noqa: E501
                "<London": "TransactionException.TYPE_NOT_SUPPORTED",
            },
        },
        {
            "indexes": {"data": -1, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {},
            "expect_exception": {
                ">=Cancun": "TransactionException.INTRINSIC_GAS_TOO_LOW",
                "<London": "TransactionException.TYPE_NOT_SUPPORTED",
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=None,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        max_fee_per_gas=2000,
        max_priority_fee_per_gas=10,
        value=TX_VALUE[v],
        access_list=tx_access_list,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
