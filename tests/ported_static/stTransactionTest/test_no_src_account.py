"""
Test_no_src_account.

Ported from:
state_tests/stTransactionTest/NoSrcAccountFiller.yml
"""

import pytest
from execution_testing import (
    AccessList,
    Address,
    Alloc,
    Bytes,
    Environment,
    Hash,
    StateTestFiller,
    Transaction,
    TransactionException,
)
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stTransactionTest/NoSrcAccountFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="d0-g0-v0",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            0,
            0,
            1,
            id="d0-g0-v1",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            0,
            1,
            0,
            id="d0-g1-v0",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            0,
            1,
            1,
            id="d0-g1-v1",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            0,
            2,
            0,
            id="d0-g2-v0",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            0,
            2,
            1,
            id="d0-g2-v1",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            1,
            0,
            0,
            id="d1-g0-v0",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            1,
            0,
            1,
            id="d1-g0-v1",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            1,
            1,
            0,
            id="d1-g1-v0",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            1,
            1,
            1,
            id="d1-g1-v1",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            1,
            2,
            0,
            id="d1-g2-v0",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            1,
            2,
            1,
            id="d1-g2-v1",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            2,
            0,
            0,
            id="d2-g0-v0",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            2,
            0,
            1,
            id="d2-g0-v1",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            2,
            1,
            0,
            id="d2-g1-v0",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            2,
            1,
            1,
            id="d2-g1-v1",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            2,
            2,
            0,
            id="d2-g2-v0",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            2,
            2,
            1,
            id="d2-g2-v1",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            3,
            0,
            0,
            id="d3-g0-v0",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            3,
            0,
            1,
            id="d3-g0-v1",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            3,
            1,
            0,
            id="d3-g1-v0",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            3,
            1,
            1,
            id="d3-g1-v1",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            3,
            2,
            0,
            id="d3-g2-v0",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            3,
            2,
            1,
            id="d3-g2-v1",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            4,
            0,
            0,
            id="d4-g0-v0",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            4,
            0,
            1,
            id="d4-g0-v1",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            4,
            1,
            0,
            id="d4-g1-v0",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            4,
            1,
            1,
            id="d4-g1-v1",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            4,
            2,
            0,
            id="d4-g2-v0",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            4,
            2,
            1,
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
    """Test_no_src_account."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=89128960,
    )

    # Source: raw
    # 0x00
    target = pre.deploy_contract(  # noqa: F841
        code=Op.STOP,
        nonce=0,
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": [0, 1], "value": -1},
            "network": [">=Cancun"],
            "result": {},
            "expect_exception": {
                ">=Frontier": TransactionException.INSUFFICIENT_ACCOUNT_FUNDS
            },
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {},
            "expect_exception": {
                ">=Frontier": [
                    TransactionException.INSUFFICIENT_ACCOUNT_FUNDS,
                    TransactionException.INTRINSIC_GAS_TOO_LOW,
                ]
            },
        },
        {
            "indexes": {"data": 1, "gas": 1, "value": -1},
            "network": [">=Cancun"],
            "result": {},
            "expect_exception": {
                ">=Frontier": TransactionException.INSUFFICIENT_ACCOUNT_FUNDS
            },
        },
        {
            "indexes": {"data": [0, 1], "gas": 2, "value": 1},
            "network": [">=Cancun"],
            "result": {},
            "expect_exception": {
                ">=Frontier": [
                    TransactionException.INSUFFICIENT_ACCOUNT_FUNDS,
                    TransactionException.INTRINSIC_GAS_TOO_LOW,
                ]
            },
        },
        {
            "indexes": {"data": [0, 1], "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {},
            "expect_exception": {
                ">=Frontier": TransactionException.INTRINSIC_GAS_TOO_LOW
            },
        },
        {
            "indexes": {"data": 2, "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {},
            "expect_exception": {
                ">=Cancun": [
                    TransactionException.INSUFFICIENT_ACCOUNT_FUNDS,
                    TransactionException.INTRINSIC_GAS_TOO_LOW,
                ],
                ">=Frontier<MuirGlacier": TransactionException.TYPE_NOT_SUPPORTED,  # noqa: E501
            },
        },
        {
            "indexes": {"data": 2, "gas": 1, "value": -1},
            "network": [">=Cancun"],
            "result": {},
            "expect_exception": {
                ">=Cancun": TransactionException.INSUFFICIENT_ACCOUNT_FUNDS,
                ">=Frontier<MuirGlacier": TransactionException.TYPE_NOT_SUPPORTED,  # noqa: E501
            },
        },
        {
            "indexes": {"data": 3, "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {},
            "expect_exception": {
                ">=Cancun": [
                    TransactionException.INSUFFICIENT_ACCOUNT_FUNDS,
                    TransactionException.INTRINSIC_GAS_TOO_LOW,
                ],
                ">=Frontier<MuirGlacier": TransactionException.TYPE_NOT_SUPPORTED,  # noqa: E501
            },
        },
        {
            "indexes": {"data": 3, "gas": 1, "value": -1},
            "network": [">=Cancun"],
            "result": {},
            "expect_exception": {
                ">=Cancun": TransactionException.INSUFFICIENT_ACCOUNT_FUNDS,
                ">=Frontier<MuirGlacier": TransactionException.TYPE_NOT_SUPPORTED,  # noqa: E501
            },
        },
        {
            "indexes": {"data": 4, "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {},
            "expect_exception": {
                ">=Cancun": [
                    TransactionException.INSUFFICIENT_ACCOUNT_FUNDS,
                    TransactionException.INTRINSIC_GAS_TOO_LOW,
                ],
                ">=Frontier<MuirGlacier": TransactionException.TYPE_NOT_SUPPORTED,  # noqa: E501
            },
        },
        {
            "indexes": {"data": 4, "gas": 1, "value": -1},
            "network": [">=Cancun"],
            "result": {},
            "expect_exception": {
                ">=Cancun": TransactionException.INSUFFICIENT_ACCOUNT_FUNDS,
                ">=Frontier<MuirGlacier": TransactionException.TYPE_NOT_SUPPORTED,  # noqa: E501
            },
        },
        {
            "indexes": {"data": [2, 3, 4], "gas": 2, "value": 1},
            "network": [">=Cancun"],
            "result": {},
            "expect_exception": {
                ">=Cancun": [
                    TransactionException.INSUFFICIENT_ACCOUNT_FUNDS,
                    TransactionException.INTRINSIC_GAS_TOO_LOW,
                ],
                ">=Frontier<MuirGlacier": TransactionException.TYPE_NOT_SUPPORTED,  # noqa: E501
            },
        },
        {
            "indexes": {"data": [2, 3, 4], "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {},
            "expect_exception": {
                ">=Cancun": TransactionException.INTRINSIC_GAS_TOO_LOW,
                ">=Frontier<MuirGlacier": TransactionException.TYPE_NOT_SUPPORTED,  # noqa: E501
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Bytes(""),
        Bytes("dead60a7"),
        Bytes("00"),
        Bytes("00"),
        Bytes("00"),
    ]
    tx_gas = [21000, 210000, 0]
    tx_value = [0, 1]
    tx_access_lists: dict[int, list] = {
        2: [],
        3: [
            AccessList(
                address=target,
                storage_keys=[],
            ),
        ],
        4: [
            AccessList(
                address=target,
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000001"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
    }

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
        gas_price=100,
        access_list=tx_access_lists.get(d),
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
