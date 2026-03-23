"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
tests/static/state_tests/VMTests/vmLogTest/log0Filler.yml
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
    "693c6139000000000000000000000000000000000000000000000000000000000000000a",
]

TX_GAS = [16777216]

TX_VALUE = [1]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    ["tests/static/state_tests/VMTests/vmLogTest/log0Filler.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(0, 0, 0, id="case0"),
        pytest.param(7, 0, 0, id="case1"),
        pytest.param(5, 0, 0, id="case2"),
        pytest.param(6, 0, 0, id="case3"),
        pytest.param(2, 0, 0, id="case4"),
        pytest.param(3, 0, 0, id="case5"),
        pytest.param(1, 0, 0, id="case6"),
        pytest.param(4, 0, 0, id="case7"),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_log0(
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
        code=(
            Op.LOG0(offset=0x0, size=0x0)
            + Op.SSTORE(key=0x0, value=0x600D)
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001000"),  # noqa: E501
    )
    callee_1 = pre.deploy_contract(
        code=(
            Op.MSTORE(
                offset=0x0,
                value=0xAABBFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFCCDD,  # noqa: E501
            )
            + Op.LOG0(
                offset=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                size=0x1,
            )
            + Op.SSTORE(key=0x0, value=0x600D)
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001001"),  # noqa: E501
    )
    callee_2 = pre.deploy_contract(
        code=(
            Op.MSTORE(
                offset=0x0,
                value=0xAABBFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFCCDD,  # noqa: E501
            )
            + Op.LOG0(
                offset=0x1,
                size=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
            )
            + Op.SSTORE(key=0x0, value=0x600D)
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001002"),  # noqa: E501
    )
    callee_3 = pre.deploy_contract(
        code=(
            Op.MSTORE(
                offset=0x0,
                value=0xAABBFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFCCDD,  # noqa: E501
            )
            + Op.LOG0(offset=0x1, size=0x0)
            + Op.SSTORE(key=0x0, value=0x600D)
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001003"),  # noqa: E501
    )
    callee_4 = pre.deploy_contract(
        code=(
            Op.MSTORE(
                offset=0x0,
                value=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
            )
            + Op.LOG0(offset=0x0, size=0x20)
            + Op.SSTORE(key=0x0, value=0x600D)
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001004"),  # noqa: E501
    )
    callee_5 = pre.deploy_contract(
        code=(
            Op.MSTORE(
                offset=0x0,
                value=0xAABBFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFCCDD,  # noqa: E501
            )
            + Op.LOG0(offset=0x0, size=0x1)
            + Op.SSTORE(key=0x0, value=0x600D)
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001005"),  # noqa: E501
    )
    callee_6 = pre.deploy_contract(
        code=(
            Op.MSTORE(
                offset=0x0,
                value=0xAABBFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFCCDD,  # noqa: E501
            )
            + Op.LOG0(offset=0x1F, size=0x1)
            + Op.SSTORE(key=0x0, value=0x600D)
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001006"),  # noqa: E501
    )
    # Source: LLL
    # {        ; logTwice
    #    [0] 0xaabbffffffffffffffffffffffffffffffffffffffffffffffffffffffffccdd
    #    (log0 0 32)
    #    (log0 2 16)
    #    [[0]] 0x600D
    # }
    callee_7 = pre.deploy_contract(
        code=(
            Op.MSTORE(
                offset=0x0,
                value=0xAABBFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFCCDD,  # noqa: E501
            )
            + Op.LOG0(offset=0x0, size=0x20)
            + Op.LOG0(offset=0x2, size=0x10)
            + Op.SSTORE(key=0x0, value=0x600D)
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x000000000000000000000000000000000000100a"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x100000000000)
    # Source: LLL
    # {
    #     (delegatecall (gas) (+ 0x1000 $4) 0 0 0 0)
    # }
    contract = pre.deploy_contract(
        code=(
            Op.DELEGATECALL(
                gas=Op.GAS,
                address=Op.ADD(0x1000, Op.CALLDATALOAD(offset=0x4)),
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        storage={0x0: 0xBAD},
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0xcccccccccccccccccccccccccccccccccccccccc"),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("60006000a061600d60005500")
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "7faabbffffffffffffffffffffffffffffffffffffffffffffffffffffffffccdd60005260017fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffa061600d60005500"  # noqa: E501
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "7faabbffffffffffffffffffffffffffffffffffffffffffffffffffffffffccdd6000527fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff6001a061600d60005500"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "7faabbffffffffffffffffffffffffffffffffffffffffffffffffffffffffccdd60005260006001a061600d60005500"  # noqa: E501
                    )
                ),
                callee_4: Account(
                    code=bytes.fromhex(
                        "7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff60005260206000a061600d60005500"  # noqa: E501
                    )
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "7faabbffffffffffffffffffffffffffffffffffffffffffffffffffffffffccdd60005260016000a061600d60005500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "7faabbffffffffffffffffffffffffffffffffffffffffffffffffffffffffccdd6000526001601fa061600d60005500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "7faabbffffffffffffffffffffffffffffffffffffffffffffffffffffffffccdd60005260206000a060106002a061600d60005500"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 24589},
                    code=bytes.fromhex("6000600060006000600435611000015af400"),
                ),
            },
        },
        {
            "indexes": {"data": 7, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("60006000a061600d60005500")
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "7faabbffffffffffffffffffffffffffffffffffffffffffffffffffffffffccdd60005260017fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffa061600d60005500"  # noqa: E501
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "7faabbffffffffffffffffffffffffffffffffffffffffffffffffffffffffccdd6000527fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff6001a061600d60005500"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "7faabbffffffffffffffffffffffffffffffffffffffffffffffffffffffffccdd60005260006001a061600d60005500"  # noqa: E501
                    )
                ),
                callee_4: Account(
                    code=bytes.fromhex(
                        "7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff60005260206000a061600d60005500"  # noqa: E501
                    )
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "7faabbffffffffffffffffffffffffffffffffffffffffffffffffffffffffccdd60005260016000a061600d60005500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "7faabbffffffffffffffffffffffffffffffffffffffffffffffffffffffffccdd6000526001601fa061600d60005500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "7faabbffffffffffffffffffffffffffffffffffffffffffffffffffffffffccdd60005260206000a060106002a061600d60005500"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 24589},
                    code=bytes.fromhex("6000600060006000600435611000015af400"),
                ),
            },
        },
        {
            "indexes": {"data": 5, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("60006000a061600d60005500")
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "7faabbffffffffffffffffffffffffffffffffffffffffffffffffffffffffccdd60005260017fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffa061600d60005500"  # noqa: E501
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "7faabbffffffffffffffffffffffffffffffffffffffffffffffffffffffffccdd6000527fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff6001a061600d60005500"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "7faabbffffffffffffffffffffffffffffffffffffffffffffffffffffffffccdd60005260006001a061600d60005500"  # noqa: E501
                    )
                ),
                callee_4: Account(
                    code=bytes.fromhex(
                        "7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff60005260206000a061600d60005500"  # noqa: E501
                    )
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "7faabbffffffffffffffffffffffffffffffffffffffffffffffffffffffffccdd60005260016000a061600d60005500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "7faabbffffffffffffffffffffffffffffffffffffffffffffffffffffffffccdd6000526001601fa061600d60005500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "7faabbffffffffffffffffffffffffffffffffffffffffffffffffffffffffccdd60005260206000a060106002a061600d60005500"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 24589},
                    code=bytes.fromhex("6000600060006000600435611000015af400"),
                ),
            },
        },
        {
            "indexes": {"data": 6, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("60006000a061600d60005500")
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "7faabbffffffffffffffffffffffffffffffffffffffffffffffffffffffffccdd60005260017fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffa061600d60005500"  # noqa: E501
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "7faabbffffffffffffffffffffffffffffffffffffffffffffffffffffffffccdd6000527fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff6001a061600d60005500"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "7faabbffffffffffffffffffffffffffffffffffffffffffffffffffffffffccdd60005260006001a061600d60005500"  # noqa: E501
                    )
                ),
                callee_4: Account(
                    code=bytes.fromhex(
                        "7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff60005260206000a061600d60005500"  # noqa: E501
                    )
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "7faabbffffffffffffffffffffffffffffffffffffffffffffffffffffffffccdd60005260016000a061600d60005500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "7faabbffffffffffffffffffffffffffffffffffffffffffffffffffffffffccdd6000526001601fa061600d60005500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "7faabbffffffffffffffffffffffffffffffffffffffffffffffffffffffffccdd60005260206000a060106002a061600d60005500"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 24589},
                    code=bytes.fromhex("6000600060006000600435611000015af400"),
                ),
            },
        },
        {
            "indexes": {"data": 2, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("60006000a061600d60005500")
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "7faabbffffffffffffffffffffffffffffffffffffffffffffffffffffffffccdd60005260017fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffa061600d60005500"  # noqa: E501
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "7faabbffffffffffffffffffffffffffffffffffffffffffffffffffffffffccdd6000527fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff6001a061600d60005500"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "7faabbffffffffffffffffffffffffffffffffffffffffffffffffffffffffccdd60005260006001a061600d60005500"  # noqa: E501
                    )
                ),
                callee_4: Account(
                    code=bytes.fromhex(
                        "7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff60005260206000a061600d60005500"  # noqa: E501
                    )
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "7faabbffffffffffffffffffffffffffffffffffffffffffffffffffffffffccdd60005260016000a061600d60005500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "7faabbffffffffffffffffffffffffffffffffffffffffffffffffffffffffccdd6000526001601fa061600d60005500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "7faabbffffffffffffffffffffffffffffffffffffffffffffffffffffffffccdd60005260206000a060106002a061600d60005500"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 2989},
                    code=bytes.fromhex("6000600060006000600435611000015af400"),
                ),
            },
        },
        {
            "indexes": {"data": 3, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("60006000a061600d60005500")
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "7faabbffffffffffffffffffffffffffffffffffffffffffffffffffffffffccdd60005260017fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffa061600d60005500"  # noqa: E501
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "7faabbffffffffffffffffffffffffffffffffffffffffffffffffffffffffccdd6000527fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff6001a061600d60005500"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "7faabbffffffffffffffffffffffffffffffffffffffffffffffffffffffffccdd60005260006001a061600d60005500"  # noqa: E501
                    )
                ),
                callee_4: Account(
                    code=bytes.fromhex(
                        "7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff60005260206000a061600d60005500"  # noqa: E501
                    )
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "7faabbffffffffffffffffffffffffffffffffffffffffffffffffffffffffccdd60005260016000a061600d60005500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "7faabbffffffffffffffffffffffffffffffffffffffffffffffffffffffffccdd6000526001601fa061600d60005500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "7faabbffffffffffffffffffffffffffffffffffffffffffffffffffffffffccdd60005260206000a060106002a061600d60005500"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 24589},
                    code=bytes.fromhex("6000600060006000600435611000015af400"),
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("60006000a061600d60005500")
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "7faabbffffffffffffffffffffffffffffffffffffffffffffffffffffffffccdd60005260017fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffa061600d60005500"  # noqa: E501
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "7faabbffffffffffffffffffffffffffffffffffffffffffffffffffffffffccdd6000527fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff6001a061600d60005500"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "7faabbffffffffffffffffffffffffffffffffffffffffffffffffffffffffccdd60005260006001a061600d60005500"  # noqa: E501
                    )
                ),
                callee_4: Account(
                    code=bytes.fromhex(
                        "7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff60005260206000a061600d60005500"  # noqa: E501
                    )
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "7faabbffffffffffffffffffffffffffffffffffffffffffffffffffffffffccdd60005260016000a061600d60005500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "7faabbffffffffffffffffffffffffffffffffffffffffffffffffffffffffccdd6000526001601fa061600d60005500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "7faabbffffffffffffffffffffffffffffffffffffffffffffffffffffffffccdd60005260206000a060106002a061600d60005500"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 2989},
                    code=bytes.fromhex("6000600060006000600435611000015af400"),
                ),
            },
        },
        {
            "indexes": {"data": 4, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("60006000a061600d60005500")
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "7faabbffffffffffffffffffffffffffffffffffffffffffffffffffffffffccdd60005260017fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffa061600d60005500"  # noqa: E501
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "7faabbffffffffffffffffffffffffffffffffffffffffffffffffffffffffccdd6000527fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff6001a061600d60005500"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "7faabbffffffffffffffffffffffffffffffffffffffffffffffffffffffffccdd60005260006001a061600d60005500"  # noqa: E501
                    )
                ),
                callee_4: Account(
                    code=bytes.fromhex(
                        "7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff60005260206000a061600d60005500"  # noqa: E501
                    )
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "7faabbffffffffffffffffffffffffffffffffffffffffffffffffffffffffccdd60005260016000a061600d60005500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "7faabbffffffffffffffffffffffffffffffffffffffffffffffffffffffffccdd6000526001601fa061600d60005500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "7faabbffffffffffffffffffffffffffffffffffffffffffffffffffffffffccdd60005260206000a060106002a061600d60005500"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 24589},
                    code=bytes.fromhex("6000600060006000600435611000015af400"),
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
