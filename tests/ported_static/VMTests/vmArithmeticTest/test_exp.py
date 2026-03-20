"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
tests/static/state_tests/VMTests/vmArithmeticTest/expFiller.yml
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
    "693c61390000000000000000000000000000000000000000000000000000000000000000",
    "693c61390000000000000000000000000000000000000000000000000000000000000001",
    "693c61390000000000000000000000000000000000000000000000000000000000000002",
    "693c61390000000000000000000000000000000000000000000000000000000000000003",
    "693c61390000000000000000000000000000000000000000000000000000000000000004",
    "693c61390000000000000000000000000000000000000000000000000000000000000005",
    "693c61390000000000000000000000000000000000000000000000000000000000000006",
    "693c61390000000000000000000000000000000000000000000000000000000000000007",
    "693c61390000000000000000000000000000000000000000000000000000000000000008",
    "693c61390000000000000000000000000000000000000000000000000000000000000009",
    "693c6139000000000000000000000000000000000000000000000000000000000000000a",
]

TX_GAS = [16777216]

TX_VALUE = [1]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    ["tests/static/state_tests/VMTests/vmArithmeticTest/expFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(8, 0, 0, id="case0"),
        pytest.param(3, 0, 0, id="case1"),
        pytest.param(6, 0, 0, id="case2"),
        pytest.param(5, 0, 0, id="case3"),
        pytest.param(10, 0, 0, id="case4"),
        pytest.param(7, 0, 0, id="case5"),
        pytest.param(0, 0, 0, id="case6"),
        pytest.param(9, 0, 0, id="case7"),
        pytest.param(4, 0, 0, id="case8"),
        pytest.param(2, 0, 0, id="case9"),
        pytest.param(1, 0, 0, id="case10"),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_exp(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Ori Pomerantz qbzzt1@gmail.com."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    callee = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.EXP(0x2, 0x2)) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001000"),  # noqa: E501
    )
    callee_1 = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.EXP(
                    0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                    0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE,  # noqa: E501
                ),
            )
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001001"),  # noqa: E501
    )
    callee_2 = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=Op.EXP(0x7FFFFFFF, 0x7FFFFFFF)) + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001002"),  # noqa: E501
    )
    callee_3 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.EXP(0x0, 0x7FFFFFFF)) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001003"),  # noqa: E501
    )
    callee_4 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.EXP(0x7FFFFFFF, 0x0)) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001004"),  # noqa: E501
    )
    callee_5 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.EXP(0x101, 0x1)) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001005"),  # noqa: E501
    )
    callee_6 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.EXP(0x1, 0x101)) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001006"),  # noqa: E501
    )
    callee_7 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.EXP(0x2, 0x101)) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001007"),  # noqa: E501
    )
    # Source: LLL
    # {  ; 0^0 (that is 1 in evm arithmetic)
    #    [[0]] (exp 0 0)
    # }
    callee_8 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.EXP(0x0, 0x0)) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001008"),  # noqa: E501
    )
    # Source: LLL
    # {  ; 2^big = 0
    #    [[0]] (exp 2 0x0100000000000f)
    # }
    callee_9 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.EXP(0x2, 0x100000000000F)) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001009"),  # noqa: E501
    )
    # Source: LLL
    # {  ; 2^15 = 0x8000
    #    [[0]] (exp 2 15)
    # }
    callee_10 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.EXP(0x2, 0xF)) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x000000000000000000000000000000000000100a"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xBA1A9CE0BA1A9CE)
    # Source: LLL
    # {
    #     (call 0xffffff (+ 0x1000 $4) 0 0 0 0 0)
    # }
    contract = pre.deploy_contract(
        code=(
            Op.CALL(
                gas=0xFFFFFF,
                address=Op.ADD(0x1000, Op.CALLDATALOAD(offset=0x4)),
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0xcccccccccccccccccccccccccccccccccccccccc"),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 8, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("600260020a60005500")),
                callee_1: Account(
                    code=bytes.fromhex(
                        "7ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff0a60005500"  # noqa: E501
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex("637fffffff637fffffff0a60005500")
                ),
                callee_3: Account(
                    code=bytes.fromhex("637fffffff60000a60005500")
                ),
                callee_4: Account(
                    code=bytes.fromhex("6000637fffffff0a60005500")
                ),
                callee_5: Account(code=bytes.fromhex("60016101010a60005500")),
                callee_6: Account(code=bytes.fromhex("61010160010a60005500")),
                callee_7: Account(code=bytes.fromhex("61010160020a60005500")),
                callee_8: Account(
                    storage={0: 1}, code=bytes.fromhex("600060000a60005500")
                ),
                callee_9: Account(
                    code=bytes.fromhex("660100000000000f60020a60005500")
                ),
                callee_10: Account(code=bytes.fromhex("600f60020a60005500")),
                contract: Account(
                    code=bytes.fromhex(
                        "600060006000600060006004356110000162fffffff100"
                    )
                ),
            },
        },
        {
            "indexes": {"data": 3, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("600260020a60005500")),
                callee_1: Account(
                    code=bytes.fromhex(
                        "7ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff0a60005500"  # noqa: E501
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex("637fffffff637fffffff0a60005500")
                ),
                callee_3: Account(
                    code=bytes.fromhex("637fffffff60000a60005500")
                ),
                callee_4: Account(
                    code=bytes.fromhex("6000637fffffff0a60005500")
                ),
                callee_5: Account(code=bytes.fromhex("60016101010a60005500")),
                callee_6: Account(code=bytes.fromhex("61010160010a60005500")),
                callee_7: Account(code=bytes.fromhex("61010160020a60005500")),
                callee_8: Account(code=bytes.fromhex("600060000a60005500")),
                callee_9: Account(
                    code=bytes.fromhex("660100000000000f60020a60005500")
                ),
                callee_10: Account(code=bytes.fromhex("600f60020a60005500")),
                contract: Account(
                    code=bytes.fromhex(
                        "600060006000600060006004356110000162fffffff100"
                    )
                ),
            },
        },
        {
            "indexes": {"data": 6, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("600260020a60005500")),
                callee_1: Account(
                    code=bytes.fromhex(
                        "7ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff0a60005500"  # noqa: E501
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex("637fffffff637fffffff0a60005500")
                ),
                callee_3: Account(
                    code=bytes.fromhex("637fffffff60000a60005500")
                ),
                callee_4: Account(
                    code=bytes.fromhex("6000637fffffff0a60005500")
                ),
                callee_5: Account(code=bytes.fromhex("60016101010a60005500")),
                callee_6: Account(
                    storage={0: 1}, code=bytes.fromhex("61010160010a60005500")
                ),
                callee_7: Account(code=bytes.fromhex("61010160020a60005500")),
                callee_8: Account(code=bytes.fromhex("600060000a60005500")),
                callee_9: Account(
                    code=bytes.fromhex("660100000000000f60020a60005500")
                ),
                callee_10: Account(code=bytes.fromhex("600f60020a60005500")),
                contract: Account(
                    code=bytes.fromhex(
                        "600060006000600060006004356110000162fffffff100"
                    )
                ),
            },
        },
        {
            "indexes": {"data": 5, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("600260020a60005500")),
                callee_1: Account(
                    code=bytes.fromhex(
                        "7ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff0a60005500"  # noqa: E501
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex("637fffffff637fffffff0a60005500")
                ),
                callee_3: Account(
                    code=bytes.fromhex("637fffffff60000a60005500")
                ),
                callee_4: Account(
                    code=bytes.fromhex("6000637fffffff0a60005500")
                ),
                callee_5: Account(
                    storage={0: 257},
                    code=bytes.fromhex("60016101010a60005500"),
                ),
                callee_6: Account(code=bytes.fromhex("61010160010a60005500")),
                callee_7: Account(code=bytes.fromhex("61010160020a60005500")),
                callee_8: Account(code=bytes.fromhex("600060000a60005500")),
                callee_9: Account(
                    code=bytes.fromhex("660100000000000f60020a60005500")
                ),
                callee_10: Account(code=bytes.fromhex("600f60020a60005500")),
                contract: Account(
                    code=bytes.fromhex(
                        "600060006000600060006004356110000162fffffff100"
                    )
                ),
            },
        },
        {
            "indexes": {"data": 10, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("600260020a60005500")),
                callee_1: Account(
                    code=bytes.fromhex(
                        "7ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff0a60005500"  # noqa: E501
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex("637fffffff637fffffff0a60005500")
                ),
                callee_3: Account(
                    code=bytes.fromhex("637fffffff60000a60005500")
                ),
                callee_4: Account(
                    code=bytes.fromhex("6000637fffffff0a60005500")
                ),
                callee_5: Account(code=bytes.fromhex("60016101010a60005500")),
                callee_6: Account(code=bytes.fromhex("61010160010a60005500")),
                callee_7: Account(code=bytes.fromhex("61010160020a60005500")),
                callee_8: Account(code=bytes.fromhex("600060000a60005500")),
                callee_9: Account(
                    code=bytes.fromhex("660100000000000f60020a60005500")
                ),
                callee_10: Account(
                    storage={0: 32768},
                    code=bytes.fromhex("600f60020a60005500"),
                ),
                contract: Account(
                    code=bytes.fromhex(
                        "600060006000600060006004356110000162fffffff100"
                    )
                ),
            },
        },
        {
            "indexes": {"data": 7, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("600260020a60005500")),
                callee_1: Account(
                    code=bytes.fromhex(
                        "7ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff0a60005500"  # noqa: E501
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex("637fffffff637fffffff0a60005500")
                ),
                callee_3: Account(
                    code=bytes.fromhex("637fffffff60000a60005500")
                ),
                callee_4: Account(
                    code=bytes.fromhex("6000637fffffff0a60005500")
                ),
                callee_5: Account(code=bytes.fromhex("60016101010a60005500")),
                callee_6: Account(code=bytes.fromhex("61010160010a60005500")),
                callee_7: Account(code=bytes.fromhex("61010160020a60005500")),
                callee_8: Account(code=bytes.fromhex("600060000a60005500")),
                callee_9: Account(
                    code=bytes.fromhex("660100000000000f60020a60005500")
                ),
                callee_10: Account(code=bytes.fromhex("600f60020a60005500")),
                contract: Account(
                    code=bytes.fromhex(
                        "600060006000600060006004356110000162fffffff100"
                    )
                ),
            },
        },
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    storage={0: 4}, code=bytes.fromhex("600260020a60005500")
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "7ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff0a60005500"  # noqa: E501
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex("637fffffff637fffffff0a60005500")
                ),
                callee_3: Account(
                    code=bytes.fromhex("637fffffff60000a60005500")
                ),
                callee_4: Account(
                    code=bytes.fromhex("6000637fffffff0a60005500")
                ),
                callee_5: Account(code=bytes.fromhex("60016101010a60005500")),
                callee_6: Account(code=bytes.fromhex("61010160010a60005500")),
                callee_7: Account(code=bytes.fromhex("61010160020a60005500")),
                callee_8: Account(code=bytes.fromhex("600060000a60005500")),
                callee_9: Account(
                    code=bytes.fromhex("660100000000000f60020a60005500")
                ),
                callee_10: Account(code=bytes.fromhex("600f60020a60005500")),
                contract: Account(
                    code=bytes.fromhex(
                        "600060006000600060006004356110000162fffffff100"
                    )
                ),
            },
        },
        {
            "indexes": {"data": 9, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("600260020a60005500")),
                callee_1: Account(
                    code=bytes.fromhex(
                        "7ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff0a60005500"  # noqa: E501
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex("637fffffff637fffffff0a60005500")
                ),
                callee_3: Account(
                    code=bytes.fromhex("637fffffff60000a60005500")
                ),
                callee_4: Account(
                    code=bytes.fromhex("6000637fffffff0a60005500")
                ),
                callee_5: Account(code=bytes.fromhex("60016101010a60005500")),
                callee_6: Account(code=bytes.fromhex("61010160010a60005500")),
                callee_7: Account(code=bytes.fromhex("61010160020a60005500")),
                callee_8: Account(code=bytes.fromhex("600060000a60005500")),
                callee_9: Account(
                    code=bytes.fromhex("660100000000000f60020a60005500")
                ),
                callee_10: Account(code=bytes.fromhex("600f60020a60005500")),
                contract: Account(
                    code=bytes.fromhex(
                        "600060006000600060006004356110000162fffffff100"
                    )
                ),
            },
        },
        {
            "indexes": {"data": 4, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("600260020a60005500")),
                callee_1: Account(
                    code=bytes.fromhex(
                        "7ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff0a60005500"  # noqa: E501
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex("637fffffff637fffffff0a60005500")
                ),
                callee_3: Account(
                    code=bytes.fromhex("637fffffff60000a60005500")
                ),
                callee_4: Account(
                    storage={0: 1},
                    code=bytes.fromhex("6000637fffffff0a60005500"),
                ),
                callee_5: Account(code=bytes.fromhex("60016101010a60005500")),
                callee_6: Account(code=bytes.fromhex("61010160010a60005500")),
                callee_7: Account(code=bytes.fromhex("61010160020a60005500")),
                callee_8: Account(code=bytes.fromhex("600060000a60005500")),
                callee_9: Account(
                    code=bytes.fromhex("660100000000000f60020a60005500")
                ),
                callee_10: Account(code=bytes.fromhex("600f60020a60005500")),
                contract: Account(
                    code=bytes.fromhex(
                        "600060006000600060006004356110000162fffffff100"
                    )
                ),
            },
        },
        {
            "indexes": {"data": 2, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("600260020a60005500")),
                callee_1: Account(
                    code=bytes.fromhex(
                        "7ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff0a60005500"  # noqa: E501
                    )
                ),
                callee_2: Account(
                    storage={
                        0: 0xBC8CCCCCCCC888888880000000AAAAAAB00000000FFFFFFFFFFFFFFF7FFFFFFF,  # noqa: E501
                    },
                    code=bytes.fromhex("637fffffff637fffffff0a60005500"),
                ),
                callee_3: Account(
                    code=bytes.fromhex("637fffffff60000a60005500")
                ),
                callee_4: Account(
                    code=bytes.fromhex("6000637fffffff0a60005500")
                ),
                callee_5: Account(code=bytes.fromhex("60016101010a60005500")),
                callee_6: Account(code=bytes.fromhex("61010160010a60005500")),
                callee_7: Account(code=bytes.fromhex("61010160020a60005500")),
                callee_8: Account(code=bytes.fromhex("600060000a60005500")),
                callee_9: Account(
                    code=bytes.fromhex("660100000000000f60020a60005500")
                ),
                callee_10: Account(code=bytes.fromhex("600f60020a60005500")),
                contract: Account(
                    code=bytes.fromhex(
                        "600060006000600060006004356110000162fffffff100"
                    )
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("600260020a60005500")),
                callee_1: Account(
                    storage={0: 1},
                    code=bytes.fromhex(
                        "7ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff0a60005500"  # noqa: E501
                    ),
                ),
                callee_2: Account(
                    code=bytes.fromhex("637fffffff637fffffff0a60005500")
                ),
                callee_3: Account(
                    code=bytes.fromhex("637fffffff60000a60005500")
                ),
                callee_4: Account(
                    code=bytes.fromhex("6000637fffffff0a60005500")
                ),
                callee_5: Account(code=bytes.fromhex("60016101010a60005500")),
                callee_6: Account(code=bytes.fromhex("61010160010a60005500")),
                callee_7: Account(code=bytes.fromhex("61010160020a60005500")),
                callee_8: Account(code=bytes.fromhex("600060000a60005500")),
                callee_9: Account(
                    code=bytes.fromhex("660100000000000f60020a60005500")
                ),
                callee_10: Account(code=bytes.fromhex("600f60020a60005500")),
                contract: Account(
                    code=bytes.fromhex(
                        "600060006000600060006004356110000162fffffff100"
                    )
                ),
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
