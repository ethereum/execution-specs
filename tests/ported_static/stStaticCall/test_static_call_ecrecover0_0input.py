"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stStaticCall/static_CallEcrecover0_0inputFiller.json
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
    resolve_expect_post,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

TX_DATA = [
    "0000000000000000000000000000000000000000000000000000000000000000",
    "0000000000000000000000000000000000000000000000000000000000000001",
    "0000000000000000000000000000000000000000000000000000000000000002",
    "0000000000000000000000000000000000000000000000000000000000000003",
    "0000000000000000000000000000000000000000000000000000000000000004",
    "0000000000000000000000000000000000000000000000000000000000000005",
    "0000000000000000000000000000000000000000000000000000000000000006",
    "0000000000000000000000000000000000000000000000000000000000000007",
    "0000000000000000000000000000000000000000000000000000000000000008",
]

TX_GAS = [3652240]

TX_VALUE = [100000]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stStaticCall/static_CallEcrecover0_0inputFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(0, 0, 0, id="case0"),
        pytest.param(1, 0, 0, id="case1"),
        pytest.param(2, 0, 0, id="case2"),
        pytest.param(3, 0, 0, id="case3"),
        pytest.param(4, 0, 0, id="case4"),
        pytest.param(5, 0, 0, id="case5"),
        pytest.param(6, 0, 0, id="case6"),
        pytest.param(7, 0, 0, id="case7"),
        pytest.param(8, 0, 0, id="case8"),
    ],
)
@pytest.mark.pre_alloc_mutable
@pytest.mark.slow
def test_static_call_ecrecover0_0input(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xE04D1AC7DDDA0C98397D56A0B501E960D4CD325A39286919AC23C1A07009A869
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    # Source: LLL
    # { [[ 2 ]] (STATICCALL 300000 (CALLDATALOAD 0) 0 128 128 32) [[ 0 ]] (MOD (MLOAD 128) (EXP 2 160)) }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x2,
                value=Op.STATICCALL(
                    gas=0x493E0,
                    address=Op.CALLDATALOAD(offset=0x0),
                    args_offset=0x0,
                    args_size=0x80,
                    ret_offset=0x80,
                    ret_size=0x20,
                ),
            )
            + Op.SSTORE(
                key=0x0,
                value=Op.MOD(Op.MLOAD(offset=0x80), Op.EXP(0x2, 0xA0)),
            )
            + Op.STOP
        ),
        balance=0x1312D00,
        nonce=0,
        address=Address("0x1fd04a51ac69c94c58521d30e2defc4856a581b0"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={2: 1},
                    code=bytes.fromhex(
                        "6020608060806000600035620493e0fa60025560a060020a6080510660005500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={2: 1},
                    code=bytes.fromhex(
                        "6020608060806000600035620493e0fa60025560a060020a6080510660005500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 2, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        0: 0x8209944E898F69A7BD10A23C839D341E935FD5CA,
                        2: 1,
                    },
                    code=bytes.fromhex(
                        "6020608060806000600035620493e0fa60025560a060020a6080510660005500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 3, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        0: 0x4300A157335CB7C9FC9423E011D7DD51090D093F,
                        2: 1,
                    },
                    code=bytes.fromhex(
                        "6020608060806000600035620493e0fa60025560a060020a6080510660005500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 4, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={2: 1},
                    code=bytes.fromhex(
                        "6020608060806000600035620493e0fa60025560a060020a6080510660005500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 5, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={2: 1},
                    code=bytes.fromhex(
                        "6020608060806000600035620493e0fa60025560a060020a6080510660005500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 6, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={2: 1},
                    code=bytes.fromhex(
                        "6020608060806000600035620493e0fa60025560a060020a6080510660005500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 7, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={2: 1},
                    code=bytes.fromhex(
                        "6020608060806000600035620493e0fa60025560a060020a6080510660005500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 8, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    code=bytes.fromhex(
                        "6020608060806000600035620493e0fa60025560a060020a6080510660005500"  # noqa: E501
                    )
                )
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=contract,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        value=TX_VALUE[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
