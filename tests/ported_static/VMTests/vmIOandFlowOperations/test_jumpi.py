"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
tests/static/state_tests/VMTests/vmIOandFlowOperations/jumpiFiller.yml
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
    "693c61390000000000000000000000000000000000000000000000000000000000001000",
    "693c61390000000000000000000000000000000000000000000000000000000000001001",
    "693c61390000000000000000000000000000000000000000000000000000000000000200",
    "693c61390000000000000000000000000000000000000000000000000000000000000201",
    "693c61390000000000000000000000000000000000000000000000000000000000001002",
    "693c61390000000000000000000000000000000000000000000000000000000000000202",
    "693c61390000000000000000000000000000000000000000000000000000000000001003",
    "693c61390000000000000000000000000000000000000000000000000000000000000203",
    "693c61390000000000000000000000000000000000000000000000000000000000001004",
    "693c61390000000000000000000000000000000000000000000000000000000000001005",
    "693c61390000000000000000000000000000000000000000000000000000000000001006",
    "693c61390000000000000000000000000000000000000000000000000000000000001007",
    "693c61390000000000000000000000000000000000000000000000000000000000001008",
    "693c61390000000000000000000000000000000000000000000000000000000000000208",
    "693c61390000000000000000000000000000000000000000000000000000000000001009",
    "693c6139000000000000000000000000000000000000000000000000000000000000100a",
    "693c6139000000000000000000000000000000000000000000000000000000000000100b",
    "693c6139000000000000000000000000000000000000000000000000000000000000100c",
    "693c6139000000000000000000000000000000000000000000000000000000000000100d",
    "693c6139000000000000000000000000000000000000000000000000000000000000020d",
    "693c6139000000000000000000000000000000000000000000000000000000000000100e",
    "693c6139000000000000000000000000000000000000000000000000000000000000020e",
    "693c6139000000000000000000000000000000000000000000000000000000000000100f",
    "693c6139000000000000000000000000000000000000000000000000000000000000020f",
    "693c61390000000000000000000000000000000000000000000000000000000000000110",
    "693c61390000000000000000000000000000000000000000000000000000000000000111",
]

TX_GAS = [16777216]

TX_VALUE = [1]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    ["tests/static/state_tests/VMTests/vmIOandFlowOperations/jumpiFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(9, 0, 0, id="case0"),
        pytest.param(15, 0, 0, id="case1"),
        pytest.param(14, 0, 0, id="case2"),
        pytest.param(11, 0, 0, id="case3"),
        pytest.param(10, 0, 0, id="case4"),
        pytest.param(12, 0, 0, id="case5"),
        pytest.param(1, 0, 0, id="case6"),
        pytest.param(6, 0, 0, id="case7"),
        pytest.param(18, 0, 0, id="case8"),
        pytest.param(20, 0, 0, id="case9"),
        pytest.param(22, 0, 0, id="case10"),
        pytest.param(0, 0, 0, id="case11"),
        pytest.param(16, 0, 0, id="case12"),
        pytest.param(17, 0, 0, id="case13"),
        pytest.param(8, 0, 0, id="case14"),
        pytest.param(4, 0, 0, id="case15"),
        pytest.param(24, 0, 0, id="case16"),
        pytest.param(25, 0, 0, id="case17"),
        pytest.param(13, 0, 0, id="case18"),
        pytest.param(3, 0, 0, id="case19"),
        pytest.param(7, 0, 0, id="case20"),
        pytest.param(19, 0, 0, id="case21"),
        pytest.param(21, 0, 0, id="case22"),
        pytest.param(23, 0, 0, id="case23"),
        pytest.param(2, 0, 0, id="case24"),
        pytest.param(5, 0, 0, id="case25"),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_jumpi(
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

    # Source: raw bytecode
    callee = pre.deploy_contract(
        code=(
            Op.JUMPI(pc=0xE, condition=0x1)
            + Op.JUMPDEST
            + Op.JUMPDEST
            + Op.JUMPDEST
            + Op.JUMPDEST
            + Op.JUMPDEST
            + Op.JUMPDEST
            + Op.JUMPDEST
            + Op.JUMPDEST
            + Op.JUMPDEST
            + Op.JUMPDEST
            + Op.JUMPDEST
            + Op.JUMPDEST
            + Op.JUMPDEST
            + Op.JUMPDEST
            + Op.JUMPDEST
            + Op.JUMPDEST
            + Op.SSTORE(key=0x0, value=0x600D)
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000000110"),  # noqa: E501
    )
    # Source: raw bytecode
    callee_1 = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x600D)
            + Op.MSTORE(offset=0x0, value=0x10)
            + Op.JUMPDEST
            + Op.SUB(Op.MLOAD(offset=0x0), 0x1)
            + Op.MSTORE(offset=0x0, value=Op.DUP1)
            + Op.PUSH1[0xB]
            + Op.JUMPI
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000000111"),  # noqa: E501
    )
    callee_2 = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x600D)
            + Op.JUMPI(pc=Op.MUL(0x20, 0x10), condition=0x0)
            + Op.JUMPDEST
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000000200"),  # noqa: E501
    )
    callee_3 = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x600D)
            + Op.JUMPI(pc=Op.MUL(0x20, 0x10), condition=0x0)
            + Op.JUMPDEST
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000000201"),  # noqa: E501
    )
    # Source: raw bytecode
    callee_4 = pre.deploy_contract(
        code=(
            Op.JUMPI(pc=0x6, condition=0x0)
            + Op.STOP
            + Op.JUMPDEST
            + Op.SSTORE(key=0x0, value=0x600D)
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000000202"),  # noqa: E501
    )
    callee_5 = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x600D)
            + Op.JUMPI(pc=0xFFFFFFF, condition=0x0)
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000000203"),  # noqa: E501
    )
    # Source: raw bytecode
    callee_6 = pre.deploy_contract(
        code=(
            Op.JUMPI(pc=Op.ADD(0x5, 0x4), condition=0x0)
            + Op.STOP
            + Op.JUMPDEST
            + Op.SSTORE(key=0x0, value=0x600D)
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000000208"),  # noqa: E501
    )
    # Source: raw bytecode
    callee_7 = pre.deploy_contract(
        code=(
            Op.JUMPI(pc=0x1000000000000000D, condition=0x0)
            + Op.JUMPDEST
            + Op.JUMPDEST
            + Op.SSTORE(key=0x0, value=0x600D)
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x000000000000000000000000000000000000020d"),  # noqa: E501
    )
    # Source: raw bytecode
    callee_8 = pre.deploy_contract(
        code=(
            Op.JUMPI(pc=0x100000009, condition=0x0)
            + Op.JUMPDEST
            + Op.JUMPDEST
            + Op.SSTORE(key=0x0, value=0x600D)
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x000000000000000000000000000000000000020e"),  # noqa: E501
    )
    # Source: LLL
    # {
    #   @0 (- 0 1)
    #   (asm 0 0 mload jumpi 0x600D 0x00 sstore)
    # }
    callee_9 = pre.deploy_contract(
        code=(
            Op.POP(Op.MLOAD(offset=0x0))
            + Op.POP(Op.SUB(0x0, 0x1))
            + Op.JUMPI(pc=Op.MLOAD(offset=0x0), condition=0x0)
            + Op.SSTORE(key=0x0, value=0x600D)
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x000000000000000000000000000000000000020f"),  # noqa: E501
    )
    callee_10 = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x600D)
            + Op.JUMPI(pc=Op.MUL(0x20, 0x10), condition=0x1)
            + Op.JUMPDEST
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001000"),  # noqa: E501
    )
    callee_11 = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x600D)
            + Op.JUMPI(pc=Op.MUL(0x20, 0x10), condition=0x1)
            + Op.JUMPDEST
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001001"),  # noqa: E501
    )
    # Source: raw bytecode
    callee_12 = pre.deploy_contract(
        code=(
            Op.JUMPI(pc=0x6, condition=0x1)
            + Op.STOP
            + Op.JUMPDEST
            + Op.SSTORE(key=0x0, value=0x600D)
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001002"),  # noqa: E501
    )
    callee_13 = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x600D)
            + Op.JUMPI(pc=0xFFFFFFF, condition=0xFF)
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001003"),  # noqa: E501
    )
    # Source: raw bytecode
    callee_14 = pre.deploy_contract(
        code=(
            Op.PUSH1[0x23]
            + Op.JUMPI(pc=0x8, condition=0x1)
            + Op.PUSH1[0x1]
            + Op.JUMPDEST
            + Op.PUSH1[0x2]
            + Op.SSTORE
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001004"),  # noqa: E501
    )
    # Source: raw bytecode
    callee_15 = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x600D)
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x6, condition=0x6)
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001005"),  # noqa: E501
    )
    # Source: raw bytecode
    callee_16 = pre.deploy_contract(
        code=(
            Op.PUSH2[0x600D]
            + Op.JUMPI(pc=0xA, condition=0x1)
            + Op.PUSH1[0xFF]
            + Op.JUMPDEST
            + Op.PUSH1[0x0]
            + Op.SSTORE
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001006"),  # noqa: E501
    )
    # Source: raw bytecode
    callee_17 = pre.deploy_contract(
        code=(
            Op.JUMP(pc=0xB)
            + Op.JUMPDEST
            + Op.SSTORE(key=0x0, value=0x600D)
            + Op.STOP
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x3, condition=0x1)
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001007"),  # noqa: E501
    )
    # Source: raw bytecode
    callee_18 = pre.deploy_contract(
        code=(
            Op.JUMPI(pc=Op.ADD(0x5, 0x4), condition=0x1)
            + Op.STOP
            + Op.JUMPDEST
            + Op.SSTORE(key=0x0, value=0x600D)
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001008"),  # noqa: E501
    )
    # Source: raw bytecode
    callee_19 = pre.deploy_contract(
        code=(
            Op.JUMPI(pc=0x7, condition=0x1)
            + Op.STOP
            + Op.PUSH1[0x5B]
            + Op.SSTORE(key=0x0, value=0x600D)
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001009"),  # noqa: E501
    )
    # Source: raw bytecode
    callee_20 = pre.deploy_contract(
        code=(
            Op.JUMPI(pc=0x7, condition=0x1)
            + Op.STOP
            + Op.PUSH1[0x1]
            + Op.SSTORE(key=0x0, value=0x600D)
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x000000000000000000000000000000000000100a"),  # noqa: E501
    )
    # Source: raw bytecode
    callee_21 = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x600D)
            + Op.JUMPI(pc=0xD, condition=0x1)
            + Op.GAS
            + Op.JUMPDEST
            + Op.SSTORE(key=0x1, value=Op.GAS)
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x000000000000000000000000000000000000100b"),  # noqa: E501
    )
    # Source: raw bytecode
    callee_22 = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x600D)
            + Op.JUMPI(pc=0xB, condition=0x1)
            + Op.GAS
            + Op.JUMPDEST
            + Op.SSTORE(key=0x1, value=Op.GAS)
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x000000000000000000000000000000000000100c"),  # noqa: E501
    )
    # Source: raw bytecode
    callee_23 = pre.deploy_contract(
        code=(
            Op.JUMPI(pc=0x1000000000000000D, condition=0x11)
            + Op.JUMPDEST
            + Op.JUMPDEST
            + Op.SSTORE(key=0x0, value=0x600D)
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x000000000000000000000000000000000000100d"),  # noqa: E501
    )
    # Source: raw bytecode
    callee_24 = pre.deploy_contract(
        code=(
            Op.JUMPI(pc=0x100000009, condition=0x11)
            + Op.JUMPDEST
            + Op.JUMPDEST
            + Op.SSTORE(key=0x0, value=0x600D)
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x000000000000000000000000000000000000100e"),  # noqa: E501
    )
    # Source: LLL
    # {
    #   @0 (- 0 1)
    #   (asm 1 0 mload jumpi 0x600D 0x00 sstore)
    # }
    callee_25 = pre.deploy_contract(
        code=(
            Op.POP(Op.MLOAD(offset=0x0))
            + Op.POP(Op.SUB(0x0, 0x1))
            + Op.JUMPI(pc=Op.MLOAD(offset=0x0), condition=0x1)
            + Op.SSTORE(key=0x0, value=0x600D)
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x000000000000000000000000000000000000100f"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x100000000000)
    # Source: LLL
    # {
    #     ; limited gas because of the endless loop
    #     (delegatecall 0x10000 $4 0 0 0 0)
    # }
    contract = pre.deploy_contract(
        code=(
            Op.DELEGATECALL(
                gas=0x10000,
                address=Op.CALLDATALOAD(offset=0x4),
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
            "indexes": {"data": 9, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "6001600e575b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b61600d600055"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "61600d60005560106000525b60016000510380600052600b57"
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex("61600d60005560006010602002575b00")
                ),
                callee_3: Account(
                    code=bytes.fromhex("61600d60005560006010602002575b00")
                ),
                callee_4: Account(
                    code=bytes.fromhex("6000600657005b61600d60005500")
                ),
                callee_5: Account(
                    code=bytes.fromhex("61600d6000556000630fffffff5700")
                ),
                callee_6: Account(
                    code=bytes.fromhex("6000600460050157005b61600d600055")
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "60006801000000000000000d575b5b61600d600055"
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex("6000640100000009575b5b61600d600055")
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "6000515060016000035060006000515761600d60005500"
                    )
                ),
                callee_10: Account(
                    code=bytes.fromhex("61600d60005560016010602002575b00")
                ),
                callee_11: Account(
                    code=bytes.fromhex("61600d60005560016010602002575b00")
                ),
                callee_12: Account(
                    code=bytes.fromhex("6001600657005b61600d60005500")
                ),
                callee_13: Account(
                    code=bytes.fromhex("61600d60005560ff630fffffff5700")
                ),
                callee_14: Account(
                    code=bytes.fromhex("6023600160085760015b600255")
                ),
                callee_15: Account(
                    code=bytes.fromhex("61600d6000555b6006600657")
                ),
                callee_16: Account(
                    code=bytes.fromhex("61600d6001600a5760ff5b600055")
                ),
                callee_17: Account(
                    code=bytes.fromhex("600b565b61600d600055005b6001600357")
                ),
                callee_18: Account(
                    code=bytes.fromhex("6001600460050157005b61600d600055")
                ),
                callee_19: Account(
                    code=bytes.fromhex("600160075700605b61600d600055")
                ),
                callee_20: Account(
                    code=bytes.fromhex("600160075700600161600d600055")
                ),
                callee_21: Account(
                    code=bytes.fromhex("61600d6000556001600d575a5b5a600155")
                ),
                callee_22: Account(
                    code=bytes.fromhex("61600d6000556001600b575a5b5a600155")
                ),
                callee_23: Account(
                    code=bytes.fromhex(
                        "60116801000000000000000d575b5b61600d600055"
                    )
                ),
                callee_24: Account(
                    code=bytes.fromhex("6011640100000009575b5b61600d600055")
                ),
                callee_25: Account(
                    code=bytes.fromhex(
                        "6000515060016000035060016000515761600d60005500"
                    )
                ),
                contract: Account(
                    storage={0: 2989},
                    code=bytes.fromhex("600060006000600060043562010000f400"),
                ),
            },
        },
        {
            "indexes": {"data": 15, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "6001600e575b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b61600d600055"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "61600d60005560106000525b60016000510380600052600b57"
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex("61600d60005560006010602002575b00")
                ),
                callee_3: Account(
                    code=bytes.fromhex("61600d60005560006010602002575b00")
                ),
                callee_4: Account(
                    code=bytes.fromhex("6000600657005b61600d60005500")
                ),
                callee_5: Account(
                    code=bytes.fromhex("61600d6000556000630fffffff5700")
                ),
                callee_6: Account(
                    code=bytes.fromhex("6000600460050157005b61600d600055")
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "60006801000000000000000d575b5b61600d600055"
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex("6000640100000009575b5b61600d600055")
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "6000515060016000035060006000515761600d60005500"
                    )
                ),
                callee_10: Account(
                    code=bytes.fromhex("61600d60005560016010602002575b00")
                ),
                callee_11: Account(
                    code=bytes.fromhex("61600d60005560016010602002575b00")
                ),
                callee_12: Account(
                    code=bytes.fromhex("6001600657005b61600d60005500")
                ),
                callee_13: Account(
                    code=bytes.fromhex("61600d60005560ff630fffffff5700")
                ),
                callee_14: Account(
                    code=bytes.fromhex("6023600160085760015b600255")
                ),
                callee_15: Account(
                    code=bytes.fromhex("61600d6000555b6006600657")
                ),
                callee_16: Account(
                    code=bytes.fromhex("61600d6001600a5760ff5b600055")
                ),
                callee_17: Account(
                    code=bytes.fromhex("600b565b61600d600055005b6001600357")
                ),
                callee_18: Account(
                    code=bytes.fromhex("6001600460050157005b61600d600055")
                ),
                callee_19: Account(
                    code=bytes.fromhex("600160075700605b61600d600055")
                ),
                callee_20: Account(
                    code=bytes.fromhex("600160075700600161600d600055")
                ),
                callee_21: Account(
                    code=bytes.fromhex("61600d6000556001600d575a5b5a600155")
                ),
                callee_22: Account(
                    code=bytes.fromhex("61600d6000556001600b575a5b5a600155")
                ),
                callee_23: Account(
                    code=bytes.fromhex(
                        "60116801000000000000000d575b5b61600d600055"
                    )
                ),
                callee_24: Account(
                    code=bytes.fromhex("6011640100000009575b5b61600d600055")
                ),
                callee_25: Account(
                    code=bytes.fromhex(
                        "6000515060016000035060016000515761600d60005500"
                    )
                ),
                contract: Account(
                    storage={0: 2989},
                    code=bytes.fromhex("600060006000600060043562010000f400"),
                ),
            },
        },
        {
            "indexes": {"data": 14, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "6001600e575b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b61600d600055"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "61600d60005560106000525b60016000510380600052600b57"
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex("61600d60005560006010602002575b00")
                ),
                callee_3: Account(
                    code=bytes.fromhex("61600d60005560006010602002575b00")
                ),
                callee_4: Account(
                    code=bytes.fromhex("6000600657005b61600d60005500")
                ),
                callee_5: Account(
                    code=bytes.fromhex("61600d6000556000630fffffff5700")
                ),
                callee_6: Account(
                    code=bytes.fromhex("6000600460050157005b61600d600055")
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "60006801000000000000000d575b5b61600d600055"
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex("6000640100000009575b5b61600d600055")
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "6000515060016000035060006000515761600d60005500"
                    )
                ),
                callee_10: Account(
                    code=bytes.fromhex("61600d60005560016010602002575b00")
                ),
                callee_11: Account(
                    code=bytes.fromhex("61600d60005560016010602002575b00")
                ),
                callee_12: Account(
                    code=bytes.fromhex("6001600657005b61600d60005500")
                ),
                callee_13: Account(
                    code=bytes.fromhex("61600d60005560ff630fffffff5700")
                ),
                callee_14: Account(
                    code=bytes.fromhex("6023600160085760015b600255")
                ),
                callee_15: Account(
                    code=bytes.fromhex("61600d6000555b6006600657")
                ),
                callee_16: Account(
                    code=bytes.fromhex("61600d6001600a5760ff5b600055")
                ),
                callee_17: Account(
                    code=bytes.fromhex("600b565b61600d600055005b6001600357")
                ),
                callee_18: Account(
                    code=bytes.fromhex("6001600460050157005b61600d600055")
                ),
                callee_19: Account(
                    code=bytes.fromhex("600160075700605b61600d600055")
                ),
                callee_20: Account(
                    code=bytes.fromhex("600160075700600161600d600055")
                ),
                callee_21: Account(
                    code=bytes.fromhex("61600d6000556001600d575a5b5a600155")
                ),
                callee_22: Account(
                    code=bytes.fromhex("61600d6000556001600b575a5b5a600155")
                ),
                callee_23: Account(
                    code=bytes.fromhex(
                        "60116801000000000000000d575b5b61600d600055"
                    )
                ),
                callee_24: Account(
                    code=bytes.fromhex("6011640100000009575b5b61600d600055")
                ),
                callee_25: Account(
                    code=bytes.fromhex(
                        "6000515060016000035060016000515761600d60005500"
                    )
                ),
                contract: Account(
                    storage={0: 2989},
                    code=bytes.fromhex("600060006000600060043562010000f400"),
                ),
            },
        },
        {
            "indexes": {"data": 11, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "6001600e575b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b61600d600055"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "61600d60005560106000525b60016000510380600052600b57"
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex("61600d60005560006010602002575b00")
                ),
                callee_3: Account(
                    code=bytes.fromhex("61600d60005560006010602002575b00")
                ),
                callee_4: Account(
                    code=bytes.fromhex("6000600657005b61600d60005500")
                ),
                callee_5: Account(
                    code=bytes.fromhex("61600d6000556000630fffffff5700")
                ),
                callee_6: Account(
                    code=bytes.fromhex("6000600460050157005b61600d600055")
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "60006801000000000000000d575b5b61600d600055"
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex("6000640100000009575b5b61600d600055")
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "6000515060016000035060006000515761600d60005500"
                    )
                ),
                callee_10: Account(
                    code=bytes.fromhex("61600d60005560016010602002575b00")
                ),
                callee_11: Account(
                    code=bytes.fromhex("61600d60005560016010602002575b00")
                ),
                callee_12: Account(
                    code=bytes.fromhex("6001600657005b61600d60005500")
                ),
                callee_13: Account(
                    code=bytes.fromhex("61600d60005560ff630fffffff5700")
                ),
                callee_14: Account(
                    code=bytes.fromhex("6023600160085760015b600255")
                ),
                callee_15: Account(
                    code=bytes.fromhex("61600d6000555b6006600657")
                ),
                callee_16: Account(
                    code=bytes.fromhex("61600d6001600a5760ff5b600055")
                ),
                callee_17: Account(
                    code=bytes.fromhex("600b565b61600d600055005b6001600357")
                ),
                callee_18: Account(
                    code=bytes.fromhex("6001600460050157005b61600d600055")
                ),
                callee_19: Account(
                    code=bytes.fromhex("600160075700605b61600d600055")
                ),
                callee_20: Account(
                    code=bytes.fromhex("600160075700600161600d600055")
                ),
                callee_21: Account(
                    code=bytes.fromhex("61600d6000556001600d575a5b5a600155")
                ),
                callee_22: Account(
                    code=bytes.fromhex("61600d6000556001600b575a5b5a600155")
                ),
                callee_23: Account(
                    code=bytes.fromhex(
                        "60116801000000000000000d575b5b61600d600055"
                    )
                ),
                callee_24: Account(
                    code=bytes.fromhex("6011640100000009575b5b61600d600055")
                ),
                callee_25: Account(
                    code=bytes.fromhex(
                        "6000515060016000035060016000515761600d60005500"
                    )
                ),
                contract: Account(
                    storage={0: 24589},
                    code=bytes.fromhex("600060006000600060043562010000f400"),
                ),
            },
        },
        {
            "indexes": {"data": 10, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "6001600e575b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b61600d600055"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "61600d60005560106000525b60016000510380600052600b57"
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex("61600d60005560006010602002575b00")
                ),
                callee_3: Account(
                    code=bytes.fromhex("61600d60005560006010602002575b00")
                ),
                callee_4: Account(
                    code=bytes.fromhex("6000600657005b61600d60005500")
                ),
                callee_5: Account(
                    code=bytes.fromhex("61600d6000556000630fffffff5700")
                ),
                callee_6: Account(
                    code=bytes.fromhex("6000600460050157005b61600d600055")
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "60006801000000000000000d575b5b61600d600055"
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex("6000640100000009575b5b61600d600055")
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "6000515060016000035060006000515761600d60005500"
                    )
                ),
                callee_10: Account(
                    code=bytes.fromhex("61600d60005560016010602002575b00")
                ),
                callee_11: Account(
                    code=bytes.fromhex("61600d60005560016010602002575b00")
                ),
                callee_12: Account(
                    code=bytes.fromhex("6001600657005b61600d60005500")
                ),
                callee_13: Account(
                    code=bytes.fromhex("61600d60005560ff630fffffff5700")
                ),
                callee_14: Account(
                    code=bytes.fromhex("6023600160085760015b600255")
                ),
                callee_15: Account(
                    code=bytes.fromhex("61600d6000555b6006600657")
                ),
                callee_16: Account(
                    code=bytes.fromhex("61600d6001600a5760ff5b600055")
                ),
                callee_17: Account(
                    code=bytes.fromhex("600b565b61600d600055005b6001600357")
                ),
                callee_18: Account(
                    code=bytes.fromhex("6001600460050157005b61600d600055")
                ),
                callee_19: Account(
                    code=bytes.fromhex("600160075700605b61600d600055")
                ),
                callee_20: Account(
                    code=bytes.fromhex("600160075700600161600d600055")
                ),
                callee_21: Account(
                    code=bytes.fromhex("61600d6000556001600d575a5b5a600155")
                ),
                callee_22: Account(
                    code=bytes.fromhex("61600d6000556001600b575a5b5a600155")
                ),
                callee_23: Account(
                    code=bytes.fromhex(
                        "60116801000000000000000d575b5b61600d600055"
                    )
                ),
                callee_24: Account(
                    code=bytes.fromhex("6011640100000009575b5b61600d600055")
                ),
                callee_25: Account(
                    code=bytes.fromhex(
                        "6000515060016000035060016000515761600d60005500"
                    )
                ),
                contract: Account(
                    storage={0: 24589},
                    code=bytes.fromhex("600060006000600060043562010000f400"),
                ),
            },
        },
        {
            "indexes": {"data": 12, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "6001600e575b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b61600d600055"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "61600d60005560106000525b60016000510380600052600b57"
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex("61600d60005560006010602002575b00")
                ),
                callee_3: Account(
                    code=bytes.fromhex("61600d60005560006010602002575b00")
                ),
                callee_4: Account(
                    code=bytes.fromhex("6000600657005b61600d60005500")
                ),
                callee_5: Account(
                    code=bytes.fromhex("61600d6000556000630fffffff5700")
                ),
                callee_6: Account(
                    code=bytes.fromhex("6000600460050157005b61600d600055")
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "60006801000000000000000d575b5b61600d600055"
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex("6000640100000009575b5b61600d600055")
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "6000515060016000035060006000515761600d60005500"
                    )
                ),
                callee_10: Account(
                    code=bytes.fromhex("61600d60005560016010602002575b00")
                ),
                callee_11: Account(
                    code=bytes.fromhex("61600d60005560016010602002575b00")
                ),
                callee_12: Account(
                    code=bytes.fromhex("6001600657005b61600d60005500")
                ),
                callee_13: Account(
                    code=bytes.fromhex("61600d60005560ff630fffffff5700")
                ),
                callee_14: Account(
                    code=bytes.fromhex("6023600160085760015b600255")
                ),
                callee_15: Account(
                    code=bytes.fromhex("61600d6000555b6006600657")
                ),
                callee_16: Account(
                    code=bytes.fromhex("61600d6001600a5760ff5b600055")
                ),
                callee_17: Account(
                    code=bytes.fromhex("600b565b61600d600055005b6001600357")
                ),
                callee_18: Account(
                    code=bytes.fromhex("6001600460050157005b61600d600055")
                ),
                callee_19: Account(
                    code=bytes.fromhex("600160075700605b61600d600055")
                ),
                callee_20: Account(
                    code=bytes.fromhex("600160075700600161600d600055")
                ),
                callee_21: Account(
                    code=bytes.fromhex("61600d6000556001600d575a5b5a600155")
                ),
                callee_22: Account(
                    code=bytes.fromhex("61600d6000556001600b575a5b5a600155")
                ),
                callee_23: Account(
                    code=bytes.fromhex(
                        "60116801000000000000000d575b5b61600d600055"
                    )
                ),
                callee_24: Account(
                    code=bytes.fromhex("6011640100000009575b5b61600d600055")
                ),
                callee_25: Account(
                    code=bytes.fromhex(
                        "6000515060016000035060016000515761600d60005500"
                    )
                ),
                contract: Account(
                    storage={0: 24589},
                    code=bytes.fromhex("600060006000600060043562010000f400"),
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "6001600e575b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b61600d600055"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "61600d60005560106000525b60016000510380600052600b57"
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex("61600d60005560006010602002575b00")
                ),
                callee_3: Account(
                    code=bytes.fromhex("61600d60005560006010602002575b00")
                ),
                callee_4: Account(
                    code=bytes.fromhex("6000600657005b61600d60005500")
                ),
                callee_5: Account(
                    code=bytes.fromhex("61600d6000556000630fffffff5700")
                ),
                callee_6: Account(
                    code=bytes.fromhex("6000600460050157005b61600d600055")
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "60006801000000000000000d575b5b61600d600055"
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex("6000640100000009575b5b61600d600055")
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "6000515060016000035060006000515761600d60005500"
                    )
                ),
                callee_10: Account(
                    code=bytes.fromhex("61600d60005560016010602002575b00")
                ),
                callee_11: Account(
                    code=bytes.fromhex("61600d60005560016010602002575b00")
                ),
                callee_12: Account(
                    code=bytes.fromhex("6001600657005b61600d60005500")
                ),
                callee_13: Account(
                    code=bytes.fromhex("61600d60005560ff630fffffff5700")
                ),
                callee_14: Account(
                    code=bytes.fromhex("6023600160085760015b600255")
                ),
                callee_15: Account(
                    code=bytes.fromhex("61600d6000555b6006600657")
                ),
                callee_16: Account(
                    code=bytes.fromhex("61600d6001600a5760ff5b600055")
                ),
                callee_17: Account(
                    code=bytes.fromhex("600b565b61600d600055005b6001600357")
                ),
                callee_18: Account(
                    code=bytes.fromhex("6001600460050157005b61600d600055")
                ),
                callee_19: Account(
                    code=bytes.fromhex("600160075700605b61600d600055")
                ),
                callee_20: Account(
                    code=bytes.fromhex("600160075700600161600d600055")
                ),
                callee_21: Account(
                    code=bytes.fromhex("61600d6000556001600d575a5b5a600155")
                ),
                callee_22: Account(
                    code=bytes.fromhex("61600d6000556001600b575a5b5a600155")
                ),
                callee_23: Account(
                    code=bytes.fromhex(
                        "60116801000000000000000d575b5b61600d600055"
                    )
                ),
                callee_24: Account(
                    code=bytes.fromhex("6011640100000009575b5b61600d600055")
                ),
                callee_25: Account(
                    code=bytes.fromhex(
                        "6000515060016000035060016000515761600d60005500"
                    )
                ),
                contract: Account(
                    storage={0: 2989},
                    code=bytes.fromhex("600060006000600060043562010000f400"),
                ),
            },
        },
        {
            "indexes": {"data": 6, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "6001600e575b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b61600d600055"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "61600d60005560106000525b60016000510380600052600b57"
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex("61600d60005560006010602002575b00")
                ),
                callee_3: Account(
                    code=bytes.fromhex("61600d60005560006010602002575b00")
                ),
                callee_4: Account(
                    code=bytes.fromhex("6000600657005b61600d60005500")
                ),
                callee_5: Account(
                    code=bytes.fromhex("61600d6000556000630fffffff5700")
                ),
                callee_6: Account(
                    code=bytes.fromhex("6000600460050157005b61600d600055")
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "60006801000000000000000d575b5b61600d600055"
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex("6000640100000009575b5b61600d600055")
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "6000515060016000035060006000515761600d60005500"
                    )
                ),
                callee_10: Account(
                    code=bytes.fromhex("61600d60005560016010602002575b00")
                ),
                callee_11: Account(
                    code=bytes.fromhex("61600d60005560016010602002575b00")
                ),
                callee_12: Account(
                    code=bytes.fromhex("6001600657005b61600d60005500")
                ),
                callee_13: Account(
                    code=bytes.fromhex("61600d60005560ff630fffffff5700")
                ),
                callee_14: Account(
                    code=bytes.fromhex("6023600160085760015b600255")
                ),
                callee_15: Account(
                    code=bytes.fromhex("61600d6000555b6006600657")
                ),
                callee_16: Account(
                    code=bytes.fromhex("61600d6001600a5760ff5b600055")
                ),
                callee_17: Account(
                    code=bytes.fromhex("600b565b61600d600055005b6001600357")
                ),
                callee_18: Account(
                    code=bytes.fromhex("6001600460050157005b61600d600055")
                ),
                callee_19: Account(
                    code=bytes.fromhex("600160075700605b61600d600055")
                ),
                callee_20: Account(
                    code=bytes.fromhex("600160075700600161600d600055")
                ),
                callee_21: Account(
                    code=bytes.fromhex("61600d6000556001600d575a5b5a600155")
                ),
                callee_22: Account(
                    code=bytes.fromhex("61600d6000556001600b575a5b5a600155")
                ),
                callee_23: Account(
                    code=bytes.fromhex(
                        "60116801000000000000000d575b5b61600d600055"
                    )
                ),
                callee_24: Account(
                    code=bytes.fromhex("6011640100000009575b5b61600d600055")
                ),
                callee_25: Account(
                    code=bytes.fromhex(
                        "6000515060016000035060016000515761600d60005500"
                    )
                ),
                contract: Account(
                    storage={0: 2989},
                    code=bytes.fromhex("600060006000600060043562010000f400"),
                ),
            },
        },
        {
            "indexes": {"data": 18, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "6001600e575b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b61600d600055"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "61600d60005560106000525b60016000510380600052600b57"
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex("61600d60005560006010602002575b00")
                ),
                callee_3: Account(
                    code=bytes.fromhex("61600d60005560006010602002575b00")
                ),
                callee_4: Account(
                    code=bytes.fromhex("6000600657005b61600d60005500")
                ),
                callee_5: Account(
                    code=bytes.fromhex("61600d6000556000630fffffff5700")
                ),
                callee_6: Account(
                    code=bytes.fromhex("6000600460050157005b61600d600055")
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "60006801000000000000000d575b5b61600d600055"
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex("6000640100000009575b5b61600d600055")
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "6000515060016000035060006000515761600d60005500"
                    )
                ),
                callee_10: Account(
                    code=bytes.fromhex("61600d60005560016010602002575b00")
                ),
                callee_11: Account(
                    code=bytes.fromhex("61600d60005560016010602002575b00")
                ),
                callee_12: Account(
                    code=bytes.fromhex("6001600657005b61600d60005500")
                ),
                callee_13: Account(
                    code=bytes.fromhex("61600d60005560ff630fffffff5700")
                ),
                callee_14: Account(
                    code=bytes.fromhex("6023600160085760015b600255")
                ),
                callee_15: Account(
                    code=bytes.fromhex("61600d6000555b6006600657")
                ),
                callee_16: Account(
                    code=bytes.fromhex("61600d6001600a5760ff5b600055")
                ),
                callee_17: Account(
                    code=bytes.fromhex("600b565b61600d600055005b6001600357")
                ),
                callee_18: Account(
                    code=bytes.fromhex("6001600460050157005b61600d600055")
                ),
                callee_19: Account(
                    code=bytes.fromhex("600160075700605b61600d600055")
                ),
                callee_20: Account(
                    code=bytes.fromhex("600160075700600161600d600055")
                ),
                callee_21: Account(
                    code=bytes.fromhex("61600d6000556001600d575a5b5a600155")
                ),
                callee_22: Account(
                    code=bytes.fromhex("61600d6000556001600b575a5b5a600155")
                ),
                callee_23: Account(
                    code=bytes.fromhex(
                        "60116801000000000000000d575b5b61600d600055"
                    )
                ),
                callee_24: Account(
                    code=bytes.fromhex("6011640100000009575b5b61600d600055")
                ),
                callee_25: Account(
                    code=bytes.fromhex(
                        "6000515060016000035060016000515761600d60005500"
                    )
                ),
                contract: Account(
                    storage={0: 2989},
                    code=bytes.fromhex("600060006000600060043562010000f400"),
                ),
            },
        },
        {
            "indexes": {"data": 20, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "6001600e575b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b61600d600055"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "61600d60005560106000525b60016000510380600052600b57"
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex("61600d60005560006010602002575b00")
                ),
                callee_3: Account(
                    code=bytes.fromhex("61600d60005560006010602002575b00")
                ),
                callee_4: Account(
                    code=bytes.fromhex("6000600657005b61600d60005500")
                ),
                callee_5: Account(
                    code=bytes.fromhex("61600d6000556000630fffffff5700")
                ),
                callee_6: Account(
                    code=bytes.fromhex("6000600460050157005b61600d600055")
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "60006801000000000000000d575b5b61600d600055"
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex("6000640100000009575b5b61600d600055")
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "6000515060016000035060006000515761600d60005500"
                    )
                ),
                callee_10: Account(
                    code=bytes.fromhex("61600d60005560016010602002575b00")
                ),
                callee_11: Account(
                    code=bytes.fromhex("61600d60005560016010602002575b00")
                ),
                callee_12: Account(
                    code=bytes.fromhex("6001600657005b61600d60005500")
                ),
                callee_13: Account(
                    code=bytes.fromhex("61600d60005560ff630fffffff5700")
                ),
                callee_14: Account(
                    code=bytes.fromhex("6023600160085760015b600255")
                ),
                callee_15: Account(
                    code=bytes.fromhex("61600d6000555b6006600657")
                ),
                callee_16: Account(
                    code=bytes.fromhex("61600d6001600a5760ff5b600055")
                ),
                callee_17: Account(
                    code=bytes.fromhex("600b565b61600d600055005b6001600357")
                ),
                callee_18: Account(
                    code=bytes.fromhex("6001600460050157005b61600d600055")
                ),
                callee_19: Account(
                    code=bytes.fromhex("600160075700605b61600d600055")
                ),
                callee_20: Account(
                    code=bytes.fromhex("600160075700600161600d600055")
                ),
                callee_21: Account(
                    code=bytes.fromhex("61600d6000556001600d575a5b5a600155")
                ),
                callee_22: Account(
                    code=bytes.fromhex("61600d6000556001600b575a5b5a600155")
                ),
                callee_23: Account(
                    code=bytes.fromhex(
                        "60116801000000000000000d575b5b61600d600055"
                    )
                ),
                callee_24: Account(
                    code=bytes.fromhex("6011640100000009575b5b61600d600055")
                ),
                callee_25: Account(
                    code=bytes.fromhex(
                        "6000515060016000035060016000515761600d60005500"
                    )
                ),
                contract: Account(
                    storage={0: 2989},
                    code=bytes.fromhex("600060006000600060043562010000f400"),
                ),
            },
        },
        {
            "indexes": {"data": 22, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "6001600e575b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b61600d600055"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "61600d60005560106000525b60016000510380600052600b57"
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex("61600d60005560006010602002575b00")
                ),
                callee_3: Account(
                    code=bytes.fromhex("61600d60005560006010602002575b00")
                ),
                callee_4: Account(
                    code=bytes.fromhex("6000600657005b61600d60005500")
                ),
                callee_5: Account(
                    code=bytes.fromhex("61600d6000556000630fffffff5700")
                ),
                callee_6: Account(
                    code=bytes.fromhex("6000600460050157005b61600d600055")
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "60006801000000000000000d575b5b61600d600055"
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex("6000640100000009575b5b61600d600055")
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "6000515060016000035060006000515761600d60005500"
                    )
                ),
                callee_10: Account(
                    code=bytes.fromhex("61600d60005560016010602002575b00")
                ),
                callee_11: Account(
                    code=bytes.fromhex("61600d60005560016010602002575b00")
                ),
                callee_12: Account(
                    code=bytes.fromhex("6001600657005b61600d60005500")
                ),
                callee_13: Account(
                    code=bytes.fromhex("61600d60005560ff630fffffff5700")
                ),
                callee_14: Account(
                    code=bytes.fromhex("6023600160085760015b600255")
                ),
                callee_15: Account(
                    code=bytes.fromhex("61600d6000555b6006600657")
                ),
                callee_16: Account(
                    code=bytes.fromhex("61600d6001600a5760ff5b600055")
                ),
                callee_17: Account(
                    code=bytes.fromhex("600b565b61600d600055005b6001600357")
                ),
                callee_18: Account(
                    code=bytes.fromhex("6001600460050157005b61600d600055")
                ),
                callee_19: Account(
                    code=bytes.fromhex("600160075700605b61600d600055")
                ),
                callee_20: Account(
                    code=bytes.fromhex("600160075700600161600d600055")
                ),
                callee_21: Account(
                    code=bytes.fromhex("61600d6000556001600d575a5b5a600155")
                ),
                callee_22: Account(
                    code=bytes.fromhex("61600d6000556001600b575a5b5a600155")
                ),
                callee_23: Account(
                    code=bytes.fromhex(
                        "60116801000000000000000d575b5b61600d600055"
                    )
                ),
                callee_24: Account(
                    code=bytes.fromhex("6011640100000009575b5b61600d600055")
                ),
                callee_25: Account(
                    code=bytes.fromhex(
                        "6000515060016000035060016000515761600d60005500"
                    )
                ),
                contract: Account(
                    storage={0: 2989},
                    code=bytes.fromhex("600060006000600060043562010000f400"),
                ),
            },
        },
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "6001600e575b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b61600d600055"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "61600d60005560106000525b60016000510380600052600b57"
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex("61600d60005560006010602002575b00")
                ),
                callee_3: Account(
                    code=bytes.fromhex("61600d60005560006010602002575b00")
                ),
                callee_4: Account(
                    code=bytes.fromhex("6000600657005b61600d60005500")
                ),
                callee_5: Account(
                    code=bytes.fromhex("61600d6000556000630fffffff5700")
                ),
                callee_6: Account(
                    code=bytes.fromhex("6000600460050157005b61600d600055")
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "60006801000000000000000d575b5b61600d600055"
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex("6000640100000009575b5b61600d600055")
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "6000515060016000035060006000515761600d60005500"
                    )
                ),
                callee_10: Account(
                    code=bytes.fromhex("61600d60005560016010602002575b00")
                ),
                callee_11: Account(
                    code=bytes.fromhex("61600d60005560016010602002575b00")
                ),
                callee_12: Account(
                    code=bytes.fromhex("6001600657005b61600d60005500")
                ),
                callee_13: Account(
                    code=bytes.fromhex("61600d60005560ff630fffffff5700")
                ),
                callee_14: Account(
                    code=bytes.fromhex("6023600160085760015b600255")
                ),
                callee_15: Account(
                    code=bytes.fromhex("61600d6000555b6006600657")
                ),
                callee_16: Account(
                    code=bytes.fromhex("61600d6001600a5760ff5b600055")
                ),
                callee_17: Account(
                    code=bytes.fromhex("600b565b61600d600055005b6001600357")
                ),
                callee_18: Account(
                    code=bytes.fromhex("6001600460050157005b61600d600055")
                ),
                callee_19: Account(
                    code=bytes.fromhex("600160075700605b61600d600055")
                ),
                callee_20: Account(
                    code=bytes.fromhex("600160075700600161600d600055")
                ),
                callee_21: Account(
                    code=bytes.fromhex("61600d6000556001600d575a5b5a600155")
                ),
                callee_22: Account(
                    code=bytes.fromhex("61600d6000556001600b575a5b5a600155")
                ),
                callee_23: Account(
                    code=bytes.fromhex(
                        "60116801000000000000000d575b5b61600d600055"
                    )
                ),
                callee_24: Account(
                    code=bytes.fromhex("6011640100000009575b5b61600d600055")
                ),
                callee_25: Account(
                    code=bytes.fromhex(
                        "6000515060016000035060016000515761600d60005500"
                    )
                ),
                contract: Account(
                    storage={0: 2989},
                    code=bytes.fromhex("600060006000600060043562010000f400"),
                ),
            },
        },
        {
            "indexes": {"data": 16, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "6001600e575b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b61600d600055"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "61600d60005560106000525b60016000510380600052600b57"
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex("61600d60005560006010602002575b00")
                ),
                callee_3: Account(
                    code=bytes.fromhex("61600d60005560006010602002575b00")
                ),
                callee_4: Account(
                    code=bytes.fromhex("6000600657005b61600d60005500")
                ),
                callee_5: Account(
                    code=bytes.fromhex("61600d6000556000630fffffff5700")
                ),
                callee_6: Account(
                    code=bytes.fromhex("6000600460050157005b61600d600055")
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "60006801000000000000000d575b5b61600d600055"
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex("6000640100000009575b5b61600d600055")
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "6000515060016000035060006000515761600d60005500"
                    )
                ),
                callee_10: Account(
                    code=bytes.fromhex("61600d60005560016010602002575b00")
                ),
                callee_11: Account(
                    code=bytes.fromhex("61600d60005560016010602002575b00")
                ),
                callee_12: Account(
                    code=bytes.fromhex("6001600657005b61600d60005500")
                ),
                callee_13: Account(
                    code=bytes.fromhex("61600d60005560ff630fffffff5700")
                ),
                callee_14: Account(
                    code=bytes.fromhex("6023600160085760015b600255")
                ),
                callee_15: Account(
                    code=bytes.fromhex("61600d6000555b6006600657")
                ),
                callee_16: Account(
                    code=bytes.fromhex("61600d6001600a5760ff5b600055")
                ),
                callee_17: Account(
                    code=bytes.fromhex("600b565b61600d600055005b6001600357")
                ),
                callee_18: Account(
                    code=bytes.fromhex("6001600460050157005b61600d600055")
                ),
                callee_19: Account(
                    code=bytes.fromhex("600160075700605b61600d600055")
                ),
                callee_20: Account(
                    code=bytes.fromhex("600160075700600161600d600055")
                ),
                callee_21: Account(
                    code=bytes.fromhex("61600d6000556001600d575a5b5a600155")
                ),
                callee_22: Account(
                    code=bytes.fromhex("61600d6000556001600b575a5b5a600155")
                ),
                callee_23: Account(
                    code=bytes.fromhex(
                        "60116801000000000000000d575b5b61600d600055"
                    )
                ),
                callee_24: Account(
                    code=bytes.fromhex("6011640100000009575b5b61600d600055")
                ),
                callee_25: Account(
                    code=bytes.fromhex(
                        "6000515060016000035060016000515761600d60005500"
                    )
                ),
                contract: Account(
                    storage={0: 2989},
                    code=bytes.fromhex("600060006000600060043562010000f400"),
                ),
            },
        },
        {
            "indexes": {"data": 17, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "6001600e575b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b61600d600055"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "61600d60005560106000525b60016000510380600052600b57"
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex("61600d60005560006010602002575b00")
                ),
                callee_3: Account(
                    code=bytes.fromhex("61600d60005560006010602002575b00")
                ),
                callee_4: Account(
                    code=bytes.fromhex("6000600657005b61600d60005500")
                ),
                callee_5: Account(
                    code=bytes.fromhex("61600d6000556000630fffffff5700")
                ),
                callee_6: Account(
                    code=bytes.fromhex("6000600460050157005b61600d600055")
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "60006801000000000000000d575b5b61600d600055"
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex("6000640100000009575b5b61600d600055")
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "6000515060016000035060006000515761600d60005500"
                    )
                ),
                callee_10: Account(
                    code=bytes.fromhex("61600d60005560016010602002575b00")
                ),
                callee_11: Account(
                    code=bytes.fromhex("61600d60005560016010602002575b00")
                ),
                callee_12: Account(
                    code=bytes.fromhex("6001600657005b61600d60005500")
                ),
                callee_13: Account(
                    code=bytes.fromhex("61600d60005560ff630fffffff5700")
                ),
                callee_14: Account(
                    code=bytes.fromhex("6023600160085760015b600255")
                ),
                callee_15: Account(
                    code=bytes.fromhex("61600d6000555b6006600657")
                ),
                callee_16: Account(
                    code=bytes.fromhex("61600d6001600a5760ff5b600055")
                ),
                callee_17: Account(
                    code=bytes.fromhex("600b565b61600d600055005b6001600357")
                ),
                callee_18: Account(
                    code=bytes.fromhex("6001600460050157005b61600d600055")
                ),
                callee_19: Account(
                    code=bytes.fromhex("600160075700605b61600d600055")
                ),
                callee_20: Account(
                    code=bytes.fromhex("600160075700600161600d600055")
                ),
                callee_21: Account(
                    code=bytes.fromhex("61600d6000556001600d575a5b5a600155")
                ),
                callee_22: Account(
                    code=bytes.fromhex("61600d6000556001600b575a5b5a600155")
                ),
                callee_23: Account(
                    code=bytes.fromhex(
                        "60116801000000000000000d575b5b61600d600055"
                    )
                ),
                callee_24: Account(
                    code=bytes.fromhex("6011640100000009575b5b61600d600055")
                ),
                callee_25: Account(
                    code=bytes.fromhex(
                        "6000515060016000035060016000515761600d60005500"
                    )
                ),
                contract: Account(
                    storage={0: 2989},
                    code=bytes.fromhex("600060006000600060043562010000f400"),
                ),
            },
        },
        {
            "indexes": {"data": 8, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "6001600e575b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b61600d600055"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "61600d60005560106000525b60016000510380600052600b57"
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex("61600d60005560006010602002575b00")
                ),
                callee_3: Account(
                    code=bytes.fromhex("61600d60005560006010602002575b00")
                ),
                callee_4: Account(
                    code=bytes.fromhex("6000600657005b61600d60005500")
                ),
                callee_5: Account(
                    code=bytes.fromhex("61600d6000556000630fffffff5700")
                ),
                callee_6: Account(
                    code=bytes.fromhex("6000600460050157005b61600d600055")
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "60006801000000000000000d575b5b61600d600055"
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex("6000640100000009575b5b61600d600055")
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "6000515060016000035060006000515761600d60005500"
                    )
                ),
                callee_10: Account(
                    code=bytes.fromhex("61600d60005560016010602002575b00")
                ),
                callee_11: Account(
                    code=bytes.fromhex("61600d60005560016010602002575b00")
                ),
                callee_12: Account(
                    code=bytes.fromhex("6001600657005b61600d60005500")
                ),
                callee_13: Account(
                    code=bytes.fromhex("61600d60005560ff630fffffff5700")
                ),
                callee_14: Account(
                    code=bytes.fromhex("6023600160085760015b600255")
                ),
                callee_15: Account(
                    code=bytes.fromhex("61600d6000555b6006600657")
                ),
                callee_16: Account(
                    code=bytes.fromhex("61600d6001600a5760ff5b600055")
                ),
                callee_17: Account(
                    code=bytes.fromhex("600b565b61600d600055005b6001600357")
                ),
                callee_18: Account(
                    code=bytes.fromhex("6001600460050157005b61600d600055")
                ),
                callee_19: Account(
                    code=bytes.fromhex("600160075700605b61600d600055")
                ),
                callee_20: Account(
                    code=bytes.fromhex("600160075700600161600d600055")
                ),
                callee_21: Account(
                    code=bytes.fromhex("61600d6000556001600d575a5b5a600155")
                ),
                callee_22: Account(
                    code=bytes.fromhex("61600d6000556001600b575a5b5a600155")
                ),
                callee_23: Account(
                    code=bytes.fromhex(
                        "60116801000000000000000d575b5b61600d600055"
                    )
                ),
                callee_24: Account(
                    code=bytes.fromhex("6011640100000009575b5b61600d600055")
                ),
                callee_25: Account(
                    code=bytes.fromhex(
                        "6000515060016000035060016000515761600d60005500"
                    )
                ),
                contract: Account(
                    storage={0: 2989},
                    code=bytes.fromhex("600060006000600060043562010000f400"),
                ),
            },
        },
        {
            "indexes": {"data": 4, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "6001600e575b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b61600d600055"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "61600d60005560106000525b60016000510380600052600b57"
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex("61600d60005560006010602002575b00")
                ),
                callee_3: Account(
                    code=bytes.fromhex("61600d60005560006010602002575b00")
                ),
                callee_4: Account(
                    code=bytes.fromhex("6000600657005b61600d60005500")
                ),
                callee_5: Account(
                    code=bytes.fromhex("61600d6000556000630fffffff5700")
                ),
                callee_6: Account(
                    code=bytes.fromhex("6000600460050157005b61600d600055")
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "60006801000000000000000d575b5b61600d600055"
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex("6000640100000009575b5b61600d600055")
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "6000515060016000035060006000515761600d60005500"
                    )
                ),
                callee_10: Account(
                    code=bytes.fromhex("61600d60005560016010602002575b00")
                ),
                callee_11: Account(
                    code=bytes.fromhex("61600d60005560016010602002575b00")
                ),
                callee_12: Account(
                    code=bytes.fromhex("6001600657005b61600d60005500")
                ),
                callee_13: Account(
                    code=bytes.fromhex("61600d60005560ff630fffffff5700")
                ),
                callee_14: Account(
                    code=bytes.fromhex("6023600160085760015b600255")
                ),
                callee_15: Account(
                    code=bytes.fromhex("61600d6000555b6006600657")
                ),
                callee_16: Account(
                    code=bytes.fromhex("61600d6001600a5760ff5b600055")
                ),
                callee_17: Account(
                    code=bytes.fromhex("600b565b61600d600055005b6001600357")
                ),
                callee_18: Account(
                    code=bytes.fromhex("6001600460050157005b61600d600055")
                ),
                callee_19: Account(
                    code=bytes.fromhex("600160075700605b61600d600055")
                ),
                callee_20: Account(
                    code=bytes.fromhex("600160075700600161600d600055")
                ),
                callee_21: Account(
                    code=bytes.fromhex("61600d6000556001600d575a5b5a600155")
                ),
                callee_22: Account(
                    code=bytes.fromhex("61600d6000556001600b575a5b5a600155")
                ),
                callee_23: Account(
                    code=bytes.fromhex(
                        "60116801000000000000000d575b5b61600d600055"
                    )
                ),
                callee_24: Account(
                    code=bytes.fromhex("6011640100000009575b5b61600d600055")
                ),
                callee_25: Account(
                    code=bytes.fromhex(
                        "6000515060016000035060016000515761600d60005500"
                    )
                ),
                contract: Account(
                    storage={0: 24589},
                    code=bytes.fromhex("600060006000600060043562010000f400"),
                ),
            },
        },
        {
            "indexes": {"data": 24, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "6001600e575b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b61600d600055"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "61600d60005560106000525b60016000510380600052600b57"
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex("61600d60005560006010602002575b00")
                ),
                callee_3: Account(
                    code=bytes.fromhex("61600d60005560006010602002575b00")
                ),
                callee_4: Account(
                    code=bytes.fromhex("6000600657005b61600d60005500")
                ),
                callee_5: Account(
                    code=bytes.fromhex("61600d6000556000630fffffff5700")
                ),
                callee_6: Account(
                    code=bytes.fromhex("6000600460050157005b61600d600055")
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "60006801000000000000000d575b5b61600d600055"
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex("6000640100000009575b5b61600d600055")
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "6000515060016000035060006000515761600d60005500"
                    )
                ),
                callee_10: Account(
                    code=bytes.fromhex("61600d60005560016010602002575b00")
                ),
                callee_11: Account(
                    code=bytes.fromhex("61600d60005560016010602002575b00")
                ),
                callee_12: Account(
                    code=bytes.fromhex("6001600657005b61600d60005500")
                ),
                callee_13: Account(
                    code=bytes.fromhex("61600d60005560ff630fffffff5700")
                ),
                callee_14: Account(
                    code=bytes.fromhex("6023600160085760015b600255")
                ),
                callee_15: Account(
                    code=bytes.fromhex("61600d6000555b6006600657")
                ),
                callee_16: Account(
                    code=bytes.fromhex("61600d6001600a5760ff5b600055")
                ),
                callee_17: Account(
                    code=bytes.fromhex("600b565b61600d600055005b6001600357")
                ),
                callee_18: Account(
                    code=bytes.fromhex("6001600460050157005b61600d600055")
                ),
                callee_19: Account(
                    code=bytes.fromhex("600160075700605b61600d600055")
                ),
                callee_20: Account(
                    code=bytes.fromhex("600160075700600161600d600055")
                ),
                callee_21: Account(
                    code=bytes.fromhex("61600d6000556001600d575a5b5a600155")
                ),
                callee_22: Account(
                    code=bytes.fromhex("61600d6000556001600b575a5b5a600155")
                ),
                callee_23: Account(
                    code=bytes.fromhex(
                        "60116801000000000000000d575b5b61600d600055"
                    )
                ),
                callee_24: Account(
                    code=bytes.fromhex("6011640100000009575b5b61600d600055")
                ),
                callee_25: Account(
                    code=bytes.fromhex(
                        "6000515060016000035060016000515761600d60005500"
                    )
                ),
                contract: Account(
                    storage={0: 24589},
                    code=bytes.fromhex("600060006000600060043562010000f400"),
                ),
            },
        },
        {
            "indexes": {"data": 25, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "6001600e575b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b61600d600055"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "61600d60005560106000525b60016000510380600052600b57"
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex("61600d60005560006010602002575b00")
                ),
                callee_3: Account(
                    code=bytes.fromhex("61600d60005560006010602002575b00")
                ),
                callee_4: Account(
                    code=bytes.fromhex("6000600657005b61600d60005500")
                ),
                callee_5: Account(
                    code=bytes.fromhex("61600d6000556000630fffffff5700")
                ),
                callee_6: Account(
                    code=bytes.fromhex("6000600460050157005b61600d600055")
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "60006801000000000000000d575b5b61600d600055"
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex("6000640100000009575b5b61600d600055")
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "6000515060016000035060006000515761600d60005500"
                    )
                ),
                callee_10: Account(
                    code=bytes.fromhex("61600d60005560016010602002575b00")
                ),
                callee_11: Account(
                    code=bytes.fromhex("61600d60005560016010602002575b00")
                ),
                callee_12: Account(
                    code=bytes.fromhex("6001600657005b61600d60005500")
                ),
                callee_13: Account(
                    code=bytes.fromhex("61600d60005560ff630fffffff5700")
                ),
                callee_14: Account(
                    code=bytes.fromhex("6023600160085760015b600255")
                ),
                callee_15: Account(
                    code=bytes.fromhex("61600d6000555b6006600657")
                ),
                callee_16: Account(
                    code=bytes.fromhex("61600d6001600a5760ff5b600055")
                ),
                callee_17: Account(
                    code=bytes.fromhex("600b565b61600d600055005b6001600357")
                ),
                callee_18: Account(
                    code=bytes.fromhex("6001600460050157005b61600d600055")
                ),
                callee_19: Account(
                    code=bytes.fromhex("600160075700605b61600d600055")
                ),
                callee_20: Account(
                    code=bytes.fromhex("600160075700600161600d600055")
                ),
                callee_21: Account(
                    code=bytes.fromhex("61600d6000556001600d575a5b5a600155")
                ),
                callee_22: Account(
                    code=bytes.fromhex("61600d6000556001600b575a5b5a600155")
                ),
                callee_23: Account(
                    code=bytes.fromhex(
                        "60116801000000000000000d575b5b61600d600055"
                    )
                ),
                callee_24: Account(
                    code=bytes.fromhex("6011640100000009575b5b61600d600055")
                ),
                callee_25: Account(
                    code=bytes.fromhex(
                        "6000515060016000035060016000515761600d60005500"
                    )
                ),
                contract: Account(
                    storage={0: 24589},
                    code=bytes.fromhex("600060006000600060043562010000f400"),
                ),
            },
        },
        {
            "indexes": {"data": 13, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "6001600e575b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b61600d600055"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "61600d60005560106000525b60016000510380600052600b57"
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex("61600d60005560006010602002575b00")
                ),
                callee_3: Account(
                    code=bytes.fromhex("61600d60005560006010602002575b00")
                ),
                callee_4: Account(
                    code=bytes.fromhex("6000600657005b61600d60005500")
                ),
                callee_5: Account(
                    code=bytes.fromhex("61600d6000556000630fffffff5700")
                ),
                callee_6: Account(
                    code=bytes.fromhex("6000600460050157005b61600d600055")
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "60006801000000000000000d575b5b61600d600055"
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex("6000640100000009575b5b61600d600055")
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "6000515060016000035060006000515761600d60005500"
                    )
                ),
                callee_10: Account(
                    code=bytes.fromhex("61600d60005560016010602002575b00")
                ),
                callee_11: Account(
                    code=bytes.fromhex("61600d60005560016010602002575b00")
                ),
                callee_12: Account(
                    code=bytes.fromhex("6001600657005b61600d60005500")
                ),
                callee_13: Account(
                    code=bytes.fromhex("61600d60005560ff630fffffff5700")
                ),
                callee_14: Account(
                    code=bytes.fromhex("6023600160085760015b600255")
                ),
                callee_15: Account(
                    code=bytes.fromhex("61600d6000555b6006600657")
                ),
                callee_16: Account(
                    code=bytes.fromhex("61600d6001600a5760ff5b600055")
                ),
                callee_17: Account(
                    code=bytes.fromhex("600b565b61600d600055005b6001600357")
                ),
                callee_18: Account(
                    code=bytes.fromhex("6001600460050157005b61600d600055")
                ),
                callee_19: Account(
                    code=bytes.fromhex("600160075700605b61600d600055")
                ),
                callee_20: Account(
                    code=bytes.fromhex("600160075700600161600d600055")
                ),
                callee_21: Account(
                    code=bytes.fromhex("61600d6000556001600d575a5b5a600155")
                ),
                callee_22: Account(
                    code=bytes.fromhex("61600d6000556001600b575a5b5a600155")
                ),
                callee_23: Account(
                    code=bytes.fromhex(
                        "60116801000000000000000d575b5b61600d600055"
                    )
                ),
                callee_24: Account(
                    code=bytes.fromhex("6011640100000009575b5b61600d600055")
                ),
                callee_25: Account(
                    code=bytes.fromhex(
                        "6000515060016000035060016000515761600d60005500"
                    )
                ),
                contract: Account(
                    storage={0: 2989},
                    code=bytes.fromhex("600060006000600060043562010000f400"),
                ),
            },
        },
        {
            "indexes": {"data": 3, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "6001600e575b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b61600d600055"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "61600d60005560106000525b60016000510380600052600b57"
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex("61600d60005560006010602002575b00")
                ),
                callee_3: Account(
                    code=bytes.fromhex("61600d60005560006010602002575b00")
                ),
                callee_4: Account(
                    code=bytes.fromhex("6000600657005b61600d60005500")
                ),
                callee_5: Account(
                    code=bytes.fromhex("61600d6000556000630fffffff5700")
                ),
                callee_6: Account(
                    code=bytes.fromhex("6000600460050157005b61600d600055")
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "60006801000000000000000d575b5b61600d600055"
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex("6000640100000009575b5b61600d600055")
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "6000515060016000035060006000515761600d60005500"
                    )
                ),
                callee_10: Account(
                    code=bytes.fromhex("61600d60005560016010602002575b00")
                ),
                callee_11: Account(
                    code=bytes.fromhex("61600d60005560016010602002575b00")
                ),
                callee_12: Account(
                    code=bytes.fromhex("6001600657005b61600d60005500")
                ),
                callee_13: Account(
                    code=bytes.fromhex("61600d60005560ff630fffffff5700")
                ),
                callee_14: Account(
                    code=bytes.fromhex("6023600160085760015b600255")
                ),
                callee_15: Account(
                    code=bytes.fromhex("61600d6000555b6006600657")
                ),
                callee_16: Account(
                    code=bytes.fromhex("61600d6001600a5760ff5b600055")
                ),
                callee_17: Account(
                    code=bytes.fromhex("600b565b61600d600055005b6001600357")
                ),
                callee_18: Account(
                    code=bytes.fromhex("6001600460050157005b61600d600055")
                ),
                callee_19: Account(
                    code=bytes.fromhex("600160075700605b61600d600055")
                ),
                callee_20: Account(
                    code=bytes.fromhex("600160075700600161600d600055")
                ),
                callee_21: Account(
                    code=bytes.fromhex("61600d6000556001600d575a5b5a600155")
                ),
                callee_22: Account(
                    code=bytes.fromhex("61600d6000556001600b575a5b5a600155")
                ),
                callee_23: Account(
                    code=bytes.fromhex(
                        "60116801000000000000000d575b5b61600d600055"
                    )
                ),
                callee_24: Account(
                    code=bytes.fromhex("6011640100000009575b5b61600d600055")
                ),
                callee_25: Account(
                    code=bytes.fromhex(
                        "6000515060016000035060016000515761600d60005500"
                    )
                ),
                contract: Account(
                    storage={0: 24589},
                    code=bytes.fromhex("600060006000600060043562010000f400"),
                ),
            },
        },
        {
            "indexes": {"data": 7, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "6001600e575b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b61600d600055"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "61600d60005560106000525b60016000510380600052600b57"
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex("61600d60005560006010602002575b00")
                ),
                callee_3: Account(
                    code=bytes.fromhex("61600d60005560006010602002575b00")
                ),
                callee_4: Account(
                    code=bytes.fromhex("6000600657005b61600d60005500")
                ),
                callee_5: Account(
                    code=bytes.fromhex("61600d6000556000630fffffff5700")
                ),
                callee_6: Account(
                    code=bytes.fromhex("6000600460050157005b61600d600055")
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "60006801000000000000000d575b5b61600d600055"
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex("6000640100000009575b5b61600d600055")
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "6000515060016000035060006000515761600d60005500"
                    )
                ),
                callee_10: Account(
                    code=bytes.fromhex("61600d60005560016010602002575b00")
                ),
                callee_11: Account(
                    code=bytes.fromhex("61600d60005560016010602002575b00")
                ),
                callee_12: Account(
                    code=bytes.fromhex("6001600657005b61600d60005500")
                ),
                callee_13: Account(
                    code=bytes.fromhex("61600d60005560ff630fffffff5700")
                ),
                callee_14: Account(
                    code=bytes.fromhex("6023600160085760015b600255")
                ),
                callee_15: Account(
                    code=bytes.fromhex("61600d6000555b6006600657")
                ),
                callee_16: Account(
                    code=bytes.fromhex("61600d6001600a5760ff5b600055")
                ),
                callee_17: Account(
                    code=bytes.fromhex("600b565b61600d600055005b6001600357")
                ),
                callee_18: Account(
                    code=bytes.fromhex("6001600460050157005b61600d600055")
                ),
                callee_19: Account(
                    code=bytes.fromhex("600160075700605b61600d600055")
                ),
                callee_20: Account(
                    code=bytes.fromhex("600160075700600161600d600055")
                ),
                callee_21: Account(
                    code=bytes.fromhex("61600d6000556001600d575a5b5a600155")
                ),
                callee_22: Account(
                    code=bytes.fromhex("61600d6000556001600b575a5b5a600155")
                ),
                callee_23: Account(
                    code=bytes.fromhex(
                        "60116801000000000000000d575b5b61600d600055"
                    )
                ),
                callee_24: Account(
                    code=bytes.fromhex("6011640100000009575b5b61600d600055")
                ),
                callee_25: Account(
                    code=bytes.fromhex(
                        "6000515060016000035060016000515761600d60005500"
                    )
                ),
                contract: Account(
                    storage={0: 24589},
                    code=bytes.fromhex("600060006000600060043562010000f400"),
                ),
            },
        },
        {
            "indexes": {"data": 19, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "6001600e575b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b61600d600055"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "61600d60005560106000525b60016000510380600052600b57"
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex("61600d60005560006010602002575b00")
                ),
                callee_3: Account(
                    code=bytes.fromhex("61600d60005560006010602002575b00")
                ),
                callee_4: Account(
                    code=bytes.fromhex("6000600657005b61600d60005500")
                ),
                callee_5: Account(
                    code=bytes.fromhex("61600d6000556000630fffffff5700")
                ),
                callee_6: Account(
                    code=bytes.fromhex("6000600460050157005b61600d600055")
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "60006801000000000000000d575b5b61600d600055"
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex("6000640100000009575b5b61600d600055")
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "6000515060016000035060006000515761600d60005500"
                    )
                ),
                callee_10: Account(
                    code=bytes.fromhex("61600d60005560016010602002575b00")
                ),
                callee_11: Account(
                    code=bytes.fromhex("61600d60005560016010602002575b00")
                ),
                callee_12: Account(
                    code=bytes.fromhex("6001600657005b61600d60005500")
                ),
                callee_13: Account(
                    code=bytes.fromhex("61600d60005560ff630fffffff5700")
                ),
                callee_14: Account(
                    code=bytes.fromhex("6023600160085760015b600255")
                ),
                callee_15: Account(
                    code=bytes.fromhex("61600d6000555b6006600657")
                ),
                callee_16: Account(
                    code=bytes.fromhex("61600d6001600a5760ff5b600055")
                ),
                callee_17: Account(
                    code=bytes.fromhex("600b565b61600d600055005b6001600357")
                ),
                callee_18: Account(
                    code=bytes.fromhex("6001600460050157005b61600d600055")
                ),
                callee_19: Account(
                    code=bytes.fromhex("600160075700605b61600d600055")
                ),
                callee_20: Account(
                    code=bytes.fromhex("600160075700600161600d600055")
                ),
                callee_21: Account(
                    code=bytes.fromhex("61600d6000556001600d575a5b5a600155")
                ),
                callee_22: Account(
                    code=bytes.fromhex("61600d6000556001600b575a5b5a600155")
                ),
                callee_23: Account(
                    code=bytes.fromhex(
                        "60116801000000000000000d575b5b61600d600055"
                    )
                ),
                callee_24: Account(
                    code=bytes.fromhex("6011640100000009575b5b61600d600055")
                ),
                callee_25: Account(
                    code=bytes.fromhex(
                        "6000515060016000035060016000515761600d60005500"
                    )
                ),
                contract: Account(
                    storage={0: 24589},
                    code=bytes.fromhex("600060006000600060043562010000f400"),
                ),
            },
        },
        {
            "indexes": {"data": 21, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "6001600e575b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b61600d600055"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "61600d60005560106000525b60016000510380600052600b57"
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex("61600d60005560006010602002575b00")
                ),
                callee_3: Account(
                    code=bytes.fromhex("61600d60005560006010602002575b00")
                ),
                callee_4: Account(
                    code=bytes.fromhex("6000600657005b61600d60005500")
                ),
                callee_5: Account(
                    code=bytes.fromhex("61600d6000556000630fffffff5700")
                ),
                callee_6: Account(
                    code=bytes.fromhex("6000600460050157005b61600d600055")
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "60006801000000000000000d575b5b61600d600055"
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex("6000640100000009575b5b61600d600055")
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "6000515060016000035060006000515761600d60005500"
                    )
                ),
                callee_10: Account(
                    code=bytes.fromhex("61600d60005560016010602002575b00")
                ),
                callee_11: Account(
                    code=bytes.fromhex("61600d60005560016010602002575b00")
                ),
                callee_12: Account(
                    code=bytes.fromhex("6001600657005b61600d60005500")
                ),
                callee_13: Account(
                    code=bytes.fromhex("61600d60005560ff630fffffff5700")
                ),
                callee_14: Account(
                    code=bytes.fromhex("6023600160085760015b600255")
                ),
                callee_15: Account(
                    code=bytes.fromhex("61600d6000555b6006600657")
                ),
                callee_16: Account(
                    code=bytes.fromhex("61600d6001600a5760ff5b600055")
                ),
                callee_17: Account(
                    code=bytes.fromhex("600b565b61600d600055005b6001600357")
                ),
                callee_18: Account(
                    code=bytes.fromhex("6001600460050157005b61600d600055")
                ),
                callee_19: Account(
                    code=bytes.fromhex("600160075700605b61600d600055")
                ),
                callee_20: Account(
                    code=bytes.fromhex("600160075700600161600d600055")
                ),
                callee_21: Account(
                    code=bytes.fromhex("61600d6000556001600d575a5b5a600155")
                ),
                callee_22: Account(
                    code=bytes.fromhex("61600d6000556001600b575a5b5a600155")
                ),
                callee_23: Account(
                    code=bytes.fromhex(
                        "60116801000000000000000d575b5b61600d600055"
                    )
                ),
                callee_24: Account(
                    code=bytes.fromhex("6011640100000009575b5b61600d600055")
                ),
                callee_25: Account(
                    code=bytes.fromhex(
                        "6000515060016000035060016000515761600d60005500"
                    )
                ),
                contract: Account(
                    storage={0: 24589},
                    code=bytes.fromhex("600060006000600060043562010000f400"),
                ),
            },
        },
        {
            "indexes": {"data": 23, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "6001600e575b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b61600d600055"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "61600d60005560106000525b60016000510380600052600b57"
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex("61600d60005560006010602002575b00")
                ),
                callee_3: Account(
                    code=bytes.fromhex("61600d60005560006010602002575b00")
                ),
                callee_4: Account(
                    code=bytes.fromhex("6000600657005b61600d60005500")
                ),
                callee_5: Account(
                    code=bytes.fromhex("61600d6000556000630fffffff5700")
                ),
                callee_6: Account(
                    code=bytes.fromhex("6000600460050157005b61600d600055")
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "60006801000000000000000d575b5b61600d600055"
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex("6000640100000009575b5b61600d600055")
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "6000515060016000035060006000515761600d60005500"
                    )
                ),
                callee_10: Account(
                    code=bytes.fromhex("61600d60005560016010602002575b00")
                ),
                callee_11: Account(
                    code=bytes.fromhex("61600d60005560016010602002575b00")
                ),
                callee_12: Account(
                    code=bytes.fromhex("6001600657005b61600d60005500")
                ),
                callee_13: Account(
                    code=bytes.fromhex("61600d60005560ff630fffffff5700")
                ),
                callee_14: Account(
                    code=bytes.fromhex("6023600160085760015b600255")
                ),
                callee_15: Account(
                    code=bytes.fromhex("61600d6000555b6006600657")
                ),
                callee_16: Account(
                    code=bytes.fromhex("61600d6001600a5760ff5b600055")
                ),
                callee_17: Account(
                    code=bytes.fromhex("600b565b61600d600055005b6001600357")
                ),
                callee_18: Account(
                    code=bytes.fromhex("6001600460050157005b61600d600055")
                ),
                callee_19: Account(
                    code=bytes.fromhex("600160075700605b61600d600055")
                ),
                callee_20: Account(
                    code=bytes.fromhex("600160075700600161600d600055")
                ),
                callee_21: Account(
                    code=bytes.fromhex("61600d6000556001600d575a5b5a600155")
                ),
                callee_22: Account(
                    code=bytes.fromhex("61600d6000556001600b575a5b5a600155")
                ),
                callee_23: Account(
                    code=bytes.fromhex(
                        "60116801000000000000000d575b5b61600d600055"
                    )
                ),
                callee_24: Account(
                    code=bytes.fromhex("6011640100000009575b5b61600d600055")
                ),
                callee_25: Account(
                    code=bytes.fromhex(
                        "6000515060016000035060016000515761600d60005500"
                    )
                ),
                contract: Account(
                    storage={0: 24589},
                    code=bytes.fromhex("600060006000600060043562010000f400"),
                ),
            },
        },
        {
            "indexes": {"data": 2, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "6001600e575b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b61600d600055"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "61600d60005560106000525b60016000510380600052600b57"
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex("61600d60005560006010602002575b00")
                ),
                callee_3: Account(
                    code=bytes.fromhex("61600d60005560006010602002575b00")
                ),
                callee_4: Account(
                    code=bytes.fromhex("6000600657005b61600d60005500")
                ),
                callee_5: Account(
                    code=bytes.fromhex("61600d6000556000630fffffff5700")
                ),
                callee_6: Account(
                    code=bytes.fromhex("6000600460050157005b61600d600055")
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "60006801000000000000000d575b5b61600d600055"
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex("6000640100000009575b5b61600d600055")
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "6000515060016000035060006000515761600d60005500"
                    )
                ),
                callee_10: Account(
                    code=bytes.fromhex("61600d60005560016010602002575b00")
                ),
                callee_11: Account(
                    code=bytes.fromhex("61600d60005560016010602002575b00")
                ),
                callee_12: Account(
                    code=bytes.fromhex("6001600657005b61600d60005500")
                ),
                callee_13: Account(
                    code=bytes.fromhex("61600d60005560ff630fffffff5700")
                ),
                callee_14: Account(
                    code=bytes.fromhex("6023600160085760015b600255")
                ),
                callee_15: Account(
                    code=bytes.fromhex("61600d6000555b6006600657")
                ),
                callee_16: Account(
                    code=bytes.fromhex("61600d6001600a5760ff5b600055")
                ),
                callee_17: Account(
                    code=bytes.fromhex("600b565b61600d600055005b6001600357")
                ),
                callee_18: Account(
                    code=bytes.fromhex("6001600460050157005b61600d600055")
                ),
                callee_19: Account(
                    code=bytes.fromhex("600160075700605b61600d600055")
                ),
                callee_20: Account(
                    code=bytes.fromhex("600160075700600161600d600055")
                ),
                callee_21: Account(
                    code=bytes.fromhex("61600d6000556001600d575a5b5a600155")
                ),
                callee_22: Account(
                    code=bytes.fromhex("61600d6000556001600b575a5b5a600155")
                ),
                callee_23: Account(
                    code=bytes.fromhex(
                        "60116801000000000000000d575b5b61600d600055"
                    )
                ),
                callee_24: Account(
                    code=bytes.fromhex("6011640100000009575b5b61600d600055")
                ),
                callee_25: Account(
                    code=bytes.fromhex(
                        "6000515060016000035060016000515761600d60005500"
                    )
                ),
                contract: Account(
                    storage={0: 24589},
                    code=bytes.fromhex("600060006000600060043562010000f400"),
                ),
            },
        },
        {
            "indexes": {"data": 5, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "6001600e575b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b61600d600055"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "61600d60005560106000525b60016000510380600052600b57"
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex("61600d60005560006010602002575b00")
                ),
                callee_3: Account(
                    code=bytes.fromhex("61600d60005560006010602002575b00")
                ),
                callee_4: Account(
                    code=bytes.fromhex("6000600657005b61600d60005500")
                ),
                callee_5: Account(
                    code=bytes.fromhex("61600d6000556000630fffffff5700")
                ),
                callee_6: Account(
                    code=bytes.fromhex("6000600460050157005b61600d600055")
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "60006801000000000000000d575b5b61600d600055"
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex("6000640100000009575b5b61600d600055")
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "6000515060016000035060006000515761600d60005500"
                    )
                ),
                callee_10: Account(
                    code=bytes.fromhex("61600d60005560016010602002575b00")
                ),
                callee_11: Account(
                    code=bytes.fromhex("61600d60005560016010602002575b00")
                ),
                callee_12: Account(
                    code=bytes.fromhex("6001600657005b61600d60005500")
                ),
                callee_13: Account(
                    code=bytes.fromhex("61600d60005560ff630fffffff5700")
                ),
                callee_14: Account(
                    code=bytes.fromhex("6023600160085760015b600255")
                ),
                callee_15: Account(
                    code=bytes.fromhex("61600d6000555b6006600657")
                ),
                callee_16: Account(
                    code=bytes.fromhex("61600d6001600a5760ff5b600055")
                ),
                callee_17: Account(
                    code=bytes.fromhex("600b565b61600d600055005b6001600357")
                ),
                callee_18: Account(
                    code=bytes.fromhex("6001600460050157005b61600d600055")
                ),
                callee_19: Account(
                    code=bytes.fromhex("600160075700605b61600d600055")
                ),
                callee_20: Account(
                    code=bytes.fromhex("600160075700600161600d600055")
                ),
                callee_21: Account(
                    code=bytes.fromhex("61600d6000556001600d575a5b5a600155")
                ),
                callee_22: Account(
                    code=bytes.fromhex("61600d6000556001600b575a5b5a600155")
                ),
                callee_23: Account(
                    code=bytes.fromhex(
                        "60116801000000000000000d575b5b61600d600055"
                    )
                ),
                callee_24: Account(
                    code=bytes.fromhex("6011640100000009575b5b61600d600055")
                ),
                callee_25: Account(
                    code=bytes.fromhex(
                        "6000515060016000035060016000515761600d60005500"
                    )
                ),
                contract: Account(
                    storage={0: 2989},
                    code=bytes.fromhex("600060006000600060043562010000f400"),
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
