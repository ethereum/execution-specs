"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
tests/static/state_tests/stEIP150singleCodeGasPrices/eip2929Filler.yml
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
    "048071d3000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
    "048071d3000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
    "048071d3000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000002",  # noqa: E501
    "048071d3000000000000000000000000000000000000000000000000000000000000000b000000000000000000000000000000000000000000000000000000000000000b000000000000000000000000000000000000000000000000000000000000000b",  # noqa: E501
    "048071d3000000000000000000000000000000000000000000000000000000000000000c000000000000000000000000000000000000000000000000000000000000000c000000000000000000000000000000000000000000000000000000000000000c",  # noqa: E501
    "048071d3000000000000000000000000000000000000000000000000000000000000000d000000000000000000000000000000000000000000000000000000000000000d000000000000000000000000000000000000000000000000000000000000000d",  # noqa: E501
    "048071d3000000000000000000000000000000000000000000000000000000000000000e000000000000000000000000000000000000000000000000000000000000000e000000000000000000000000000000000000000000000000000000000000000e",  # noqa: E501
    "048071d3000000000000000000000000000000000000000000000000000000000000001500000000000000000000000000000000000000000000000000000000000000150000000000000000000000000000000000000000000000000000000000000015",  # noqa: E501
    "048071d3000000000000000000000000000000000000000000000000000000000000001600000000000000000000000000000000000000000000000000000000000000160000000000000000000000000000000000000000000000000000000000000016",  # noqa: E501
    "048071d3000000000000000000000000000000000000000000000000000000000000001700000000000000000000000000000000000000000000000000000000000000170000000000000000000000000000000000000000000000000000000000000017",  # noqa: E501
    "048071d3000000000000000000000000000000000000000000000000000000000000001800000000000000000000000000000000000000000000000000000000000000180000000000000000000000000000000000000000000000000000000000000018",  # noqa: E501
    "048071d3000000000000000000000000000000000000000000000000000000000000001f000000000000000000000000000000000000000000000000000000000000001f000000000000000000000000000000000000000000000000000000000000001f",  # noqa: E501
    "048071d3000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000020",  # noqa: E501
    "048071d3000000000000000000000000000000000000000000000000000000000000002100000000000000000000000000000000000000000000000000000000000000210000000000000000000000000000000000000000000000000000000000000021",  # noqa: E501
    "048071d3000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
    "048071d3000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000021",  # noqa: E501
    "048071d3000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000021",  # noqa: E501
    "048071d3000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000021",  # noqa: E501
    "048071d3000000000000000000000000000000000000000000000000000000000000002100000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000002",  # noqa: E501
    "048071d3000000000000000000000000000000000000000000000000000000000000000b000000000000000000000000000000000000000000000000000000000000000c000000000000000000000000000000000000000000000000000000000000000e",  # noqa: E501
    "048071d3000000000000000000000000000000000000000000000000000000000000000b000000000000000000000000000000000000000000000000000000000000000e000000000000000000000000000000000000000000000000000000000000000c",  # noqa: E501
    "048071d3000000000000000000000000000000000000000000000000000000000000000c000000000000000000000000000000000000000000000000000000000000000b000000000000000000000000000000000000000000000000000000000000000e",  # noqa: E501
    "048071d3000000000000000000000000000000000000000000000000000000000000000c000000000000000000000000000000000000000000000000000000000000000e000000000000000000000000000000000000000000000000000000000000000b",  # noqa: E501
    "048071d3000000000000000000000000000000000000000000000000000000000000000e000000000000000000000000000000000000000000000000000000000000000c000000000000000000000000000000000000000000000000000000000000000b",  # noqa: E501
    "048071d3000000000000000000000000000000000000000000000000000000000000000e000000000000000000000000000000000000000000000000000000000000000b000000000000000000000000000000000000000000000000000000000000000c",  # noqa: E501
    "048071d3000000000000000000000000000000000000000000000000000000000000001500000000000000000000000000000000000000000000000000000000000000160000000000000000000000000000000000000000000000000000000000000015",  # noqa: E501
    "048071d3000000000000000000000000000000000000000000000000000000000000001600000000000000000000000000000000000000000000000000000000000000160000000000000000000000000000000000000000000000000000000000000015",  # noqa: E501
    "048071d3000000000000000000000000000000000000000000000000000000000000001700000000000000000000000000000000000000000000000000000000000000180000000000000000000000000000000000000000000000000000000000000017",  # noqa: E501
    "048071d3000000000000000000000000000000000000000000000000000000000000001700000000000000000000000000000000000000000000000000000000000000180000000000000000000000000000000000000000000000000000000000000018",  # noqa: E501
    "048071d3000000000000000000000000000000000000000000000000000000000000000b00000000000000000000000000000000000000000000000000000000000000150000000000000000000000000000000000000000000000000000000000000016",  # noqa: E501
    "048071d3000000000000000000000000000000000000000000000000000000000000000c00000000000000000000000000000000000000000000000000000000000000150000000000000000000000000000000000000000000000000000000000000016",  # noqa: E501
    "048071d3000000000000000000000000000000000000000000000000000000000000000e00000000000000000000000000000000000000000000000000000000000000150000000000000000000000000000000000000000000000000000000000000016",  # noqa: E501
    "048071d3000000000000000000000000000000000000000000000000000000000000000b00000000000000000000000000000000000000000000000000000000000000160000000000000000000000000000000000000000000000000000000000000015",  # noqa: E501
    "048071d3000000000000000000000000000000000000000000000000000000000000000c00000000000000000000000000000000000000000000000000000000000000160000000000000000000000000000000000000000000000000000000000000015",  # noqa: E501
    "048071d3000000000000000000000000000000000000000000000000000000000000000e00000000000000000000000000000000000000000000000000000000000000160000000000000000000000000000000000000000000000000000000000000015",  # noqa: E501
    "048071d3000000000000000000000000000000000000000000000000000000000000000b000000000000000000000000000000000000000000000000000000000000000c000000000000000000000000000000000000000000000000000000000000001f",  # noqa: E501
    "048071d3000000000000000000000000000000000000000000000000000000000000000b000000000000000000000000000000000000000000000000000000000000001f000000000000000000000000000000000000000000000000000000000000000e",  # noqa: E501
    "048071d3000000000000000000000000000000000000000000000000000000000000001f000000000000000000000000000000000000000000000000000000000000000e000000000000000000000000000000000000000000000000000000000000000b",  # noqa: E501
]

TX_GAS = [16777216]

TX_VALUE = [1]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    ["tests/static/state_tests/stEIP150singleCodeGasPrices/eip2929Filler.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(4, 0, 0, id="case0"),
        pytest.param(6, 0, 0, id="case1"),
        pytest.param(19, 0, 0, id="case2"),
        pytest.param(20, 0, 0, id="case3"),
        pytest.param(21, 0, 0, id="case4"),
        pytest.param(22, 0, 0, id="case5"),
        pytest.param(23, 0, 0, id="case6"),
        pytest.param(24, 0, 0, id="case7"),
        pytest.param(3, 0, 0, id="case8"),
        pytest.param(35, 0, 0, id="case9"),
        pytest.param(30, 0, 0, id="case10"),
        pytest.param(31, 0, 0, id="case11"),
        pytest.param(32, 0, 0, id="case12"),
        pytest.param(33, 0, 0, id="case13"),
        pytest.param(34, 0, 0, id="case14"),
        pytest.param(29, 0, 0, id="case15"),
        pytest.param(36, 0, 0, id="case16"),
        pytest.param(10, 0, 0, id="case17"),
        pytest.param(27, 0, 0, id="case18"),
        pytest.param(28, 0, 0, id="case19"),
        pytest.param(9, 0, 0, id="case20"),
        pytest.param(8, 0, 0, id="case21"),
        pytest.param(25, 0, 0, id="case22"),
        pytest.param(26, 0, 0, id="case23"),
        pytest.param(7, 0, 0, id="case24"),
        pytest.param(5, 0, 0, id="case25"),
        pytest.param(37, 0, 0, id="case26"),
        pytest.param(11, 0, 0, id="case27"),
        pytest.param(13, 0, 0, id="case28"),
        pytest.param(18, 0, 0, id="case29"),
        pytest.param(12, 0, 0, id="case30"),
        pytest.param(17, 0, 0, id="case31"),
        pytest.param(0, 0, 0, id="case32"),
        pytest.param(15, 0, 0, id="case33"),
        pytest.param(1, 0, 0, id="case34"),
        pytest.param(16, 0, 0, id="case35"),
        pytest.param(14, 0, 0, id="case36"),
        pytest.param(2, 0, 0, id="case37"),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_eip2929(
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
        code=bytes.fromhex("00"),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x000000000000000000000000000000000000ca11"),  # noqa: E501
    )
    # Source: LLL
    # {
    #     @@0x100
    # }
    callee_1 = pre.deploy_contract(
        code=Op.SLOAD(key=0x100) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x00000000000000000000000000000000ca110100"),  # noqa: E501
    )
    # Source: LLL
    # {
    #      (balance 0xca11)
    # }
    callee_2 = pre.deploy_contract(
        code=Op.BALANCE(address=0xCA11) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x000000000000000000000000000000ca1100ca11"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xBA1A9CE0BA1A9CE)
    # Source: LLL
    # {
    #    (def 'oper1 $4)
    #    (def 'oper2 $36)
    #    (def 'oper3 $68)
    #
    #    (def 'NOP 0)
    #    (def 'measurementCost 0x022a)
    #
    #    (def 'gasB4     0x00)
    #    (def 'gasAfter  0x20)
    #    (def 'operation 0x40)
    #
    #    ; Write to the memory so memory allocation won't affect the
    #    ; measurement
    #    [gasB4] (gas)
    #    [gasAfter] (gas)
    #
    #    ; Read addresses so that won't affect the measurement
    #    (balance 0xca1100ca11)
    #    (balance   0xca110100)
    #
    #    (def 'tests {
    #        (if (= @operation 1) @@0x100 NOP) ; SLOAD
    #        (if (= @operation 2) [[0x100]] 5 NOP) ; SSTORE
    #        (if (= @operation 11) (balance 0xca11) NOP) ; BALANCE
    #        (if (= @operation 12) (extcodesize 0xca11) NOP) ; EXTCODESIZE
    #        (if (= @operation 13) (extcodecopy 0xca11 0 0 0) NOP) ; EXTCODECOPY  # noqa: E501
    #        (if (= @operation 14) (extcodehash 0xca11) NOP) ; EXTCODEHASH
    #        (if (= @operation 21) (call 0x1000 0xca11 0 0 0 0 0) NOP) ; CALL
    #        (if (= @operation 22) (callcode 0x1000 0xca11 0 0 0 0 0) NOP) ; CALLCODE  # noqa: E501
    # ... (35 more lines)
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=Op.GAS)
            + Op.MSTORE(offset=0x20, value=Op.GAS)
            + Op.POP(Op.BALANCE(address=0xCA1100CA11))
            + Op.POP(Op.BALANCE(address=0xCA110100))
            + Op.MSTORE(offset=0x40, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0x0, value=Op.GAS)
            + Op.JUMPI(
                pc=Op.PUSH2[0x31],
                condition=Op.EQ(Op.MLOAD(offset=0x40), 0x1),
            )
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=Op.PUSH2[0x36])
            + Op.JUMPDEST
            + Op.SLOAD(key=0x100)
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPI(
                pc=Op.PUSH2[0x49],
                condition=Op.EQ(Op.MLOAD(offset=0x40), 0x2),
            )
            + Op.POP(0x0)
            + Op.JUMP(pc=Op.PUSH2[0x50])
            + Op.JUMPDEST
            + Op.SSTORE(key=0x100, value=0x5)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=Op.PUSH2[0x61],
                condition=Op.EQ(Op.MLOAD(offset=0x40), 0xB),
            )
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=Op.PUSH2[0x66])
            + Op.JUMPDEST
            + Op.BALANCE(address=0xCA11)
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPI(
                pc=Op.PUSH2[0x78],
                condition=Op.EQ(Op.MLOAD(offset=0x40), 0xC),
            )
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=Op.PUSH2[0x7D])
            + Op.JUMPDEST
            + Op.EXTCODESIZE(address=0xCA11)
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPI(
                pc=Op.PUSH2[0x90],
                condition=Op.EQ(Op.MLOAD(offset=0x40), 0xD),
            )
            + Op.POP(0x0)
            + Op.JUMP(pc=Op.PUSH2[0x9B])
            + Op.JUMPDEST
            + Op.EXTCODECOPY(
                address=0xCA11, dest_offset=0x0, offset=0x0, size=0x0
            )
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=Op.PUSH2[0xAC],
                condition=Op.EQ(Op.MLOAD(offset=0x40), 0xE),
            )
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=Op.PUSH2[0xB1])
            + Op.JUMPDEST
            + Op.EXTCODEHASH(address=0xCA11)
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPI(
                pc=Op.PUSH2[0xC3],
                condition=Op.EQ(Op.MLOAD(offset=0x40), 0x15),
            )
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=Op.PUSH2[0xD5])
            + Op.JUMPDEST
            + Op.CALL(
                gas=0x1000,
                address=0xCA11,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPI(
                pc=Op.PUSH2[0xE7],
                condition=Op.EQ(Op.MLOAD(offset=0x40), 0x16),
            )
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=Op.PUSH2[0xF9])
            + Op.JUMPDEST
            + Op.CALLCODE(
                gas=0x1000,
                address=0xCA11,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPI(pc=0x10B, condition=Op.EQ(Op.MLOAD(offset=0x40), 0x17))
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=0x11B)
            + Op.JUMPDEST
            + Op.DELEGATECALL(
                gas=0x1000,
                address=0xCA11,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPI(pc=0x12D, condition=Op.EQ(Op.MLOAD(offset=0x40), 0x18))
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=0x13D)
            + Op.JUMPDEST
            + Op.STATICCALL(
                gas=0x1000,
                address=0xCA11,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPI(pc=0x14F, condition=Op.EQ(Op.MLOAD(offset=0x40), 0x1F))
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=0x164)
            + Op.JUMPDEST
            + Op.CALL(
                gas=0x1000,
                address=0xCA1100CA11,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPI(pc=0x176, condition=Op.EQ(Op.MLOAD(offset=0x40), 0x20))
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=0x18A)
            + Op.JUMPDEST
            + Op.CALLCODE(
                gas=0x1000,
                address=0xCA110100,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPI(pc=0x19C, condition=Op.EQ(Op.MLOAD(offset=0x40), 0x21))
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=0x1AE)
            + Op.JUMPDEST
            + Op.DELEGATECALL(
                gas=0x1000,
                address=0xCA110100,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.JUMPDEST
            + Op.POP
            + Op.MSTORE(offset=0x20, value=Op.GAS)
            + Op.SSTORE(
                key=0x0,
                value=Op.SUB(
                    Op.SUB(Op.MLOAD(offset=0x0), Op.MLOAD(offset=0x20)),
                    0x22A,
                ),
            )
            + Op.MSTORE(offset=0x40, value=Op.CALLDATALOAD(offset=0x24))
            + Op.MSTORE(offset=0x0, value=Op.GAS)
            + Op.JUMPI(pc=0x1DC, condition=Op.EQ(Op.MLOAD(offset=0x40), 0x1))
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=0x1E1)
            + Op.JUMPDEST
            + Op.SLOAD(key=0x100)
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPI(pc=0x1F4, condition=Op.EQ(Op.MLOAD(offset=0x40), 0x2))
            + Op.POP(0x0)
            + Op.JUMP(pc=0x1FB)
            + Op.JUMPDEST
            + Op.SSTORE(key=0x100, value=0x5)
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x20C, condition=Op.EQ(Op.MLOAD(offset=0x40), 0xB))
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=0x211)
            + Op.JUMPDEST
            + Op.BALANCE(address=0xCA11)
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPI(pc=0x223, condition=Op.EQ(Op.MLOAD(offset=0x40), 0xC))
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=0x228)
            + Op.JUMPDEST
            + Op.EXTCODESIZE(address=0xCA11)
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPI(pc=0x23B, condition=Op.EQ(Op.MLOAD(offset=0x40), 0xD))
            + Op.POP(0x0)
            + Op.JUMP(pc=0x246)
            + Op.JUMPDEST
            + Op.EXTCODECOPY(
                address=0xCA11, dest_offset=0x0, offset=0x0, size=0x0
            )
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x257, condition=Op.EQ(Op.MLOAD(offset=0x40), 0xE))
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=0x25C)
            + Op.JUMPDEST
            + Op.EXTCODEHASH(address=0xCA11)
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPI(pc=0x26E, condition=Op.EQ(Op.MLOAD(offset=0x40), 0x15))
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=0x280)
            + Op.JUMPDEST
            + Op.CALL(
                gas=0x1000,
                address=0xCA11,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPI(pc=0x292, condition=Op.EQ(Op.MLOAD(offset=0x40), 0x16))
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=0x2A4)
            + Op.JUMPDEST
            + Op.CALLCODE(
                gas=0x1000,
                address=0xCA11,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPI(pc=0x2B6, condition=Op.EQ(Op.MLOAD(offset=0x40), 0x17))
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=0x2C6)
            + Op.JUMPDEST
            + Op.DELEGATECALL(
                gas=0x1000,
                address=0xCA11,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPI(pc=0x2D8, condition=Op.EQ(Op.MLOAD(offset=0x40), 0x18))
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=0x2E8)
            + Op.JUMPDEST
            + Op.STATICCALL(
                gas=0x1000,
                address=0xCA11,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPI(pc=0x2FA, condition=Op.EQ(Op.MLOAD(offset=0x40), 0x1F))
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=0x30F)
            + Op.JUMPDEST
            + Op.CALL(
                gas=0x1000,
                address=0xCA1100CA11,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPI(pc=0x321, condition=Op.EQ(Op.MLOAD(offset=0x40), 0x20))
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=0x335)
            + Op.JUMPDEST
            + Op.CALLCODE(
                gas=0x1000,
                address=0xCA110100,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPI(pc=0x347, condition=Op.EQ(Op.MLOAD(offset=0x40), 0x21))
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=0x359)
            + Op.JUMPDEST
            + Op.DELEGATECALL(
                gas=0x1000,
                address=0xCA110100,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.JUMPDEST
            + Op.POP
            + Op.MSTORE(offset=0x20, value=Op.GAS)
            + Op.SSTORE(
                key=0x1,
                value=Op.SUB(
                    Op.SUB(Op.MLOAD(offset=0x0), Op.MLOAD(offset=0x20)),
                    0x22A,
                ),
            )
            + Op.MSTORE(offset=0x40, value=Op.CALLDATALOAD(offset=0x44))
            + Op.MSTORE(offset=0x0, value=Op.GAS)
            + Op.JUMPI(pc=0x387, condition=Op.EQ(Op.MLOAD(offset=0x40), 0x1))
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=0x38C)
            + Op.JUMPDEST
            + Op.SLOAD(key=0x100)
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPI(pc=0x39F, condition=Op.EQ(Op.MLOAD(offset=0x40), 0x2))
            + Op.POP(0x0)
            + Op.JUMP(pc=0x3A6)
            + Op.JUMPDEST
            + Op.SSTORE(key=0x100, value=0x5)
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x3B7, condition=Op.EQ(Op.MLOAD(offset=0x40), 0xB))
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=0x3BC)
            + Op.JUMPDEST
            + Op.BALANCE(address=0xCA11)
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPI(pc=0x3CE, condition=Op.EQ(Op.MLOAD(offset=0x40), 0xC))
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=0x3D3)
            + Op.JUMPDEST
            + Op.EXTCODESIZE(address=0xCA11)
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPI(pc=0x3E6, condition=Op.EQ(Op.MLOAD(offset=0x40), 0xD))
            + Op.POP(0x0)
            + Op.JUMP(pc=0x3F1)
            + Op.JUMPDEST
            + Op.EXTCODECOPY(
                address=0xCA11, dest_offset=0x0, offset=0x0, size=0x0
            )
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x402, condition=Op.EQ(Op.MLOAD(offset=0x40), 0xE))
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=0x407)
            + Op.JUMPDEST
            + Op.EXTCODEHASH(address=0xCA11)
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPI(pc=0x419, condition=Op.EQ(Op.MLOAD(offset=0x40), 0x15))
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=0x42B)
            + Op.JUMPDEST
            + Op.CALL(
                gas=0x1000,
                address=0xCA11,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPI(pc=0x43D, condition=Op.EQ(Op.MLOAD(offset=0x40), 0x16))
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=0x44F)
            + Op.JUMPDEST
            + Op.CALLCODE(
                gas=0x1000,
                address=0xCA11,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPI(pc=0x461, condition=Op.EQ(Op.MLOAD(offset=0x40), 0x17))
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=0x471)
            + Op.JUMPDEST
            + Op.DELEGATECALL(
                gas=0x1000,
                address=0xCA11,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPI(pc=0x483, condition=Op.EQ(Op.MLOAD(offset=0x40), 0x18))
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=0x493)
            + Op.JUMPDEST
            + Op.STATICCALL(
                gas=0x1000,
                address=0xCA11,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPI(pc=0x4A5, condition=Op.EQ(Op.MLOAD(offset=0x40), 0x1F))
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=0x4BA)
            + Op.JUMPDEST
            + Op.CALL(
                gas=0x1000,
                address=0xCA1100CA11,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPI(pc=0x4CC, condition=Op.EQ(Op.MLOAD(offset=0x40), 0x20))
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=0x4E0)
            + Op.JUMPDEST
            + Op.CALLCODE(
                gas=0x1000,
                address=0xCA110100,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMPI(pc=0x4F2, condition=Op.EQ(Op.MLOAD(offset=0x40), 0x21))
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=0x504)
            + Op.JUMPDEST
            + Op.DELEGATECALL(
                gas=0x1000,
                address=0xCA110100,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.JUMPDEST
            + Op.POP
            + Op.MSTORE(offset=0x20, value=Op.GAS)
            + Op.SSTORE(
                key=0x2,
                value=Op.SUB(
                    Op.SUB(Op.MLOAD(offset=0x0), Op.MLOAD(offset=0x20)),
                    0x22A,
                ),
            )
            + Op.SSTORE(key=0x100, value=0x0)
            + Op.STOP
        ),
        storage={0x100: 0x60A7},
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0xcccccccccccccccccccccccccccccccccccccccc"),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 4, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("00")),
                callee_1: Account(code=bytes.fromhex("6101005400")),
                callee_2: Account(code=bytes.fromhex("61ca113100")),
                contract: Account(
                    storage={0: 2590, 1: 90, 2: 90},
                    code=bytes.fromhex(
                        "5a6000525a60205264ca1100ca11315063ca11010031506004356040525a600052600160405114610031576000610036565b610100545b5060026040511461004957600050610050565b6005610100555b600b60405114610061576000610066565b61ca11315b50600c6040511461007857600061007d565b61ca113b5b50600d604051146100905760005061009b565b60006000600061ca113c5b600e604051146100ac5760006100b1565b61ca113f5b506015604051146100c35760006100d5565b6000600060006000600061ca11611000f15b506016604051146100e75760006100f9565b6000600060006000600061ca11611000f25b5060176040511461010b57600061011b565b600060006000600061ca11611000f45b5060186040511461012d57600061013d565b600060006000600061ca11611000fa5b50601f6040511461014f576000610164565b6000600060006000600064ca1100ca11611000f15b5060206040511461017657600061018a565b6000600060006000600063ca110100611000f25b5060216040511461019c5760006101ae565b600060006000600063ca110100611000f45b505a60205261022a60205160005103036000556024356040525a6000526001604051146101dc5760006101e1565b610100545b506002604051146101f4576000506101fb565b6005610100555b600b6040511461020c576000610211565b61ca11315b50600c60405114610223576000610228565b61ca113b5b50600d6040511461023b57600050610246565b60006000600061ca113c5b600e6040511461025757600061025c565b61ca113f5b5060156040511461026e576000610280565b6000600060006000600061ca11611000f15b506016604051146102925760006102a4565b6000600060006000600061ca11611000f25b506017604051146102b65760006102c6565b600060006000600061ca11611000f45b506018604051146102d85760006102e8565b600060006000600061ca11611000fa5b50601f604051146102fa57600061030f565b6000600060006000600064ca1100ca11611000f15b50602060405114610321576000610335565b6000600060006000600063ca110100611000f25b50602160405114610347576000610359565b600060006000600063ca110100611000f45b505a60205261022a60205160005103036001556044356040525a60005260016040511461038757600061038c565b610100545b5060026040511461039f576000506103a6565b6005610100555b600b604051146103b75760006103bc565b61ca11315b50600c604051146103ce5760006103d3565b61ca113b5b50600d604051146103e6576000506103f1565b60006000600061ca113c5b600e60405114610402576000610407565b61ca113f5b5060156040511461041957600061042b565b6000600060006000600061ca11611000f15b5060166040511461043d57600061044f565b6000600060006000600061ca11611000f25b50601760405114610461576000610471565b600060006000600061ca11611000f45b50601860405114610483576000610493565b600060006000600061ca11611000fa5b50601f604051146104a55760006104ba565b6000600060006000600064ca1100ca11611000f15b506020604051146104cc5760006104e0565b6000600060006000600063ca110100611000f25b506021604051146104f2576000610504565b600060006000600063ca110100611000f45b505a60205261022a602051600051030360025560006101005500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 6, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("00")),
                callee_1: Account(code=bytes.fromhex("6101005400")),
                callee_2: Account(code=bytes.fromhex("61ca113100")),
                contract: Account(
                    storage={0: 2590, 1: 90, 2: 90},
                    code=bytes.fromhex(
                        "5a6000525a60205264ca1100ca11315063ca11010031506004356040525a600052600160405114610031576000610036565b610100545b5060026040511461004957600050610050565b6005610100555b600b60405114610061576000610066565b61ca11315b50600c6040511461007857600061007d565b61ca113b5b50600d604051146100905760005061009b565b60006000600061ca113c5b600e604051146100ac5760006100b1565b61ca113f5b506015604051146100c35760006100d5565b6000600060006000600061ca11611000f15b506016604051146100e75760006100f9565b6000600060006000600061ca11611000f25b5060176040511461010b57600061011b565b600060006000600061ca11611000f45b5060186040511461012d57600061013d565b600060006000600061ca11611000fa5b50601f6040511461014f576000610164565b6000600060006000600064ca1100ca11611000f15b5060206040511461017657600061018a565b6000600060006000600063ca110100611000f25b5060216040511461019c5760006101ae565b600060006000600063ca110100611000f45b505a60205261022a60205160005103036000556024356040525a6000526001604051146101dc5760006101e1565b610100545b506002604051146101f4576000506101fb565b6005610100555b600b6040511461020c576000610211565b61ca11315b50600c60405114610223576000610228565b61ca113b5b50600d6040511461023b57600050610246565b60006000600061ca113c5b600e6040511461025757600061025c565b61ca113f5b5060156040511461026e576000610280565b6000600060006000600061ca11611000f15b506016604051146102925760006102a4565b6000600060006000600061ca11611000f25b506017604051146102b65760006102c6565b600060006000600061ca11611000f45b506018604051146102d85760006102e8565b600060006000600061ca11611000fa5b50601f604051146102fa57600061030f565b6000600060006000600064ca1100ca11611000f15b50602060405114610321576000610335565b6000600060006000600063ca110100611000f25b50602160405114610347576000610359565b600060006000600063ca110100611000f45b505a60205261022a60205160005103036001556044356040525a60005260016040511461038757600061038c565b610100545b5060026040511461039f576000506103a6565b6005610100555b600b604051146103b75760006103bc565b61ca11315b50600c604051146103ce5760006103d3565b61ca113b5b50600d604051146103e6576000506103f1565b60006000600061ca113c5b600e60405114610402576000610407565b61ca113f5b5060156040511461041957600061042b565b6000600060006000600061ca11611000f15b5060166040511461043d57600061044f565b6000600060006000600061ca11611000f25b50601760405114610461576000610471565b600060006000600061ca11611000f45b50601860405114610483576000610493565b600060006000600061ca11611000fa5b50601f604051146104a55760006104ba565b6000600060006000600064ca1100ca11611000f15b506020604051146104cc5760006104e0565b6000600060006000600063ca110100611000f25b506021604051146104f2576000610504565b600060006000600063ca110100611000f45b505a60205261022a602051600051030360025560006101005500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 19, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("00")),
                callee_1: Account(code=bytes.fromhex("6101005400")),
                callee_2: Account(code=bytes.fromhex("61ca113100")),
                contract: Account(
                    storage={0: 2590, 1: 90, 2: 90},
                    code=bytes.fromhex(
                        "5a6000525a60205264ca1100ca11315063ca11010031506004356040525a600052600160405114610031576000610036565b610100545b5060026040511461004957600050610050565b6005610100555b600b60405114610061576000610066565b61ca11315b50600c6040511461007857600061007d565b61ca113b5b50600d604051146100905760005061009b565b60006000600061ca113c5b600e604051146100ac5760006100b1565b61ca113f5b506015604051146100c35760006100d5565b6000600060006000600061ca11611000f15b506016604051146100e75760006100f9565b6000600060006000600061ca11611000f25b5060176040511461010b57600061011b565b600060006000600061ca11611000f45b5060186040511461012d57600061013d565b600060006000600061ca11611000fa5b50601f6040511461014f576000610164565b6000600060006000600064ca1100ca11611000f15b5060206040511461017657600061018a565b6000600060006000600063ca110100611000f25b5060216040511461019c5760006101ae565b600060006000600063ca110100611000f45b505a60205261022a60205160005103036000556024356040525a6000526001604051146101dc5760006101e1565b610100545b506002604051146101f4576000506101fb565b6005610100555b600b6040511461020c576000610211565b61ca11315b50600c60405114610223576000610228565b61ca113b5b50600d6040511461023b57600050610246565b60006000600061ca113c5b600e6040511461025757600061025c565b61ca113f5b5060156040511461026e576000610280565b6000600060006000600061ca11611000f15b506016604051146102925760006102a4565b6000600060006000600061ca11611000f25b506017604051146102b65760006102c6565b600060006000600061ca11611000f45b506018604051146102d85760006102e8565b600060006000600061ca11611000fa5b50601f604051146102fa57600061030f565b6000600060006000600064ca1100ca11611000f15b50602060405114610321576000610335565b6000600060006000600063ca110100611000f25b50602160405114610347576000610359565b600060006000600063ca110100611000f45b505a60205261022a60205160005103036001556044356040525a60005260016040511461038757600061038c565b610100545b5060026040511461039f576000506103a6565b6005610100555b600b604051146103b75760006103bc565b61ca11315b50600c604051146103ce5760006103d3565b61ca113b5b50600d604051146103e6576000506103f1565b60006000600061ca113c5b600e60405114610402576000610407565b61ca113f5b5060156040511461041957600061042b565b6000600060006000600061ca11611000f15b5060166040511461043d57600061044f565b6000600060006000600061ca11611000f25b50601760405114610461576000610471565b600060006000600061ca11611000f45b50601860405114610483576000610493565b600060006000600061ca11611000fa5b50601f604051146104a55760006104ba565b6000600060006000600064ca1100ca11611000f15b506020604051146104cc5760006104e0565b6000600060006000600063ca110100611000f25b506021604051146104f2576000610504565b600060006000600063ca110100611000f45b505a60205261022a602051600051030360025560006101005500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 20, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("00")),
                callee_1: Account(code=bytes.fromhex("6101005400")),
                callee_2: Account(code=bytes.fromhex("61ca113100")),
                contract: Account(
                    storage={0: 2590, 1: 90, 2: 90},
                    code=bytes.fromhex(
                        "5a6000525a60205264ca1100ca11315063ca11010031506004356040525a600052600160405114610031576000610036565b610100545b5060026040511461004957600050610050565b6005610100555b600b60405114610061576000610066565b61ca11315b50600c6040511461007857600061007d565b61ca113b5b50600d604051146100905760005061009b565b60006000600061ca113c5b600e604051146100ac5760006100b1565b61ca113f5b506015604051146100c35760006100d5565b6000600060006000600061ca11611000f15b506016604051146100e75760006100f9565b6000600060006000600061ca11611000f25b5060176040511461010b57600061011b565b600060006000600061ca11611000f45b5060186040511461012d57600061013d565b600060006000600061ca11611000fa5b50601f6040511461014f576000610164565b6000600060006000600064ca1100ca11611000f15b5060206040511461017657600061018a565b6000600060006000600063ca110100611000f25b5060216040511461019c5760006101ae565b600060006000600063ca110100611000f45b505a60205261022a60205160005103036000556024356040525a6000526001604051146101dc5760006101e1565b610100545b506002604051146101f4576000506101fb565b6005610100555b600b6040511461020c576000610211565b61ca11315b50600c60405114610223576000610228565b61ca113b5b50600d6040511461023b57600050610246565b60006000600061ca113c5b600e6040511461025757600061025c565b61ca113f5b5060156040511461026e576000610280565b6000600060006000600061ca11611000f15b506016604051146102925760006102a4565b6000600060006000600061ca11611000f25b506017604051146102b65760006102c6565b600060006000600061ca11611000f45b506018604051146102d85760006102e8565b600060006000600061ca11611000fa5b50601f604051146102fa57600061030f565b6000600060006000600064ca1100ca11611000f15b50602060405114610321576000610335565b6000600060006000600063ca110100611000f25b50602160405114610347576000610359565b600060006000600063ca110100611000f45b505a60205261022a60205160005103036001556044356040525a60005260016040511461038757600061038c565b610100545b5060026040511461039f576000506103a6565b6005610100555b600b604051146103b75760006103bc565b61ca11315b50600c604051146103ce5760006103d3565b61ca113b5b50600d604051146103e6576000506103f1565b60006000600061ca113c5b600e60405114610402576000610407565b61ca113f5b5060156040511461041957600061042b565b6000600060006000600061ca11611000f15b5060166040511461043d57600061044f565b6000600060006000600061ca11611000f25b50601760405114610461576000610471565b600060006000600061ca11611000f45b50601860405114610483576000610493565b600060006000600061ca11611000fa5b50601f604051146104a55760006104ba565b6000600060006000600064ca1100ca11611000f15b506020604051146104cc5760006104e0565b6000600060006000600063ca110100611000f25b506021604051146104f2576000610504565b600060006000600063ca110100611000f45b505a60205261022a602051600051030360025560006101005500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 21, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("00")),
                callee_1: Account(code=bytes.fromhex("6101005400")),
                callee_2: Account(code=bytes.fromhex("61ca113100")),
                contract: Account(
                    storage={0: 2590, 1: 90, 2: 90},
                    code=bytes.fromhex(
                        "5a6000525a60205264ca1100ca11315063ca11010031506004356040525a600052600160405114610031576000610036565b610100545b5060026040511461004957600050610050565b6005610100555b600b60405114610061576000610066565b61ca11315b50600c6040511461007857600061007d565b61ca113b5b50600d604051146100905760005061009b565b60006000600061ca113c5b600e604051146100ac5760006100b1565b61ca113f5b506015604051146100c35760006100d5565b6000600060006000600061ca11611000f15b506016604051146100e75760006100f9565b6000600060006000600061ca11611000f25b5060176040511461010b57600061011b565b600060006000600061ca11611000f45b5060186040511461012d57600061013d565b600060006000600061ca11611000fa5b50601f6040511461014f576000610164565b6000600060006000600064ca1100ca11611000f15b5060206040511461017657600061018a565b6000600060006000600063ca110100611000f25b5060216040511461019c5760006101ae565b600060006000600063ca110100611000f45b505a60205261022a60205160005103036000556024356040525a6000526001604051146101dc5760006101e1565b610100545b506002604051146101f4576000506101fb565b6005610100555b600b6040511461020c576000610211565b61ca11315b50600c60405114610223576000610228565b61ca113b5b50600d6040511461023b57600050610246565b60006000600061ca113c5b600e6040511461025757600061025c565b61ca113f5b5060156040511461026e576000610280565b6000600060006000600061ca11611000f15b506016604051146102925760006102a4565b6000600060006000600061ca11611000f25b506017604051146102b65760006102c6565b600060006000600061ca11611000f45b506018604051146102d85760006102e8565b600060006000600061ca11611000fa5b50601f604051146102fa57600061030f565b6000600060006000600064ca1100ca11611000f15b50602060405114610321576000610335565b6000600060006000600063ca110100611000f25b50602160405114610347576000610359565b600060006000600063ca110100611000f45b505a60205261022a60205160005103036001556044356040525a60005260016040511461038757600061038c565b610100545b5060026040511461039f576000506103a6565b6005610100555b600b604051146103b75760006103bc565b61ca11315b50600c604051146103ce5760006103d3565b61ca113b5b50600d604051146103e6576000506103f1565b60006000600061ca113c5b600e60405114610402576000610407565b61ca113f5b5060156040511461041957600061042b565b6000600060006000600061ca11611000f15b5060166040511461043d57600061044f565b6000600060006000600061ca11611000f25b50601760405114610461576000610471565b600060006000600061ca11611000f45b50601860405114610483576000610493565b600060006000600061ca11611000fa5b50601f604051146104a55760006104ba565b6000600060006000600064ca1100ca11611000f15b506020604051146104cc5760006104e0565b6000600060006000600063ca110100611000f25b506021604051146104f2576000610504565b600060006000600063ca110100611000f45b505a60205261022a602051600051030360025560006101005500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 22, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("00")),
                callee_1: Account(code=bytes.fromhex("6101005400")),
                callee_2: Account(code=bytes.fromhex("61ca113100")),
                contract: Account(
                    storage={0: 2590, 1: 90, 2: 90},
                    code=bytes.fromhex(
                        "5a6000525a60205264ca1100ca11315063ca11010031506004356040525a600052600160405114610031576000610036565b610100545b5060026040511461004957600050610050565b6005610100555b600b60405114610061576000610066565b61ca11315b50600c6040511461007857600061007d565b61ca113b5b50600d604051146100905760005061009b565b60006000600061ca113c5b600e604051146100ac5760006100b1565b61ca113f5b506015604051146100c35760006100d5565b6000600060006000600061ca11611000f15b506016604051146100e75760006100f9565b6000600060006000600061ca11611000f25b5060176040511461010b57600061011b565b600060006000600061ca11611000f45b5060186040511461012d57600061013d565b600060006000600061ca11611000fa5b50601f6040511461014f576000610164565b6000600060006000600064ca1100ca11611000f15b5060206040511461017657600061018a565b6000600060006000600063ca110100611000f25b5060216040511461019c5760006101ae565b600060006000600063ca110100611000f45b505a60205261022a60205160005103036000556024356040525a6000526001604051146101dc5760006101e1565b610100545b506002604051146101f4576000506101fb565b6005610100555b600b6040511461020c576000610211565b61ca11315b50600c60405114610223576000610228565b61ca113b5b50600d6040511461023b57600050610246565b60006000600061ca113c5b600e6040511461025757600061025c565b61ca113f5b5060156040511461026e576000610280565b6000600060006000600061ca11611000f15b506016604051146102925760006102a4565b6000600060006000600061ca11611000f25b506017604051146102b65760006102c6565b600060006000600061ca11611000f45b506018604051146102d85760006102e8565b600060006000600061ca11611000fa5b50601f604051146102fa57600061030f565b6000600060006000600064ca1100ca11611000f15b50602060405114610321576000610335565b6000600060006000600063ca110100611000f25b50602160405114610347576000610359565b600060006000600063ca110100611000f45b505a60205261022a60205160005103036001556044356040525a60005260016040511461038757600061038c565b610100545b5060026040511461039f576000506103a6565b6005610100555b600b604051146103b75760006103bc565b61ca11315b50600c604051146103ce5760006103d3565b61ca113b5b50600d604051146103e6576000506103f1565b60006000600061ca113c5b600e60405114610402576000610407565b61ca113f5b5060156040511461041957600061042b565b6000600060006000600061ca11611000f15b5060166040511461043d57600061044f565b6000600060006000600061ca11611000f25b50601760405114610461576000610471565b600060006000600061ca11611000f45b50601860405114610483576000610493565b600060006000600061ca11611000fa5b50601f604051146104a55760006104ba565b6000600060006000600064ca1100ca11611000f15b506020604051146104cc5760006104e0565b6000600060006000600063ca110100611000f25b506021604051146104f2576000610504565b600060006000600063ca110100611000f45b505a60205261022a602051600051030360025560006101005500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 23, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("00")),
                callee_1: Account(code=bytes.fromhex("6101005400")),
                callee_2: Account(code=bytes.fromhex("61ca113100")),
                contract: Account(
                    storage={0: 2590, 1: 90, 2: 90},
                    code=bytes.fromhex(
                        "5a6000525a60205264ca1100ca11315063ca11010031506004356040525a600052600160405114610031576000610036565b610100545b5060026040511461004957600050610050565b6005610100555b600b60405114610061576000610066565b61ca11315b50600c6040511461007857600061007d565b61ca113b5b50600d604051146100905760005061009b565b60006000600061ca113c5b600e604051146100ac5760006100b1565b61ca113f5b506015604051146100c35760006100d5565b6000600060006000600061ca11611000f15b506016604051146100e75760006100f9565b6000600060006000600061ca11611000f25b5060176040511461010b57600061011b565b600060006000600061ca11611000f45b5060186040511461012d57600061013d565b600060006000600061ca11611000fa5b50601f6040511461014f576000610164565b6000600060006000600064ca1100ca11611000f15b5060206040511461017657600061018a565b6000600060006000600063ca110100611000f25b5060216040511461019c5760006101ae565b600060006000600063ca110100611000f45b505a60205261022a60205160005103036000556024356040525a6000526001604051146101dc5760006101e1565b610100545b506002604051146101f4576000506101fb565b6005610100555b600b6040511461020c576000610211565b61ca11315b50600c60405114610223576000610228565b61ca113b5b50600d6040511461023b57600050610246565b60006000600061ca113c5b600e6040511461025757600061025c565b61ca113f5b5060156040511461026e576000610280565b6000600060006000600061ca11611000f15b506016604051146102925760006102a4565b6000600060006000600061ca11611000f25b506017604051146102b65760006102c6565b600060006000600061ca11611000f45b506018604051146102d85760006102e8565b600060006000600061ca11611000fa5b50601f604051146102fa57600061030f565b6000600060006000600064ca1100ca11611000f15b50602060405114610321576000610335565b6000600060006000600063ca110100611000f25b50602160405114610347576000610359565b600060006000600063ca110100611000f45b505a60205261022a60205160005103036001556044356040525a60005260016040511461038757600061038c565b610100545b5060026040511461039f576000506103a6565b6005610100555b600b604051146103b75760006103bc565b61ca11315b50600c604051146103ce5760006103d3565b61ca113b5b50600d604051146103e6576000506103f1565b60006000600061ca113c5b600e60405114610402576000610407565b61ca113f5b5060156040511461041957600061042b565b6000600060006000600061ca11611000f15b5060166040511461043d57600061044f565b6000600060006000600061ca11611000f25b50601760405114610461576000610471565b600060006000600061ca11611000f45b50601860405114610483576000610493565b600060006000600061ca11611000fa5b50601f604051146104a55760006104ba565b6000600060006000600064ca1100ca11611000f15b506020604051146104cc5760006104e0565b6000600060006000600063ca110100611000f25b506021604051146104f2576000610504565b600060006000600063ca110100611000f45b505a60205261022a602051600051030360025560006101005500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 24, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("00")),
                callee_1: Account(code=bytes.fromhex("6101005400")),
                callee_2: Account(code=bytes.fromhex("61ca113100")),
                contract: Account(
                    storage={0: 2590, 1: 90, 2: 90},
                    code=bytes.fromhex(
                        "5a6000525a60205264ca1100ca11315063ca11010031506004356040525a600052600160405114610031576000610036565b610100545b5060026040511461004957600050610050565b6005610100555b600b60405114610061576000610066565b61ca11315b50600c6040511461007857600061007d565b61ca113b5b50600d604051146100905760005061009b565b60006000600061ca113c5b600e604051146100ac5760006100b1565b61ca113f5b506015604051146100c35760006100d5565b6000600060006000600061ca11611000f15b506016604051146100e75760006100f9565b6000600060006000600061ca11611000f25b5060176040511461010b57600061011b565b600060006000600061ca11611000f45b5060186040511461012d57600061013d565b600060006000600061ca11611000fa5b50601f6040511461014f576000610164565b6000600060006000600064ca1100ca11611000f15b5060206040511461017657600061018a565b6000600060006000600063ca110100611000f25b5060216040511461019c5760006101ae565b600060006000600063ca110100611000f45b505a60205261022a60205160005103036000556024356040525a6000526001604051146101dc5760006101e1565b610100545b506002604051146101f4576000506101fb565b6005610100555b600b6040511461020c576000610211565b61ca11315b50600c60405114610223576000610228565b61ca113b5b50600d6040511461023b57600050610246565b60006000600061ca113c5b600e6040511461025757600061025c565b61ca113f5b5060156040511461026e576000610280565b6000600060006000600061ca11611000f15b506016604051146102925760006102a4565b6000600060006000600061ca11611000f25b506017604051146102b65760006102c6565b600060006000600061ca11611000f45b506018604051146102d85760006102e8565b600060006000600061ca11611000fa5b50601f604051146102fa57600061030f565b6000600060006000600064ca1100ca11611000f15b50602060405114610321576000610335565b6000600060006000600063ca110100611000f25b50602160405114610347576000610359565b600060006000600063ca110100611000f45b505a60205261022a60205160005103036001556044356040525a60005260016040511461038757600061038c565b610100545b5060026040511461039f576000506103a6565b6005610100555b600b604051146103b75760006103bc565b61ca11315b50600c604051146103ce5760006103d3565b61ca113b5b50600d604051146103e6576000506103f1565b60006000600061ca113c5b600e60405114610402576000610407565b61ca113f5b5060156040511461041957600061042b565b6000600060006000600061ca11611000f15b5060166040511461043d57600061044f565b6000600060006000600061ca11611000f25b50601760405114610461576000610471565b600060006000600061ca11611000f45b50601860405114610483576000610493565b600060006000600061ca11611000fa5b50601f604051146104a55760006104ba565b6000600060006000600064ca1100ca11611000f15b506020604051146104cc5760006104e0565b6000600060006000600063ca110100611000f25b506021604051146104f2576000610504565b600060006000600063ca110100611000f45b505a60205261022a602051600051030360025560006101005500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 3, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("00")),
                callee_1: Account(code=bytes.fromhex("6101005400")),
                callee_2: Account(code=bytes.fromhex("61ca113100")),
                contract: Account(
                    storage={0: 2590, 1: 90, 2: 90},
                    code=bytes.fromhex(
                        "5a6000525a60205264ca1100ca11315063ca11010031506004356040525a600052600160405114610031576000610036565b610100545b5060026040511461004957600050610050565b6005610100555b600b60405114610061576000610066565b61ca11315b50600c6040511461007857600061007d565b61ca113b5b50600d604051146100905760005061009b565b60006000600061ca113c5b600e604051146100ac5760006100b1565b61ca113f5b506015604051146100c35760006100d5565b6000600060006000600061ca11611000f15b506016604051146100e75760006100f9565b6000600060006000600061ca11611000f25b5060176040511461010b57600061011b565b600060006000600061ca11611000f45b5060186040511461012d57600061013d565b600060006000600061ca11611000fa5b50601f6040511461014f576000610164565b6000600060006000600064ca1100ca11611000f15b5060206040511461017657600061018a565b6000600060006000600063ca110100611000f25b5060216040511461019c5760006101ae565b600060006000600063ca110100611000f45b505a60205261022a60205160005103036000556024356040525a6000526001604051146101dc5760006101e1565b610100545b506002604051146101f4576000506101fb565b6005610100555b600b6040511461020c576000610211565b61ca11315b50600c60405114610223576000610228565b61ca113b5b50600d6040511461023b57600050610246565b60006000600061ca113c5b600e6040511461025757600061025c565b61ca113f5b5060156040511461026e576000610280565b6000600060006000600061ca11611000f15b506016604051146102925760006102a4565b6000600060006000600061ca11611000f25b506017604051146102b65760006102c6565b600060006000600061ca11611000f45b506018604051146102d85760006102e8565b600060006000600061ca11611000fa5b50601f604051146102fa57600061030f565b6000600060006000600064ca1100ca11611000f15b50602060405114610321576000610335565b6000600060006000600063ca110100611000f25b50602160405114610347576000610359565b600060006000600063ca110100611000f45b505a60205261022a60205160005103036001556044356040525a60005260016040511461038757600061038c565b610100545b5060026040511461039f576000506103a6565b6005610100555b600b604051146103b75760006103bc565b61ca11315b50600c604051146103ce5760006103d3565b61ca113b5b50600d604051146103e6576000506103f1565b60006000600061ca113c5b600e60405114610402576000610407565b61ca113f5b5060156040511461041957600061042b565b6000600060006000600061ca11611000f15b5060166040511461043d57600061044f565b6000600060006000600061ca11611000f25b50601760405114610461576000610471565b600060006000600061ca11611000f45b50601860405114610483576000610493565b600060006000600061ca11611000fa5b50601f604051146104a55760006104ba565b6000600060006000600064ca1100ca11611000f15b506020604051146104cc5760006104e0565b6000600060006000600063ca110100611000f25b506021604051146104f2576000610504565b600060006000600063ca110100611000f45b505a60205261022a602051600051030360025560006101005500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 35, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("00")),
                callee_1: Account(code=bytes.fromhex("6101005400")),
                callee_2: Account(code=bytes.fromhex("61ca113100")),
                contract: Account(
                    storage={0: 2590, 1: 90, 2: 211},
                    code=bytes.fromhex(
                        "5a6000525a60205264ca1100ca11315063ca11010031506004356040525a600052600160405114610031576000610036565b610100545b5060026040511461004957600050610050565b6005610100555b600b60405114610061576000610066565b61ca11315b50600c6040511461007857600061007d565b61ca113b5b50600d604051146100905760005061009b565b60006000600061ca113c5b600e604051146100ac5760006100b1565b61ca113f5b506015604051146100c35760006100d5565b6000600060006000600061ca11611000f15b506016604051146100e75760006100f9565b6000600060006000600061ca11611000f25b5060176040511461010b57600061011b565b600060006000600061ca11611000f45b5060186040511461012d57600061013d565b600060006000600061ca11611000fa5b50601f6040511461014f576000610164565b6000600060006000600064ca1100ca11611000f15b5060206040511461017657600061018a565b6000600060006000600063ca110100611000f25b5060216040511461019c5760006101ae565b600060006000600063ca110100611000f45b505a60205261022a60205160005103036000556024356040525a6000526001604051146101dc5760006101e1565b610100545b506002604051146101f4576000506101fb565b6005610100555b600b6040511461020c576000610211565b61ca11315b50600c60405114610223576000610228565b61ca113b5b50600d6040511461023b57600050610246565b60006000600061ca113c5b600e6040511461025757600061025c565b61ca113f5b5060156040511461026e576000610280565b6000600060006000600061ca11611000f15b506016604051146102925760006102a4565b6000600060006000600061ca11611000f25b506017604051146102b65760006102c6565b600060006000600061ca11611000f45b506018604051146102d85760006102e8565b600060006000600061ca11611000fa5b50601f604051146102fa57600061030f565b6000600060006000600064ca1100ca11611000f15b50602060405114610321576000610335565b6000600060006000600063ca110100611000f25b50602160405114610347576000610359565b600060006000600063ca110100611000f45b505a60205261022a60205160005103036001556044356040525a60005260016040511461038757600061038c565b610100545b5060026040511461039f576000506103a6565b6005610100555b600b604051146103b75760006103bc565b61ca11315b50600c604051146103ce5760006103d3565b61ca113b5b50600d604051146103e6576000506103f1565b60006000600061ca113c5b600e60405114610402576000610407565b61ca113f5b5060156040511461041957600061042b565b6000600060006000600061ca11611000f15b5060166040511461043d57600061044f565b6000600060006000600061ca11611000f25b50601760405114610461576000610471565b600060006000600061ca11611000f45b50601860405114610483576000610493565b600060006000600061ca11611000fa5b50601f604051146104a55760006104ba565b6000600060006000600064ca1100ca11611000f15b506020604051146104cc5760006104e0565b6000600060006000600063ca110100611000f25b506021604051146104f2576000610504565b600060006000600063ca110100611000f45b505a60205261022a602051600051030360025560006101005500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 30, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("00")),
                callee_1: Account(code=bytes.fromhex("6101005400")),
                callee_2: Account(code=bytes.fromhex("61ca113100")),
                contract: Account(
                    storage={0: 2590, 1: 108, 2: 108},
                    code=bytes.fromhex(
                        "5a6000525a60205264ca1100ca11315063ca11010031506004356040525a600052600160405114610031576000610036565b610100545b5060026040511461004957600050610050565b6005610100555b600b60405114610061576000610066565b61ca11315b50600c6040511461007857600061007d565b61ca113b5b50600d604051146100905760005061009b565b60006000600061ca113c5b600e604051146100ac5760006100b1565b61ca113f5b506015604051146100c35760006100d5565b6000600060006000600061ca11611000f15b506016604051146100e75760006100f9565b6000600060006000600061ca11611000f25b5060176040511461010b57600061011b565b600060006000600061ca11611000f45b5060186040511461012d57600061013d565b600060006000600061ca11611000fa5b50601f6040511461014f576000610164565b6000600060006000600064ca1100ca11611000f15b5060206040511461017657600061018a565b6000600060006000600063ca110100611000f25b5060216040511461019c5760006101ae565b600060006000600063ca110100611000f45b505a60205261022a60205160005103036000556024356040525a6000526001604051146101dc5760006101e1565b610100545b506002604051146101f4576000506101fb565b6005610100555b600b6040511461020c576000610211565b61ca11315b50600c60405114610223576000610228565b61ca113b5b50600d6040511461023b57600050610246565b60006000600061ca113c5b600e6040511461025757600061025c565b61ca113f5b5060156040511461026e576000610280565b6000600060006000600061ca11611000f15b506016604051146102925760006102a4565b6000600060006000600061ca11611000f25b506017604051146102b65760006102c6565b600060006000600061ca11611000f45b506018604051146102d85760006102e8565b600060006000600061ca11611000fa5b50601f604051146102fa57600061030f565b6000600060006000600064ca1100ca11611000f15b50602060405114610321576000610335565b6000600060006000600063ca110100611000f25b50602160405114610347576000610359565b600060006000600063ca110100611000f45b505a60205261022a60205160005103036001556044356040525a60005260016040511461038757600061038c565b610100545b5060026040511461039f576000506103a6565b6005610100555b600b604051146103b75760006103bc565b61ca11315b50600c604051146103ce5760006103d3565b61ca113b5b50600d604051146103e6576000506103f1565b60006000600061ca113c5b600e60405114610402576000610407565b61ca113f5b5060156040511461041957600061042b565b6000600060006000600061ca11611000f15b5060166040511461043d57600061044f565b6000600060006000600061ca11611000f25b50601760405114610461576000610471565b600060006000600061ca11611000f45b50601860405114610483576000610493565b600060006000600061ca11611000fa5b50601f604051146104a55760006104ba565b6000600060006000600064ca1100ca11611000f15b506020604051146104cc5760006104e0565b6000600060006000600063ca110100611000f25b506021604051146104f2576000610504565b600060006000600063ca110100611000f45b505a60205261022a602051600051030360025560006101005500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 31, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("00")),
                callee_1: Account(code=bytes.fromhex("6101005400")),
                callee_2: Account(code=bytes.fromhex("61ca113100")),
                contract: Account(
                    storage={0: 2590, 1: 108, 2: 108},
                    code=bytes.fromhex(
                        "5a6000525a60205264ca1100ca11315063ca11010031506004356040525a600052600160405114610031576000610036565b610100545b5060026040511461004957600050610050565b6005610100555b600b60405114610061576000610066565b61ca11315b50600c6040511461007857600061007d565b61ca113b5b50600d604051146100905760005061009b565b60006000600061ca113c5b600e604051146100ac5760006100b1565b61ca113f5b506015604051146100c35760006100d5565b6000600060006000600061ca11611000f15b506016604051146100e75760006100f9565b6000600060006000600061ca11611000f25b5060176040511461010b57600061011b565b600060006000600061ca11611000f45b5060186040511461012d57600061013d565b600060006000600061ca11611000fa5b50601f6040511461014f576000610164565b6000600060006000600064ca1100ca11611000f15b5060206040511461017657600061018a565b6000600060006000600063ca110100611000f25b5060216040511461019c5760006101ae565b600060006000600063ca110100611000f45b505a60205261022a60205160005103036000556024356040525a6000526001604051146101dc5760006101e1565b610100545b506002604051146101f4576000506101fb565b6005610100555b600b6040511461020c576000610211565b61ca11315b50600c60405114610223576000610228565b61ca113b5b50600d6040511461023b57600050610246565b60006000600061ca113c5b600e6040511461025757600061025c565b61ca113f5b5060156040511461026e576000610280565b6000600060006000600061ca11611000f15b506016604051146102925760006102a4565b6000600060006000600061ca11611000f25b506017604051146102b65760006102c6565b600060006000600061ca11611000f45b506018604051146102d85760006102e8565b600060006000600061ca11611000fa5b50601f604051146102fa57600061030f565b6000600060006000600064ca1100ca11611000f15b50602060405114610321576000610335565b6000600060006000600063ca110100611000f25b50602160405114610347576000610359565b600060006000600063ca110100611000f45b505a60205261022a60205160005103036001556044356040525a60005260016040511461038757600061038c565b610100545b5060026040511461039f576000506103a6565b6005610100555b600b604051146103b75760006103bc565b61ca11315b50600c604051146103ce5760006103d3565b61ca113b5b50600d604051146103e6576000506103f1565b60006000600061ca113c5b600e60405114610402576000610407565b61ca113f5b5060156040511461041957600061042b565b6000600060006000600061ca11611000f15b5060166040511461043d57600061044f565b6000600060006000600061ca11611000f25b50601760405114610461576000610471565b600060006000600061ca11611000f45b50601860405114610483576000610493565b600060006000600061ca11611000fa5b50601f604051146104a55760006104ba565b6000600060006000600064ca1100ca11611000f15b506020604051146104cc5760006104e0565b6000600060006000600063ca110100611000f25b506021604051146104f2576000610504565b600060006000600063ca110100611000f45b505a60205261022a602051600051030360025560006101005500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 32, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("00")),
                callee_1: Account(code=bytes.fromhex("6101005400")),
                callee_2: Account(code=bytes.fromhex("61ca113100")),
                contract: Account(
                    storage={0: 2590, 1: 108, 2: 108},
                    code=bytes.fromhex(
                        "5a6000525a60205264ca1100ca11315063ca11010031506004356040525a600052600160405114610031576000610036565b610100545b5060026040511461004957600050610050565b6005610100555b600b60405114610061576000610066565b61ca11315b50600c6040511461007857600061007d565b61ca113b5b50600d604051146100905760005061009b565b60006000600061ca113c5b600e604051146100ac5760006100b1565b61ca113f5b506015604051146100c35760006100d5565b6000600060006000600061ca11611000f15b506016604051146100e75760006100f9565b6000600060006000600061ca11611000f25b5060176040511461010b57600061011b565b600060006000600061ca11611000f45b5060186040511461012d57600061013d565b600060006000600061ca11611000fa5b50601f6040511461014f576000610164565b6000600060006000600064ca1100ca11611000f15b5060206040511461017657600061018a565b6000600060006000600063ca110100611000f25b5060216040511461019c5760006101ae565b600060006000600063ca110100611000f45b505a60205261022a60205160005103036000556024356040525a6000526001604051146101dc5760006101e1565b610100545b506002604051146101f4576000506101fb565b6005610100555b600b6040511461020c576000610211565b61ca11315b50600c60405114610223576000610228565b61ca113b5b50600d6040511461023b57600050610246565b60006000600061ca113c5b600e6040511461025757600061025c565b61ca113f5b5060156040511461026e576000610280565b6000600060006000600061ca11611000f15b506016604051146102925760006102a4565b6000600060006000600061ca11611000f25b506017604051146102b65760006102c6565b600060006000600061ca11611000f45b506018604051146102d85760006102e8565b600060006000600061ca11611000fa5b50601f604051146102fa57600061030f565b6000600060006000600064ca1100ca11611000f15b50602060405114610321576000610335565b6000600060006000600063ca110100611000f25b50602160405114610347576000610359565b600060006000600063ca110100611000f45b505a60205261022a60205160005103036001556044356040525a60005260016040511461038757600061038c565b610100545b5060026040511461039f576000506103a6565b6005610100555b600b604051146103b75760006103bc565b61ca11315b50600c604051146103ce5760006103d3565b61ca113b5b50600d604051146103e6576000506103f1565b60006000600061ca113c5b600e60405114610402576000610407565b61ca113f5b5060156040511461041957600061042b565b6000600060006000600061ca11611000f15b5060166040511461043d57600061044f565b6000600060006000600061ca11611000f25b50601760405114610461576000610471565b600060006000600061ca11611000f45b50601860405114610483576000610493565b600060006000600061ca11611000fa5b50601f604051146104a55760006104ba565b6000600060006000600064ca1100ca11611000f15b506020604051146104cc5760006104e0565b6000600060006000600063ca110100611000f25b506021604051146104f2576000610504565b600060006000600063ca110100611000f45b505a60205261022a602051600051030360025560006101005500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 33, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("00")),
                callee_1: Account(code=bytes.fromhex("6101005400")),
                callee_2: Account(code=bytes.fromhex("61ca113100")),
                contract: Account(
                    storage={0: 2590, 1: 108, 2: 108},
                    code=bytes.fromhex(
                        "5a6000525a60205264ca1100ca11315063ca11010031506004356040525a600052600160405114610031576000610036565b610100545b5060026040511461004957600050610050565b6005610100555b600b60405114610061576000610066565b61ca11315b50600c6040511461007857600061007d565b61ca113b5b50600d604051146100905760005061009b565b60006000600061ca113c5b600e604051146100ac5760006100b1565b61ca113f5b506015604051146100c35760006100d5565b6000600060006000600061ca11611000f15b506016604051146100e75760006100f9565b6000600060006000600061ca11611000f25b5060176040511461010b57600061011b565b600060006000600061ca11611000f45b5060186040511461012d57600061013d565b600060006000600061ca11611000fa5b50601f6040511461014f576000610164565b6000600060006000600064ca1100ca11611000f15b5060206040511461017657600061018a565b6000600060006000600063ca110100611000f25b5060216040511461019c5760006101ae565b600060006000600063ca110100611000f45b505a60205261022a60205160005103036000556024356040525a6000526001604051146101dc5760006101e1565b610100545b506002604051146101f4576000506101fb565b6005610100555b600b6040511461020c576000610211565b61ca11315b50600c60405114610223576000610228565b61ca113b5b50600d6040511461023b57600050610246565b60006000600061ca113c5b600e6040511461025757600061025c565b61ca113f5b5060156040511461026e576000610280565b6000600060006000600061ca11611000f15b506016604051146102925760006102a4565b6000600060006000600061ca11611000f25b506017604051146102b65760006102c6565b600060006000600061ca11611000f45b506018604051146102d85760006102e8565b600060006000600061ca11611000fa5b50601f604051146102fa57600061030f565b6000600060006000600064ca1100ca11611000f15b50602060405114610321576000610335565b6000600060006000600063ca110100611000f25b50602160405114610347576000610359565b600060006000600063ca110100611000f45b505a60205261022a60205160005103036001556044356040525a60005260016040511461038757600061038c565b610100545b5060026040511461039f576000506103a6565b6005610100555b600b604051146103b75760006103bc565b61ca11315b50600c604051146103ce5760006103d3565b61ca113b5b50600d604051146103e6576000506103f1565b60006000600061ca113c5b600e60405114610402576000610407565b61ca113f5b5060156040511461041957600061042b565b6000600060006000600061ca11611000f15b5060166040511461043d57600061044f565b6000600060006000600061ca11611000f25b50601760405114610461576000610471565b600060006000600061ca11611000f45b50601860405114610483576000610493565b600060006000600061ca11611000fa5b50601f604051146104a55760006104ba565b6000600060006000600064ca1100ca11611000f15b506020604051146104cc5760006104e0565b6000600060006000600063ca110100611000f25b506021604051146104f2576000610504565b600060006000600063ca110100611000f45b505a60205261022a602051600051030360025560006101005500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 34, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("00")),
                callee_1: Account(code=bytes.fromhex("6101005400")),
                callee_2: Account(code=bytes.fromhex("61ca113100")),
                contract: Account(
                    storage={0: 2590, 1: 108, 2: 108},
                    code=bytes.fromhex(
                        "5a6000525a60205264ca1100ca11315063ca11010031506004356040525a600052600160405114610031576000610036565b610100545b5060026040511461004957600050610050565b6005610100555b600b60405114610061576000610066565b61ca11315b50600c6040511461007857600061007d565b61ca113b5b50600d604051146100905760005061009b565b60006000600061ca113c5b600e604051146100ac5760006100b1565b61ca113f5b506015604051146100c35760006100d5565b6000600060006000600061ca11611000f15b506016604051146100e75760006100f9565b6000600060006000600061ca11611000f25b5060176040511461010b57600061011b565b600060006000600061ca11611000f45b5060186040511461012d57600061013d565b600060006000600061ca11611000fa5b50601f6040511461014f576000610164565b6000600060006000600064ca1100ca11611000f15b5060206040511461017657600061018a565b6000600060006000600063ca110100611000f25b5060216040511461019c5760006101ae565b600060006000600063ca110100611000f45b505a60205261022a60205160005103036000556024356040525a6000526001604051146101dc5760006101e1565b610100545b506002604051146101f4576000506101fb565b6005610100555b600b6040511461020c576000610211565b61ca11315b50600c60405114610223576000610228565b61ca113b5b50600d6040511461023b57600050610246565b60006000600061ca113c5b600e6040511461025757600061025c565b61ca113f5b5060156040511461026e576000610280565b6000600060006000600061ca11611000f15b506016604051146102925760006102a4565b6000600060006000600061ca11611000f25b506017604051146102b65760006102c6565b600060006000600061ca11611000f45b506018604051146102d85760006102e8565b600060006000600061ca11611000fa5b50601f604051146102fa57600061030f565b6000600060006000600064ca1100ca11611000f15b50602060405114610321576000610335565b6000600060006000600063ca110100611000f25b50602160405114610347576000610359565b600060006000600063ca110100611000f45b505a60205261022a60205160005103036001556044356040525a60005260016040511461038757600061038c565b610100545b5060026040511461039f576000506103a6565b6005610100555b600b604051146103b75760006103bc565b61ca11315b50600c604051146103ce5760006103d3565b61ca113b5b50600d604051146103e6576000506103f1565b60006000600061ca113c5b600e60405114610402576000610407565b61ca113f5b5060156040511461041957600061042b565b6000600060006000600061ca11611000f15b5060166040511461043d57600061044f565b6000600060006000600061ca11611000f25b50601760405114610461576000610471565b600060006000600061ca11611000f45b50601860405114610483576000610493565b600060006000600061ca11611000fa5b50601f604051146104a55760006104ba565b6000600060006000600064ca1100ca11611000f15b506020604051146104cc5760006104e0565b6000600060006000600063ca110100611000f25b506021604051146104f2576000610504565b600060006000600063ca110100611000f45b505a60205261022a602051600051030360025560006101005500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 29, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("00")),
                callee_1: Account(code=bytes.fromhex("6101005400")),
                callee_2: Account(code=bytes.fromhex("61ca113100")),
                contract: Account(
                    storage={0: 2590, 1: 108, 2: 108},
                    code=bytes.fromhex(
                        "5a6000525a60205264ca1100ca11315063ca11010031506004356040525a600052600160405114610031576000610036565b610100545b5060026040511461004957600050610050565b6005610100555b600b60405114610061576000610066565b61ca11315b50600c6040511461007857600061007d565b61ca113b5b50600d604051146100905760005061009b565b60006000600061ca113c5b600e604051146100ac5760006100b1565b61ca113f5b506015604051146100c35760006100d5565b6000600060006000600061ca11611000f15b506016604051146100e75760006100f9565b6000600060006000600061ca11611000f25b5060176040511461010b57600061011b565b600060006000600061ca11611000f45b5060186040511461012d57600061013d565b600060006000600061ca11611000fa5b50601f6040511461014f576000610164565b6000600060006000600064ca1100ca11611000f15b5060206040511461017657600061018a565b6000600060006000600063ca110100611000f25b5060216040511461019c5760006101ae565b600060006000600063ca110100611000f45b505a60205261022a60205160005103036000556024356040525a6000526001604051146101dc5760006101e1565b610100545b506002604051146101f4576000506101fb565b6005610100555b600b6040511461020c576000610211565b61ca11315b50600c60405114610223576000610228565b61ca113b5b50600d6040511461023b57600050610246565b60006000600061ca113c5b600e6040511461025757600061025c565b61ca113f5b5060156040511461026e576000610280565b6000600060006000600061ca11611000f15b506016604051146102925760006102a4565b6000600060006000600061ca11611000f25b506017604051146102b65760006102c6565b600060006000600061ca11611000f45b506018604051146102d85760006102e8565b600060006000600061ca11611000fa5b50601f604051146102fa57600061030f565b6000600060006000600064ca1100ca11611000f15b50602060405114610321576000610335565b6000600060006000600063ca110100611000f25b50602160405114610347576000610359565b600060006000600063ca110100611000f45b505a60205261022a60205160005103036001556044356040525a60005260016040511461038757600061038c565b610100545b5060026040511461039f576000506103a6565b6005610100555b600b604051146103b75760006103bc565b61ca11315b50600c604051146103ce5760006103d3565b61ca113b5b50600d604051146103e6576000506103f1565b60006000600061ca113c5b600e60405114610402576000610407565b61ca113f5b5060156040511461041957600061042b565b6000600060006000600061ca11611000f15b5060166040511461043d57600061044f565b6000600060006000600061ca11611000f25b50601760405114610461576000610471565b600060006000600061ca11611000f45b50601860405114610483576000610493565b600060006000600061ca11611000fa5b50601f604051146104a55760006104ba565b6000600060006000600064ca1100ca11611000f15b506020604051146104cc5760006104e0565b6000600060006000600063ca110100611000f25b506021604051146104f2576000610504565b600060006000600063ca110100611000f45b505a60205261022a602051600051030360025560006101005500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 36, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("00")),
                callee_1: Account(code=bytes.fromhex("6101005400")),
                callee_2: Account(code=bytes.fromhex("61ca113100")),
                contract: Account(
                    storage={0: 2590, 1: 211, 2: 90},
                    code=bytes.fromhex(
                        "5a6000525a60205264ca1100ca11315063ca11010031506004356040525a600052600160405114610031576000610036565b610100545b5060026040511461004957600050610050565b6005610100555b600b60405114610061576000610066565b61ca11315b50600c6040511461007857600061007d565b61ca113b5b50600d604051146100905760005061009b565b60006000600061ca113c5b600e604051146100ac5760006100b1565b61ca113f5b506015604051146100c35760006100d5565b6000600060006000600061ca11611000f15b506016604051146100e75760006100f9565b6000600060006000600061ca11611000f25b5060176040511461010b57600061011b565b600060006000600061ca11611000f45b5060186040511461012d57600061013d565b600060006000600061ca11611000fa5b50601f6040511461014f576000610164565b6000600060006000600064ca1100ca11611000f15b5060206040511461017657600061018a565b6000600060006000600063ca110100611000f25b5060216040511461019c5760006101ae565b600060006000600063ca110100611000f45b505a60205261022a60205160005103036000556024356040525a6000526001604051146101dc5760006101e1565b610100545b506002604051146101f4576000506101fb565b6005610100555b600b6040511461020c576000610211565b61ca11315b50600c60405114610223576000610228565b61ca113b5b50600d6040511461023b57600050610246565b60006000600061ca113c5b600e6040511461025757600061025c565b61ca113f5b5060156040511461026e576000610280565b6000600060006000600061ca11611000f15b506016604051146102925760006102a4565b6000600060006000600061ca11611000f25b506017604051146102b65760006102c6565b600060006000600061ca11611000f45b506018604051146102d85760006102e8565b600060006000600061ca11611000fa5b50601f604051146102fa57600061030f565b6000600060006000600064ca1100ca11611000f15b50602060405114610321576000610335565b6000600060006000600063ca110100611000f25b50602160405114610347576000610359565b600060006000600063ca110100611000f45b505a60205261022a60205160005103036001556044356040525a60005260016040511461038757600061038c565b610100545b5060026040511461039f576000506103a6565b6005610100555b600b604051146103b75760006103bc565b61ca11315b50600c604051146103ce5760006103d3565b61ca113b5b50600d604051146103e6576000506103f1565b60006000600061ca113c5b600e60405114610402576000610407565b61ca113f5b5060156040511461041957600061042b565b6000600060006000600061ca11611000f15b5060166040511461043d57600061044f565b6000600060006000600061ca11611000f25b50601760405114610461576000610471565b600060006000600061ca11611000f45b50601860405114610483576000610493565b600060006000600061ca11611000fa5b50601f604051146104a55760006104ba565b6000600060006000600064ca1100ca11611000f15b506020604051146104cc5760006104e0565b6000600060006000600063ca110100611000f25b506021604051146104f2576000610504565b600060006000600063ca110100611000f45b505a60205261022a602051600051030360025560006101005500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 10, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("00")),
                callee_1: Account(code=bytes.fromhex("6101005400")),
                callee_2: Account(code=bytes.fromhex("61ca113100")),
                contract: Account(
                    storage={0: 2605, 1: 105, 2: 105},
                    code=bytes.fromhex(
                        "5a6000525a60205264ca1100ca11315063ca11010031506004356040525a600052600160405114610031576000610036565b610100545b5060026040511461004957600050610050565b6005610100555b600b60405114610061576000610066565b61ca11315b50600c6040511461007857600061007d565b61ca113b5b50600d604051146100905760005061009b565b60006000600061ca113c5b600e604051146100ac5760006100b1565b61ca113f5b506015604051146100c35760006100d5565b6000600060006000600061ca11611000f15b506016604051146100e75760006100f9565b6000600060006000600061ca11611000f25b5060176040511461010b57600061011b565b600060006000600061ca11611000f45b5060186040511461012d57600061013d565b600060006000600061ca11611000fa5b50601f6040511461014f576000610164565b6000600060006000600064ca1100ca11611000f15b5060206040511461017657600061018a565b6000600060006000600063ca110100611000f25b5060216040511461019c5760006101ae565b600060006000600063ca110100611000f45b505a60205261022a60205160005103036000556024356040525a6000526001604051146101dc5760006101e1565b610100545b506002604051146101f4576000506101fb565b6005610100555b600b6040511461020c576000610211565b61ca11315b50600c60405114610223576000610228565b61ca113b5b50600d6040511461023b57600050610246565b60006000600061ca113c5b600e6040511461025757600061025c565b61ca113f5b5060156040511461026e576000610280565b6000600060006000600061ca11611000f15b506016604051146102925760006102a4565b6000600060006000600061ca11611000f25b506017604051146102b65760006102c6565b600060006000600061ca11611000f45b506018604051146102d85760006102e8565b600060006000600061ca11611000fa5b50601f604051146102fa57600061030f565b6000600060006000600064ca1100ca11611000f15b50602060405114610321576000610335565b6000600060006000600063ca110100611000f25b50602160405114610347576000610359565b600060006000600063ca110100611000f45b505a60205261022a60205160005103036001556044356040525a60005260016040511461038757600061038c565b610100545b5060026040511461039f576000506103a6565b6005610100555b600b604051146103b75760006103bc565b61ca11315b50600c604051146103ce5760006103d3565b61ca113b5b50600d604051146103e6576000506103f1565b60006000600061ca113c5b600e60405114610402576000610407565b61ca113f5b5060156040511461041957600061042b565b6000600060006000600061ca11611000f15b5060166040511461043d57600061044f565b6000600060006000600061ca11611000f25b50601760405114610461576000610471565b600060006000600061ca11611000f45b50601860405114610483576000610493565b600060006000600061ca11611000fa5b50601f604051146104a55760006104ba565b6000600060006000600064ca1100ca11611000f15b506020604051146104cc5760006104e0565b6000600060006000600063ca110100611000f25b506021604051146104f2576000610504565b600060006000600063ca110100611000f45b505a60205261022a602051600051030360025560006101005500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 27, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("00")),
                callee_1: Account(code=bytes.fromhex("6101005400")),
                callee_2: Account(code=bytes.fromhex("61ca113100")),
                contract: Account(
                    storage={0: 2605, 1: 105, 2: 105},
                    code=bytes.fromhex(
                        "5a6000525a60205264ca1100ca11315063ca11010031506004356040525a600052600160405114610031576000610036565b610100545b5060026040511461004957600050610050565b6005610100555b600b60405114610061576000610066565b61ca11315b50600c6040511461007857600061007d565b61ca113b5b50600d604051146100905760005061009b565b60006000600061ca113c5b600e604051146100ac5760006100b1565b61ca113f5b506015604051146100c35760006100d5565b6000600060006000600061ca11611000f15b506016604051146100e75760006100f9565b6000600060006000600061ca11611000f25b5060176040511461010b57600061011b565b600060006000600061ca11611000f45b5060186040511461012d57600061013d565b600060006000600061ca11611000fa5b50601f6040511461014f576000610164565b6000600060006000600064ca1100ca11611000f15b5060206040511461017657600061018a565b6000600060006000600063ca110100611000f25b5060216040511461019c5760006101ae565b600060006000600063ca110100611000f45b505a60205261022a60205160005103036000556024356040525a6000526001604051146101dc5760006101e1565b610100545b506002604051146101f4576000506101fb565b6005610100555b600b6040511461020c576000610211565b61ca11315b50600c60405114610223576000610228565b61ca113b5b50600d6040511461023b57600050610246565b60006000600061ca113c5b600e6040511461025757600061025c565b61ca113f5b5060156040511461026e576000610280565b6000600060006000600061ca11611000f15b506016604051146102925760006102a4565b6000600060006000600061ca11611000f25b506017604051146102b65760006102c6565b600060006000600061ca11611000f45b506018604051146102d85760006102e8565b600060006000600061ca11611000fa5b50601f604051146102fa57600061030f565b6000600060006000600064ca1100ca11611000f15b50602060405114610321576000610335565b6000600060006000600063ca110100611000f25b50602160405114610347576000610359565b600060006000600063ca110100611000f45b505a60205261022a60205160005103036001556044356040525a60005260016040511461038757600061038c565b610100545b5060026040511461039f576000506103a6565b6005610100555b600b604051146103b75760006103bc565b61ca11315b50600c604051146103ce5760006103d3565b61ca113b5b50600d604051146103e6576000506103f1565b60006000600061ca113c5b600e60405114610402576000610407565b61ca113f5b5060156040511461041957600061042b565b6000600060006000600061ca11611000f15b5060166040511461043d57600061044f565b6000600060006000600061ca11611000f25b50601760405114610461576000610471565b600060006000600061ca11611000f45b50601860405114610483576000610493565b600060006000600061ca11611000fa5b50601f604051146104a55760006104ba565b6000600060006000600064ca1100ca11611000f15b506020604051146104cc5760006104e0565b6000600060006000600063ca110100611000f25b506021604051146104f2576000610504565b600060006000600063ca110100611000f45b505a60205261022a602051600051030360025560006101005500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 28, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("00")),
                callee_1: Account(code=bytes.fromhex("6101005400")),
                callee_2: Account(code=bytes.fromhex("61ca113100")),
                contract: Account(
                    storage={0: 2605, 1: 105, 2: 105},
                    code=bytes.fromhex(
                        "5a6000525a60205264ca1100ca11315063ca11010031506004356040525a600052600160405114610031576000610036565b610100545b5060026040511461004957600050610050565b6005610100555b600b60405114610061576000610066565b61ca11315b50600c6040511461007857600061007d565b61ca113b5b50600d604051146100905760005061009b565b60006000600061ca113c5b600e604051146100ac5760006100b1565b61ca113f5b506015604051146100c35760006100d5565b6000600060006000600061ca11611000f15b506016604051146100e75760006100f9565b6000600060006000600061ca11611000f25b5060176040511461010b57600061011b565b600060006000600061ca11611000f45b5060186040511461012d57600061013d565b600060006000600061ca11611000fa5b50601f6040511461014f576000610164565b6000600060006000600064ca1100ca11611000f15b5060206040511461017657600061018a565b6000600060006000600063ca110100611000f25b5060216040511461019c5760006101ae565b600060006000600063ca110100611000f45b505a60205261022a60205160005103036000556024356040525a6000526001604051146101dc5760006101e1565b610100545b506002604051146101f4576000506101fb565b6005610100555b600b6040511461020c576000610211565b61ca11315b50600c60405114610223576000610228565b61ca113b5b50600d6040511461023b57600050610246565b60006000600061ca113c5b600e6040511461025757600061025c565b61ca113f5b5060156040511461026e576000610280565b6000600060006000600061ca11611000f15b506016604051146102925760006102a4565b6000600060006000600061ca11611000f25b506017604051146102b65760006102c6565b600060006000600061ca11611000f45b506018604051146102d85760006102e8565b600060006000600061ca11611000fa5b50601f604051146102fa57600061030f565b6000600060006000600064ca1100ca11611000f15b50602060405114610321576000610335565b6000600060006000600063ca110100611000f25b50602160405114610347576000610359565b600060006000600063ca110100611000f45b505a60205261022a60205160005103036001556044356040525a60005260016040511461038757600061038c565b610100545b5060026040511461039f576000506103a6565b6005610100555b600b604051146103b75760006103bc565b61ca11315b50600c604051146103ce5760006103d3565b61ca113b5b50600d604051146103e6576000506103f1565b60006000600061ca113c5b600e60405114610402576000610407565b61ca113f5b5060156040511461041957600061042b565b6000600060006000600061ca11611000f15b5060166040511461043d57600061044f565b6000600060006000600061ca11611000f25b50601760405114610461576000610471565b600060006000600061ca11611000f45b50601860405114610483576000610493565b600060006000600061ca11611000fa5b50601f604051146104a55760006104ba565b6000600060006000600064ca1100ca11611000f15b506020604051146104cc5760006104e0565b6000600060006000600063ca110100611000f25b506021604051146104f2576000610504565b600060006000600063ca110100611000f45b505a60205261022a602051600051030360025560006101005500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 9, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("00")),
                callee_1: Account(code=bytes.fromhex("6101005400")),
                callee_2: Account(code=bytes.fromhex("61ca113100")),
                contract: Account(
                    storage={0: 2605, 1: 105, 2: 105},
                    code=bytes.fromhex(
                        "5a6000525a60205264ca1100ca11315063ca11010031506004356040525a600052600160405114610031576000610036565b610100545b5060026040511461004957600050610050565b6005610100555b600b60405114610061576000610066565b61ca11315b50600c6040511461007857600061007d565b61ca113b5b50600d604051146100905760005061009b565b60006000600061ca113c5b600e604051146100ac5760006100b1565b61ca113f5b506015604051146100c35760006100d5565b6000600060006000600061ca11611000f15b506016604051146100e75760006100f9565b6000600060006000600061ca11611000f25b5060176040511461010b57600061011b565b600060006000600061ca11611000f45b5060186040511461012d57600061013d565b600060006000600061ca11611000fa5b50601f6040511461014f576000610164565b6000600060006000600064ca1100ca11611000f15b5060206040511461017657600061018a565b6000600060006000600063ca110100611000f25b5060216040511461019c5760006101ae565b600060006000600063ca110100611000f45b505a60205261022a60205160005103036000556024356040525a6000526001604051146101dc5760006101e1565b610100545b506002604051146101f4576000506101fb565b6005610100555b600b6040511461020c576000610211565b61ca11315b50600c60405114610223576000610228565b61ca113b5b50600d6040511461023b57600050610246565b60006000600061ca113c5b600e6040511461025757600061025c565b61ca113f5b5060156040511461026e576000610280565b6000600060006000600061ca11611000f15b506016604051146102925760006102a4565b6000600060006000600061ca11611000f25b506017604051146102b65760006102c6565b600060006000600061ca11611000f45b506018604051146102d85760006102e8565b600060006000600061ca11611000fa5b50601f604051146102fa57600061030f565b6000600060006000600064ca1100ca11611000f15b50602060405114610321576000610335565b6000600060006000600063ca110100611000f25b50602160405114610347576000610359565b600060006000600063ca110100611000f45b505a60205261022a60205160005103036001556044356040525a60005260016040511461038757600061038c565b610100545b5060026040511461039f576000506103a6565b6005610100555b600b604051146103b75760006103bc565b61ca11315b50600c604051146103ce5760006103d3565b61ca113b5b50600d604051146103e6576000506103f1565b60006000600061ca113c5b600e60405114610402576000610407565b61ca113f5b5060156040511461041957600061042b565b6000600060006000600061ca11611000f15b5060166040511461043d57600061044f565b6000600060006000600061ca11611000f25b50601760405114610461576000610471565b600060006000600061ca11611000f45b50601860405114610483576000610493565b600060006000600061ca11611000fa5b50601f604051146104a55760006104ba565b6000600060006000600064ca1100ca11611000f15b506020604051146104cc5760006104e0565b6000600060006000600063ca110100611000f25b506021604051146104f2576000610504565b600060006000600063ca110100611000f45b505a60205261022a602051600051030360025560006101005500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 8, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("00")),
                callee_1: Account(code=bytes.fromhex("6101005400")),
                callee_2: Account(code=bytes.fromhex("61ca113100")),
                contract: Account(
                    storage={0: 2608, 1: 108, 2: 108},
                    code=bytes.fromhex(
                        "5a6000525a60205264ca1100ca11315063ca11010031506004356040525a600052600160405114610031576000610036565b610100545b5060026040511461004957600050610050565b6005610100555b600b60405114610061576000610066565b61ca11315b50600c6040511461007857600061007d565b61ca113b5b50600d604051146100905760005061009b565b60006000600061ca113c5b600e604051146100ac5760006100b1565b61ca113f5b506015604051146100c35760006100d5565b6000600060006000600061ca11611000f15b506016604051146100e75760006100f9565b6000600060006000600061ca11611000f25b5060176040511461010b57600061011b565b600060006000600061ca11611000f45b5060186040511461012d57600061013d565b600060006000600061ca11611000fa5b50601f6040511461014f576000610164565b6000600060006000600064ca1100ca11611000f15b5060206040511461017657600061018a565b6000600060006000600063ca110100611000f25b5060216040511461019c5760006101ae565b600060006000600063ca110100611000f45b505a60205261022a60205160005103036000556024356040525a6000526001604051146101dc5760006101e1565b610100545b506002604051146101f4576000506101fb565b6005610100555b600b6040511461020c576000610211565b61ca11315b50600c60405114610223576000610228565b61ca113b5b50600d6040511461023b57600050610246565b60006000600061ca113c5b600e6040511461025757600061025c565b61ca113f5b5060156040511461026e576000610280565b6000600060006000600061ca11611000f15b506016604051146102925760006102a4565b6000600060006000600061ca11611000f25b506017604051146102b65760006102c6565b600060006000600061ca11611000f45b506018604051146102d85760006102e8565b600060006000600061ca11611000fa5b50601f604051146102fa57600061030f565b6000600060006000600064ca1100ca11611000f15b50602060405114610321576000610335565b6000600060006000600063ca110100611000f25b50602160405114610347576000610359565b600060006000600063ca110100611000f45b505a60205261022a60205160005103036001556044356040525a60005260016040511461038757600061038c565b610100545b5060026040511461039f576000506103a6565b6005610100555b600b604051146103b75760006103bc565b61ca11315b50600c604051146103ce5760006103d3565b61ca113b5b50600d604051146103e6576000506103f1565b60006000600061ca113c5b600e60405114610402576000610407565b61ca113f5b5060156040511461041957600061042b565b6000600060006000600061ca11611000f15b5060166040511461043d57600061044f565b6000600060006000600061ca11611000f25b50601760405114610461576000610471565b600060006000600061ca11611000f45b50601860405114610483576000610493565b600060006000600061ca11611000fa5b50601f604051146104a55760006104ba565b6000600060006000600064ca1100ca11611000f15b506020604051146104cc5760006104e0565b6000600060006000600063ca110100611000f25b506021604051146104f2576000610504565b600060006000600063ca110100611000f45b505a60205261022a602051600051030360025560006101005500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 25, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("00")),
                callee_1: Account(code=bytes.fromhex("6101005400")),
                callee_2: Account(code=bytes.fromhex("61ca113100")),
                contract: Account(
                    storage={0: 2608, 1: 108, 2: 108},
                    code=bytes.fromhex(
                        "5a6000525a60205264ca1100ca11315063ca11010031506004356040525a600052600160405114610031576000610036565b610100545b5060026040511461004957600050610050565b6005610100555b600b60405114610061576000610066565b61ca11315b50600c6040511461007857600061007d565b61ca113b5b50600d604051146100905760005061009b565b60006000600061ca113c5b600e604051146100ac5760006100b1565b61ca113f5b506015604051146100c35760006100d5565b6000600060006000600061ca11611000f15b506016604051146100e75760006100f9565b6000600060006000600061ca11611000f25b5060176040511461010b57600061011b565b600060006000600061ca11611000f45b5060186040511461012d57600061013d565b600060006000600061ca11611000fa5b50601f6040511461014f576000610164565b6000600060006000600064ca1100ca11611000f15b5060206040511461017657600061018a565b6000600060006000600063ca110100611000f25b5060216040511461019c5760006101ae565b600060006000600063ca110100611000f45b505a60205261022a60205160005103036000556024356040525a6000526001604051146101dc5760006101e1565b610100545b506002604051146101f4576000506101fb565b6005610100555b600b6040511461020c576000610211565b61ca11315b50600c60405114610223576000610228565b61ca113b5b50600d6040511461023b57600050610246565b60006000600061ca113c5b600e6040511461025757600061025c565b61ca113f5b5060156040511461026e576000610280565b6000600060006000600061ca11611000f15b506016604051146102925760006102a4565b6000600060006000600061ca11611000f25b506017604051146102b65760006102c6565b600060006000600061ca11611000f45b506018604051146102d85760006102e8565b600060006000600061ca11611000fa5b50601f604051146102fa57600061030f565b6000600060006000600064ca1100ca11611000f15b50602060405114610321576000610335565b6000600060006000600063ca110100611000f25b50602160405114610347576000610359565b600060006000600063ca110100611000f45b505a60205261022a60205160005103036001556044356040525a60005260016040511461038757600061038c565b610100545b5060026040511461039f576000506103a6565b6005610100555b600b604051146103b75760006103bc565b61ca11315b50600c604051146103ce5760006103d3565b61ca113b5b50600d604051146103e6576000506103f1565b60006000600061ca113c5b600e60405114610402576000610407565b61ca113f5b5060156040511461041957600061042b565b6000600060006000600061ca11611000f15b5060166040511461043d57600061044f565b6000600060006000600061ca11611000f25b50601760405114610461576000610471565b600060006000600061ca11611000f45b50601860405114610483576000610493565b600060006000600061ca11611000fa5b50601f604051146104a55760006104ba565b6000600060006000600064ca1100ca11611000f15b506020604051146104cc5760006104e0565b6000600060006000600063ca110100611000f25b506021604051146104f2576000610504565b600060006000600063ca110100611000f45b505a60205261022a602051600051030360025560006101005500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 26, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("00")),
                callee_1: Account(code=bytes.fromhex("6101005400")),
                callee_2: Account(code=bytes.fromhex("61ca113100")),
                contract: Account(
                    storage={0: 2608, 1: 108, 2: 108},
                    code=bytes.fromhex(
                        "5a6000525a60205264ca1100ca11315063ca11010031506004356040525a600052600160405114610031576000610036565b610100545b5060026040511461004957600050610050565b6005610100555b600b60405114610061576000610066565b61ca11315b50600c6040511461007857600061007d565b61ca113b5b50600d604051146100905760005061009b565b60006000600061ca113c5b600e604051146100ac5760006100b1565b61ca113f5b506015604051146100c35760006100d5565b6000600060006000600061ca11611000f15b506016604051146100e75760006100f9565b6000600060006000600061ca11611000f25b5060176040511461010b57600061011b565b600060006000600061ca11611000f45b5060186040511461012d57600061013d565b600060006000600061ca11611000fa5b50601f6040511461014f576000610164565b6000600060006000600064ca1100ca11611000f15b5060206040511461017657600061018a565b6000600060006000600063ca110100611000f25b5060216040511461019c5760006101ae565b600060006000600063ca110100611000f45b505a60205261022a60205160005103036000556024356040525a6000526001604051146101dc5760006101e1565b610100545b506002604051146101f4576000506101fb565b6005610100555b600b6040511461020c576000610211565b61ca11315b50600c60405114610223576000610228565b61ca113b5b50600d6040511461023b57600050610246565b60006000600061ca113c5b600e6040511461025757600061025c565b61ca113f5b5060156040511461026e576000610280565b6000600060006000600061ca11611000f15b506016604051146102925760006102a4565b6000600060006000600061ca11611000f25b506017604051146102b65760006102c6565b600060006000600061ca11611000f45b506018604051146102d85760006102e8565b600060006000600061ca11611000fa5b50601f604051146102fa57600061030f565b6000600060006000600064ca1100ca11611000f15b50602060405114610321576000610335565b6000600060006000600063ca110100611000f25b50602160405114610347576000610359565b600060006000600063ca110100611000f45b505a60205261022a60205160005103036001556044356040525a60005260016040511461038757600061038c565b610100545b5060026040511461039f576000506103a6565b6005610100555b600b604051146103b75760006103bc565b61ca11315b50600c604051146103ce5760006103d3565b61ca113b5b50600d604051146103e6576000506103f1565b60006000600061ca113c5b600e60405114610402576000610407565b61ca113f5b5060156040511461041957600061042b565b6000600060006000600061ca11611000f15b5060166040511461043d57600061044f565b6000600060006000600061ca11611000f25b50601760405114610461576000610471565b600060006000600061ca11611000f45b50601860405114610483576000610493565b600060006000600061ca11611000fa5b50601f604051146104a55760006104ba565b6000600060006000600064ca1100ca11611000f15b506020604051146104cc5760006104e0565b6000600060006000600063ca110100611000f25b506021604051146104f2576000610504565b600060006000600063ca110100611000f45b505a60205261022a602051600051030360025560006101005500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 7, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("00")),
                callee_1: Account(code=bytes.fromhex("6101005400")),
                callee_2: Account(code=bytes.fromhex("61ca113100")),
                contract: Account(
                    storage={0: 2608, 1: 108, 2: 108},
                    code=bytes.fromhex(
                        "5a6000525a60205264ca1100ca11315063ca11010031506004356040525a600052600160405114610031576000610036565b610100545b5060026040511461004957600050610050565b6005610100555b600b60405114610061576000610066565b61ca11315b50600c6040511461007857600061007d565b61ca113b5b50600d604051146100905760005061009b565b60006000600061ca113c5b600e604051146100ac5760006100b1565b61ca113f5b506015604051146100c35760006100d5565b6000600060006000600061ca11611000f15b506016604051146100e75760006100f9565b6000600060006000600061ca11611000f25b5060176040511461010b57600061011b565b600060006000600061ca11611000f45b5060186040511461012d57600061013d565b600060006000600061ca11611000fa5b50601f6040511461014f576000610164565b6000600060006000600064ca1100ca11611000f15b5060206040511461017657600061018a565b6000600060006000600063ca110100611000f25b5060216040511461019c5760006101ae565b600060006000600063ca110100611000f45b505a60205261022a60205160005103036000556024356040525a6000526001604051146101dc5760006101e1565b610100545b506002604051146101f4576000506101fb565b6005610100555b600b6040511461020c576000610211565b61ca11315b50600c60405114610223576000610228565b61ca113b5b50600d6040511461023b57600050610246565b60006000600061ca113c5b600e6040511461025757600061025c565b61ca113f5b5060156040511461026e576000610280565b6000600060006000600061ca11611000f15b506016604051146102925760006102a4565b6000600060006000600061ca11611000f25b506017604051146102b65760006102c6565b600060006000600061ca11611000f45b506018604051146102d85760006102e8565b600060006000600061ca11611000fa5b50601f604051146102fa57600061030f565b6000600060006000600064ca1100ca11611000f15b50602060405114610321576000610335565b6000600060006000600063ca110100611000f25b50602160405114610347576000610359565b600060006000600063ca110100611000f45b505a60205261022a60205160005103036001556044356040525a60005260016040511461038757600061038c565b610100545b5060026040511461039f576000506103a6565b6005610100555b600b604051146103b75760006103bc565b61ca11315b50600c604051146103ce5760006103d3565b61ca113b5b50600d604051146103e6576000506103f1565b60006000600061ca113c5b600e60405114610402576000610407565b61ca113f5b5060156040511461041957600061042b565b6000600060006000600061ca11611000f15b5060166040511461043d57600061044f565b6000600060006000600061ca11611000f25b50601760405114610461576000610471565b600060006000600061ca11611000f45b50601860405114610483576000610493565b600060006000600061ca11611000fa5b50601f604051146104a55760006104ba565b6000600060006000600064ca1100ca11611000f15b506020604051146104cc5760006104e0565b6000600060006000600063ca110100611000f25b506021604051146104f2576000610504565b600060006000600063ca110100611000f45b505a60205261022a602051600051030360025560006101005500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 5, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("00")),
                callee_1: Account(code=bytes.fromhex("6101005400")),
                callee_2: Account(code=bytes.fromhex("61ca113100")),
                contract: Account(
                    storage={0: 2597, 1: 97, 2: 97},
                    code=bytes.fromhex(
                        "5a6000525a60205264ca1100ca11315063ca11010031506004356040525a600052600160405114610031576000610036565b610100545b5060026040511461004957600050610050565b6005610100555b600b60405114610061576000610066565b61ca11315b50600c6040511461007857600061007d565b61ca113b5b50600d604051146100905760005061009b565b60006000600061ca113c5b600e604051146100ac5760006100b1565b61ca113f5b506015604051146100c35760006100d5565b6000600060006000600061ca11611000f15b506016604051146100e75760006100f9565b6000600060006000600061ca11611000f25b5060176040511461010b57600061011b565b600060006000600061ca11611000f45b5060186040511461012d57600061013d565b600060006000600061ca11611000fa5b50601f6040511461014f576000610164565b6000600060006000600064ca1100ca11611000f15b5060206040511461017657600061018a565b6000600060006000600063ca110100611000f25b5060216040511461019c5760006101ae565b600060006000600063ca110100611000f45b505a60205261022a60205160005103036000556024356040525a6000526001604051146101dc5760006101e1565b610100545b506002604051146101f4576000506101fb565b6005610100555b600b6040511461020c576000610211565b61ca11315b50600c60405114610223576000610228565b61ca113b5b50600d6040511461023b57600050610246565b60006000600061ca113c5b600e6040511461025757600061025c565b61ca113f5b5060156040511461026e576000610280565b6000600060006000600061ca11611000f15b506016604051146102925760006102a4565b6000600060006000600061ca11611000f25b506017604051146102b65760006102c6565b600060006000600061ca11611000f45b506018604051146102d85760006102e8565b600060006000600061ca11611000fa5b50601f604051146102fa57600061030f565b6000600060006000600064ca1100ca11611000f15b50602060405114610321576000610335565b6000600060006000600063ca110100611000f25b50602160405114610347576000610359565b600060006000600063ca110100611000f45b505a60205261022a60205160005103036001556044356040525a60005260016040511461038757600061038c565b610100545b5060026040511461039f576000506103a6565b6005610100555b600b604051146103b75760006103bc565b61ca11315b50600c604051146103ce5760006103d3565b61ca113b5b50600d604051146103e6576000506103f1565b60006000600061ca113c5b600e60405114610402576000610407565b61ca113f5b5060156040511461041957600061042b565b6000600060006000600061ca11611000f15b5060166040511461043d57600061044f565b6000600060006000600061ca11611000f25b50601760405114610461576000610471565b600060006000600061ca11611000f45b50601860405114610483576000610493565b600060006000600061ca11611000fa5b50601f604051146104a55760006104ba565b6000600060006000600064ca1100ca11611000f15b506020604051146104cc5760006104e0565b6000600060006000600063ca110100611000f25b506021604051146104f2576000610504565b600060006000600063ca110100611000f45b505a60205261022a602051600051030360025560006101005500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 37, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("00")),
                callee_1: Account(code=bytes.fromhex("6101005400")),
                callee_2: Account(code=bytes.fromhex("61ca113100")),
                contract: Account(
                    storage={0: 2711, 1: 90, 2: 90},
                    code=bytes.fromhex(
                        "5a6000525a60205264ca1100ca11315063ca11010031506004356040525a600052600160405114610031576000610036565b610100545b5060026040511461004957600050610050565b6005610100555b600b60405114610061576000610066565b61ca11315b50600c6040511461007857600061007d565b61ca113b5b50600d604051146100905760005061009b565b60006000600061ca113c5b600e604051146100ac5760006100b1565b61ca113f5b506015604051146100c35760006100d5565b6000600060006000600061ca11611000f15b506016604051146100e75760006100f9565b6000600060006000600061ca11611000f25b5060176040511461010b57600061011b565b600060006000600061ca11611000f45b5060186040511461012d57600061013d565b600060006000600061ca11611000fa5b50601f6040511461014f576000610164565b6000600060006000600064ca1100ca11611000f15b5060206040511461017657600061018a565b6000600060006000600063ca110100611000f25b5060216040511461019c5760006101ae565b600060006000600063ca110100611000f45b505a60205261022a60205160005103036000556024356040525a6000526001604051146101dc5760006101e1565b610100545b506002604051146101f4576000506101fb565b6005610100555b600b6040511461020c576000610211565b61ca11315b50600c60405114610223576000610228565b61ca113b5b50600d6040511461023b57600050610246565b60006000600061ca113c5b600e6040511461025757600061025c565b61ca113f5b5060156040511461026e576000610280565b6000600060006000600061ca11611000f15b506016604051146102925760006102a4565b6000600060006000600061ca11611000f25b506017604051146102b65760006102c6565b600060006000600061ca11611000f45b506018604051146102d85760006102e8565b600060006000600061ca11611000fa5b50601f604051146102fa57600061030f565b6000600060006000600064ca1100ca11611000f15b50602060405114610321576000610335565b6000600060006000600063ca110100611000f25b50602160405114610347576000610359565b600060006000600063ca110100611000f45b505a60205261022a60205160005103036001556044356040525a60005260016040511461038757600061038c565b610100545b5060026040511461039f576000506103a6565b6005610100555b600b604051146103b75760006103bc565b61ca11315b50600c604051146103ce5760006103d3565b61ca113b5b50600d604051146103e6576000506103f1565b60006000600061ca113c5b600e60405114610402576000610407565b61ca113f5b5060156040511461041957600061042b565b6000600060006000600061ca11611000f15b5060166040511461043d57600061044f565b6000600060006000600061ca11611000f25b50601760405114610461576000610471565b600060006000600061ca11611000f45b50601860405114610483576000610493565b600060006000600061ca11611000fa5b50601f604051146104a55760006104ba565b6000600060006000600064ca1100ca11611000f15b506020604051146104cc5760006104e0565b6000600060006000600063ca110100611000f25b506021604051146104f2576000610504565b600060006000600063ca110100611000f45b505a60205261022a602051600051030360025560006101005500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 11, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("00")),
                callee_1: Account(code=bytes.fromhex("6101005400")),
                callee_2: Account(code=bytes.fromhex("61ca113100")),
                contract: Account(
                    storage={0: 2711, 1: 211, 2: 211},
                    code=bytes.fromhex(
                        "5a6000525a60205264ca1100ca11315063ca11010031506004356040525a600052600160405114610031576000610036565b610100545b5060026040511461004957600050610050565b6005610100555b600b60405114610061576000610066565b61ca11315b50600c6040511461007857600061007d565b61ca113b5b50600d604051146100905760005061009b565b60006000600061ca113c5b600e604051146100ac5760006100b1565b61ca113f5b506015604051146100c35760006100d5565b6000600060006000600061ca11611000f15b506016604051146100e75760006100f9565b6000600060006000600061ca11611000f25b5060176040511461010b57600061011b565b600060006000600061ca11611000f45b5060186040511461012d57600061013d565b600060006000600061ca11611000fa5b50601f6040511461014f576000610164565b6000600060006000600064ca1100ca11611000f15b5060206040511461017657600061018a565b6000600060006000600063ca110100611000f25b5060216040511461019c5760006101ae565b600060006000600063ca110100611000f45b505a60205261022a60205160005103036000556024356040525a6000526001604051146101dc5760006101e1565b610100545b506002604051146101f4576000506101fb565b6005610100555b600b6040511461020c576000610211565b61ca11315b50600c60405114610223576000610228565b61ca113b5b50600d6040511461023b57600050610246565b60006000600061ca113c5b600e6040511461025757600061025c565b61ca113f5b5060156040511461026e576000610280565b6000600060006000600061ca11611000f15b506016604051146102925760006102a4565b6000600060006000600061ca11611000f25b506017604051146102b65760006102c6565b600060006000600061ca11611000f45b506018604051146102d85760006102e8565b600060006000600061ca11611000fa5b50601f604051146102fa57600061030f565b6000600060006000600064ca1100ca11611000f15b50602060405114610321576000610335565b6000600060006000600063ca110100611000f25b50602160405114610347576000610359565b600060006000600063ca110100611000f45b505a60205261022a60205160005103036001556044356040525a60005260016040511461038757600061038c565b610100545b5060026040511461039f576000506103a6565b6005610100555b600b604051146103b75760006103bc565b61ca11315b50600c604051146103ce5760006103d3565b61ca113b5b50600d604051146103e6576000506103f1565b60006000600061ca113c5b600e60405114610402576000610407565b61ca113f5b5060156040511461041957600061042b565b6000600060006000600061ca11611000f15b5060166040511461043d57600061044f565b6000600060006000600061ca11611000f25b50601760405114610461576000610471565b600060006000600061ca11611000f45b50601860405114610483576000610493565b600060006000600061ca11611000fa5b50601f604051146104a55760006104ba565b6000600060006000600064ca1100ca11611000f15b506020604051146104cc5760006104e0565b6000600060006000600063ca110100611000f25b506021604051146104f2576000610504565b600060006000600063ca110100611000f45b505a60205261022a602051600051030360025560006101005500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 13, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("00")),
                callee_1: Account(code=bytes.fromhex("6101005400")),
                callee_2: Account(code=bytes.fromhex("61ca113100")),
                contract: Account(
                    storage={0: 2208, 1: 208, 2: 208},
                    code=bytes.fromhex(
                        "5a6000525a60205264ca1100ca11315063ca11010031506004356040525a600052600160405114610031576000610036565b610100545b5060026040511461004957600050610050565b6005610100555b600b60405114610061576000610066565b61ca11315b50600c6040511461007857600061007d565b61ca113b5b50600d604051146100905760005061009b565b60006000600061ca113c5b600e604051146100ac5760006100b1565b61ca113f5b506015604051146100c35760006100d5565b6000600060006000600061ca11611000f15b506016604051146100e75760006100f9565b6000600060006000600061ca11611000f25b5060176040511461010b57600061011b565b600060006000600061ca11611000f45b5060186040511461012d57600061013d565b600060006000600061ca11611000fa5b50601f6040511461014f576000610164565b6000600060006000600064ca1100ca11611000f15b5060206040511461017657600061018a565b6000600060006000600063ca110100611000f25b5060216040511461019c5760006101ae565b600060006000600063ca110100611000f45b505a60205261022a60205160005103036000556024356040525a6000526001604051146101dc5760006101e1565b610100545b506002604051146101f4576000506101fb565b6005610100555b600b6040511461020c576000610211565b61ca11315b50600c60405114610223576000610228565b61ca113b5b50600d6040511461023b57600050610246565b60006000600061ca113c5b600e6040511461025757600061025c565b61ca113f5b5060156040511461026e576000610280565b6000600060006000600061ca11611000f15b506016604051146102925760006102a4565b6000600060006000600061ca11611000f25b506017604051146102b65760006102c6565b600060006000600061ca11611000f45b506018604051146102d85760006102e8565b600060006000600061ca11611000fa5b50601f604051146102fa57600061030f565b6000600060006000600064ca1100ca11611000f15b50602060405114610321576000610335565b6000600060006000600063ca110100611000f25b50602160405114610347576000610359565b600060006000600063ca110100611000f45b505a60205261022a60205160005103036001556044356040525a60005260016040511461038757600061038c565b610100545b5060026040511461039f576000506103a6565b6005610100555b600b604051146103b75760006103bc565b61ca11315b50600c604051146103ce5760006103d3565b61ca113b5b50600d604051146103e6576000506103f1565b60006000600061ca113c5b600e60405114610402576000610407565b61ca113f5b5060156040511461041957600061042b565b6000600060006000600061ca11611000f15b5060166040511461043d57600061044f565b6000600060006000600061ca11611000f25b50601760405114610461576000610471565b600060006000600061ca11611000f45b50601860405114610483576000610493565b600060006000600061ca11611000fa5b50601f604051146104a55760006104ba565b6000600060006000600064ca1100ca11611000f15b506020604051146104cc5760006104e0565b6000600060006000600063ca110100611000f25b506021604051146104f2576000610504565b600060006000600063ca110100611000f45b505a60205261022a602051600051030360025560006101005500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 18, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("00")),
                callee_1: Account(code=bytes.fromhex("6101005400")),
                callee_2: Account(code=bytes.fromhex("61ca113100")),
                contract: Account(
                    storage={0: 2208, 1: 90, 2: 2891},
                    code=bytes.fromhex(
                        "5a6000525a60205264ca1100ca11315063ca11010031506004356040525a600052600160405114610031576000610036565b610100545b5060026040511461004957600050610050565b6005610100555b600b60405114610061576000610066565b61ca11315b50600c6040511461007857600061007d565b61ca113b5b50600d604051146100905760005061009b565b60006000600061ca113c5b600e604051146100ac5760006100b1565b61ca113f5b506015604051146100c35760006100d5565b6000600060006000600061ca11611000f15b506016604051146100e75760006100f9565b6000600060006000600061ca11611000f25b5060176040511461010b57600061011b565b600060006000600061ca11611000f45b5060186040511461012d57600061013d565b600060006000600061ca11611000fa5b50601f6040511461014f576000610164565b6000600060006000600064ca1100ca11611000f15b5060206040511461017657600061018a565b6000600060006000600063ca110100611000f25b5060216040511461019c5760006101ae565b600060006000600063ca110100611000f45b505a60205261022a60205160005103036000556024356040525a6000526001604051146101dc5760006101e1565b610100545b506002604051146101f4576000506101fb565b6005610100555b600b6040511461020c576000610211565b61ca11315b50600c60405114610223576000610228565b61ca113b5b50600d6040511461023b57600050610246565b60006000600061ca113c5b600e6040511461025757600061025c565b61ca113f5b5060156040511461026e576000610280565b6000600060006000600061ca11611000f15b506016604051146102925760006102a4565b6000600060006000600061ca11611000f25b506017604051146102b65760006102c6565b600060006000600061ca11611000f45b506018604051146102d85760006102e8565b600060006000600061ca11611000fa5b50601f604051146102fa57600061030f565b6000600060006000600064ca1100ca11611000f15b50602060405114610321576000610335565b6000600060006000600063ca110100611000f25b50602160405114610347576000610359565b600060006000600063ca110100611000f45b505a60205261022a60205160005103036001556044356040525a60005260016040511461038757600061038c565b610100545b5060026040511461039f576000506103a6565b6005610100555b600b604051146103b75760006103bc565b61ca11315b50600c604051146103ce5760006103d3565b61ca113b5b50600d604051146103e6576000506103f1565b60006000600061ca113c5b600e60405114610402576000610407565b61ca113f5b5060156040511461041957600061042b565b6000600060006000600061ca11611000f15b5060166040511461043d57600061044f565b6000600060006000600061ca11611000f25b50601760405114610461576000610471565b600060006000600061ca11611000f45b50601860405114610483576000610493565b600060006000600061ca11611000fa5b50601f604051146104a55760006104ba565b6000600060006000600064ca1100ca11611000f15b506020604051146104cc5760006104e0565b6000600060006000600063ca110100611000f25b506021604051146104f2576000610504565b600060006000600063ca110100611000f45b505a60205261022a602051600051030360025560006101005500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 12, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("00")),
                callee_1: Account(code=bytes.fromhex("6101005400")),
                callee_2: Account(code=bytes.fromhex("61ca113100")),
                contract: Account(
                    storage={0: 2211, 1: 211, 2: 211},
                    code=bytes.fromhex(
                        "5a6000525a60205264ca1100ca11315063ca11010031506004356040525a600052600160405114610031576000610036565b610100545b5060026040511461004957600050610050565b6005610100555b600b60405114610061576000610066565b61ca11315b50600c6040511461007857600061007d565b61ca113b5b50600d604051146100905760005061009b565b60006000600061ca113c5b600e604051146100ac5760006100b1565b61ca113f5b506015604051146100c35760006100d5565b6000600060006000600061ca11611000f15b506016604051146100e75760006100f9565b6000600060006000600061ca11611000f25b5060176040511461010b57600061011b565b600060006000600061ca11611000f45b5060186040511461012d57600061013d565b600060006000600061ca11611000fa5b50601f6040511461014f576000610164565b6000600060006000600064ca1100ca11611000f15b5060206040511461017657600061018a565b6000600060006000600063ca110100611000f25b5060216040511461019c5760006101ae565b600060006000600063ca110100611000f45b505a60205261022a60205160005103036000556024356040525a6000526001604051146101dc5760006101e1565b610100545b506002604051146101f4576000506101fb565b6005610100555b600b6040511461020c576000610211565b61ca11315b50600c60405114610223576000610228565b61ca113b5b50600d6040511461023b57600050610246565b60006000600061ca113c5b600e6040511461025757600061025c565b61ca113f5b5060156040511461026e576000610280565b6000600060006000600061ca11611000f15b506016604051146102925760006102a4565b6000600060006000600061ca11611000f25b506017604051146102b65760006102c6565b600060006000600061ca11611000f45b506018604051146102d85760006102e8565b600060006000600061ca11611000fa5b50601f604051146102fa57600061030f565b6000600060006000600064ca1100ca11611000f15b50602060405114610321576000610335565b6000600060006000600063ca110100611000f25b50602160405114610347576000610359565b600060006000600063ca110100611000f45b505a60205261022a60205160005103036001556044356040525a60005260016040511461038757600061038c565b610100545b5060026040511461039f576000506103a6565b6005610100555b600b604051146103b75760006103bc565b61ca11315b50600c604051146103ce5760006103d3565b61ca113b5b50600d604051146103e6576000506103f1565b60006000600061ca113c5b600e60405114610402576000610407565b61ca113f5b5060156040511461041957600061042b565b6000600060006000600061ca11611000f15b5060166040511461043d57600061044f565b6000600060006000600061ca11611000f25b50601760405114610461576000610471565b600060006000600061ca11611000f45b50601860405114610483576000610493565b600060006000600061ca11611000fa5b50601f604051146104a55760006104ba565b6000600060006000600064ca1100ca11611000f15b506020604051146104cc5760006104e0565b6000600060006000600063ca110100611000f25b506021604051146104f2576000610504565b600060006000600063ca110100611000f45b505a60205261022a602051600051030360025560006101005500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 17, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("00")),
                callee_1: Account(code=bytes.fromhex("6101005400")),
                callee_2: Account(code=bytes.fromhex("61ca113100")),
                contract: Account(
                    storage={0: 2211, 1: 90, 2: 208},
                    code=bytes.fromhex(
                        "5a6000525a60205264ca1100ca11315063ca11010031506004356040525a600052600160405114610031576000610036565b610100545b5060026040511461004957600050610050565b6005610100555b600b60405114610061576000610066565b61ca11315b50600c6040511461007857600061007d565b61ca113b5b50600d604051146100905760005061009b565b60006000600061ca113c5b600e604051146100ac5760006100b1565b61ca113f5b506015604051146100c35760006100d5565b6000600060006000600061ca11611000f15b506016604051146100e75760006100f9565b6000600060006000600061ca11611000f25b5060176040511461010b57600061011b565b600060006000600061ca11611000f45b5060186040511461012d57600061013d565b600060006000600061ca11611000fa5b50601f6040511461014f576000610164565b6000600060006000600064ca1100ca11611000f15b5060206040511461017657600061018a565b6000600060006000600063ca110100611000f25b5060216040511461019c5760006101ae565b600060006000600063ca110100611000f45b505a60205261022a60205160005103036000556024356040525a6000526001604051146101dc5760006101e1565b610100545b506002604051146101f4576000506101fb565b6005610100555b600b6040511461020c576000610211565b61ca11315b50600c60405114610223576000610228565b61ca113b5b50600d6040511461023b57600050610246565b60006000600061ca113c5b600e6040511461025757600061025c565b61ca113f5b5060156040511461026e576000610280565b6000600060006000600061ca11611000f15b506016604051146102925760006102a4565b6000600060006000600061ca11611000f25b506017604051146102b65760006102c6565b600060006000600061ca11611000f45b506018604051146102d85760006102e8565b600060006000600061ca11611000fa5b50601f604051146102fa57600061030f565b6000600060006000600064ca1100ca11611000f15b50602060405114610321576000610335565b6000600060006000600063ca110100611000f25b50602160405114610347576000610359565b600060006000600063ca110100611000f45b505a60205261022a60205160005103036001556044356040525a60005260016040511461038757600061038c565b610100545b5060026040511461039f576000506103a6565b6005610100555b600b604051146103b75760006103bc565b61ca11315b50600c604051146103ce5760006103d3565b61ca113b5b50600d604051146103e6576000506103f1565b60006000600061ca113c5b600e60405114610402576000610407565b61ca113f5b5060156040511461041957600061042b565b6000600060006000600061ca11611000f15b5060166040511461043d57600061044f565b6000600060006000600061ca11611000f25b50601760405114610461576000610471565b600060006000600061ca11611000f45b50601860405114610483576000610493565b600060006000600061ca11611000fa5b50601f604051146104a55760006104ba565b6000600060006000600064ca1100ca11611000f15b506020604051146104cc5760006104e0565b6000600060006000600063ca110100611000f25b506021604051146104f2576000610504565b600060006000600063ca110100611000f45b505a60205261022a602051600051030360025560006101005500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("00")),
                callee_1: Account(code=bytes.fromhex("6101005400")),
                callee_2: Account(code=bytes.fromhex("61ca113100")),
                contract: Account(
                    code=bytes.fromhex(
                        "5a6000525a60205264ca1100ca11315063ca11010031506004356040525a600052600160405114610031576000610036565b610100545b5060026040511461004957600050610050565b6005610100555b600b60405114610061576000610066565b61ca11315b50600c6040511461007857600061007d565b61ca113b5b50600d604051146100905760005061009b565b60006000600061ca113c5b600e604051146100ac5760006100b1565b61ca113f5b506015604051146100c35760006100d5565b6000600060006000600061ca11611000f15b506016604051146100e75760006100f9565b6000600060006000600061ca11611000f25b5060176040511461010b57600061011b565b600060006000600061ca11611000f45b5060186040511461012d57600061013d565b600060006000600061ca11611000fa5b50601f6040511461014f576000610164565b6000600060006000600064ca1100ca11611000f15b5060206040511461017657600061018a565b6000600060006000600063ca110100611000f25b5060216040511461019c5760006101ae565b600060006000600063ca110100611000f45b505a60205261022a60205160005103036000556024356040525a6000526001604051146101dc5760006101e1565b610100545b506002604051146101f4576000506101fb565b6005610100555b600b6040511461020c576000610211565b61ca11315b50600c60405114610223576000610228565b61ca113b5b50600d6040511461023b57600050610246565b60006000600061ca113c5b600e6040511461025757600061025c565b61ca113f5b5060156040511461026e576000610280565b6000600060006000600061ca11611000f15b506016604051146102925760006102a4565b6000600060006000600061ca11611000f25b506017604051146102b65760006102c6565b600060006000600061ca11611000f45b506018604051146102d85760006102e8565b600060006000600061ca11611000fa5b50601f604051146102fa57600061030f565b6000600060006000600064ca1100ca11611000f15b50602060405114610321576000610335565b6000600060006000600063ca110100611000f25b50602160405114610347576000610359565b600060006000600063ca110100611000f45b505a60205261022a60205160005103036001556044356040525a60005260016040511461038757600061038c565b610100545b5060026040511461039f576000506103a6565b6005610100555b600b604051146103b75760006103bc565b61ca11315b50600c604051146103ce5760006103d3565b61ca113b5b50600d604051146103e6576000506103f1565b60006000600061ca113c5b600e60405114610402576000610407565b61ca113f5b5060156040511461041957600061042b565b6000600060006000600061ca11611000f15b5060166040511461043d57600061044f565b6000600060006000600061ca11611000f25b50601760405114610461576000610471565b600060006000600061ca11611000f45b50601860405114610483576000610493565b600060006000600061ca11611000fa5b50601f604051146104a55760006104ba565b6000600060006000600064ca1100ca11611000f15b506020604051146104cc5760006104e0565b6000600060006000600063ca110100611000f25b506021604051146104f2576000610504565b600060006000600063ca110100611000f45b505a60205261022a602051600051030360025560006101005500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 15, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("00")),
                callee_1: Account(code=bytes.fromhex("6101005400")),
                callee_2: Account(code=bytes.fromhex("61ca113100")),
                contract: Account(
                    storage={0: 2090, 1: 211, 2: 208},
                    code=bytes.fromhex(
                        "5a6000525a60205264ca1100ca11315063ca11010031506004356040525a600052600160405114610031576000610036565b610100545b5060026040511461004957600050610050565b6005610100555b600b60405114610061576000610066565b61ca11315b50600c6040511461007857600061007d565b61ca113b5b50600d604051146100905760005061009b565b60006000600061ca113c5b600e604051146100ac5760006100b1565b61ca113f5b506015604051146100c35760006100d5565b6000600060006000600061ca11611000f15b506016604051146100e75760006100f9565b6000600060006000600061ca11611000f25b5060176040511461010b57600061011b565b600060006000600061ca11611000f45b5060186040511461012d57600061013d565b600060006000600061ca11611000fa5b50601f6040511461014f576000610164565b6000600060006000600064ca1100ca11611000f15b5060206040511461017657600061018a565b6000600060006000600063ca110100611000f25b5060216040511461019c5760006101ae565b600060006000600063ca110100611000f45b505a60205261022a60205160005103036000556024356040525a6000526001604051146101dc5760006101e1565b610100545b506002604051146101f4576000506101fb565b6005610100555b600b6040511461020c576000610211565b61ca11315b50600c60405114610223576000610228565b61ca113b5b50600d6040511461023b57600050610246565b60006000600061ca113c5b600e6040511461025757600061025c565b61ca113f5b5060156040511461026e576000610280565b6000600060006000600061ca11611000f15b506016604051146102925760006102a4565b6000600060006000600061ca11611000f25b506017604051146102b65760006102c6565b600060006000600061ca11611000f45b506018604051146102d85760006102e8565b600060006000600061ca11611000fa5b50601f604051146102fa57600061030f565b6000600060006000600064ca1100ca11611000f15b50602060405114610321576000610335565b6000600060006000600063ca110100611000f25b50602160405114610347576000610359565b600060006000600063ca110100611000f45b505a60205261022a60205160005103036001556044356040525a60005260016040511461038757600061038c565b610100545b5060026040511461039f576000506103a6565b6005610100555b600b604051146103b75760006103bc565b61ca11315b50600c604051146103ce5760006103d3565b61ca113b5b50600d604051146103e6576000506103f1565b60006000600061ca113c5b600e60405114610402576000610407565b61ca113f5b5060156040511461041957600061042b565b6000600060006000600061ca11611000f15b5060166040511461043d57600061044f565b6000600060006000600061ca11611000f25b50601760405114610461576000610471565b600060006000600061ca11611000f45b50601860405114610483576000610493565b600060006000600061ca11611000fa5b50601f604051146104a55760006104ba565b6000600060006000600064ca1100ca11611000f15b506020604051146104cc5760006104e0565b6000600060006000600063ca110100611000f25b506021604051146104f2576000610504565b600060006000600063ca110100611000f45b505a60205261022a602051600051030360025560006101005500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("00")),
                callee_1: Account(code=bytes.fromhex("6101005400")),
                callee_2: Account(code=bytes.fromhex("61ca113100")),
                contract: Account(
                    storage={0: 2090, 1: 90, 2: 90},
                    code=bytes.fromhex(
                        "5a6000525a60205264ca1100ca11315063ca11010031506004356040525a600052600160405114610031576000610036565b610100545b5060026040511461004957600050610050565b6005610100555b600b60405114610061576000610066565b61ca11315b50600c6040511461007857600061007d565b61ca113b5b50600d604051146100905760005061009b565b60006000600061ca113c5b600e604051146100ac5760006100b1565b61ca113f5b506015604051146100c35760006100d5565b6000600060006000600061ca11611000f15b506016604051146100e75760006100f9565b6000600060006000600061ca11611000f25b5060176040511461010b57600061011b565b600060006000600061ca11611000f45b5060186040511461012d57600061013d565b600060006000600061ca11611000fa5b50601f6040511461014f576000610164565b6000600060006000600064ca1100ca11611000f15b5060206040511461017657600061018a565b6000600060006000600063ca110100611000f25b5060216040511461019c5760006101ae565b600060006000600063ca110100611000f45b505a60205261022a60205160005103036000556024356040525a6000526001604051146101dc5760006101e1565b610100545b506002604051146101f4576000506101fb565b6005610100555b600b6040511461020c576000610211565b61ca11315b50600c60405114610223576000610228565b61ca113b5b50600d6040511461023b57600050610246565b60006000600061ca113c5b600e6040511461025757600061025c565b61ca113f5b5060156040511461026e576000610280565b6000600060006000600061ca11611000f15b506016604051146102925760006102a4565b6000600060006000600061ca11611000f25b506017604051146102b65760006102c6565b600060006000600061ca11611000f45b506018604051146102d85760006102e8565b600060006000600061ca11611000fa5b50601f604051146102fa57600061030f565b6000600060006000600064ca1100ca11611000f15b50602060405114610321576000610335565b6000600060006000600063ca110100611000f25b50602160405114610347576000610359565b600060006000600063ca110100611000f45b505a60205261022a60205160005103036001556044356040525a60005260016040511461038757600061038c565b610100545b5060026040511461039f576000506103a6565b6005610100555b600b604051146103b75760006103bc565b61ca11315b50600c604051146103ce5760006103d3565b61ca113b5b50600d604051146103e6576000506103f1565b60006000600061ca113c5b600e60405114610402576000610407565b61ca113f5b5060156040511461041957600061042b565b6000600060006000600061ca11611000f15b5060166040511461043d57600061044f565b6000600060006000600061ca11611000f25b50601760405114610461576000610471565b600060006000600061ca11611000f45b50601860405114610483576000610493565b600060006000600061ca11611000fa5b50601f604051146104a55760006104ba565b6000600060006000600064ca1100ca11611000f15b506020604051146104cc5760006104e0565b6000600060006000600063ca110100611000f25b506021604051146104f2576000610504565b600060006000600063ca110100611000f45b505a60205261022a602051600051030360025560006101005500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 16, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("00")),
                callee_1: Account(code=bytes.fromhex("6101005400")),
                callee_2: Account(code=bytes.fromhex("61ca113100")),
                contract: Account(
                    storage={0: 2090, 1: 2891, 2: 208},
                    code=bytes.fromhex(
                        "5a6000525a60205264ca1100ca11315063ca11010031506004356040525a600052600160405114610031576000610036565b610100545b5060026040511461004957600050610050565b6005610100555b600b60405114610061576000610066565b61ca11315b50600c6040511461007857600061007d565b61ca113b5b50600d604051146100905760005061009b565b60006000600061ca113c5b600e604051146100ac5760006100b1565b61ca113f5b506015604051146100c35760006100d5565b6000600060006000600061ca11611000f15b506016604051146100e75760006100f9565b6000600060006000600061ca11611000f25b5060176040511461010b57600061011b565b600060006000600061ca11611000f45b5060186040511461012d57600061013d565b600060006000600061ca11611000fa5b50601f6040511461014f576000610164565b6000600060006000600064ca1100ca11611000f15b5060206040511461017657600061018a565b6000600060006000600063ca110100611000f25b5060216040511461019c5760006101ae565b600060006000600063ca110100611000f45b505a60205261022a60205160005103036000556024356040525a6000526001604051146101dc5760006101e1565b610100545b506002604051146101f4576000506101fb565b6005610100555b600b6040511461020c576000610211565b61ca11315b50600c60405114610223576000610228565b61ca113b5b50600d6040511461023b57600050610246565b60006000600061ca113c5b600e6040511461025757600061025c565b61ca113f5b5060156040511461026e576000610280565b6000600060006000600061ca11611000f15b506016604051146102925760006102a4565b6000600060006000600061ca11611000f25b506017604051146102b65760006102c6565b600060006000600061ca11611000f45b506018604051146102d85760006102e8565b600060006000600061ca11611000fa5b50601f604051146102fa57600061030f565b6000600060006000600064ca1100ca11611000f15b50602060405114610321576000610335565b6000600060006000600063ca110100611000f25b50602160405114610347576000610359565b600060006000600063ca110100611000f45b505a60205261022a60205160005103036001556044356040525a60005260016040511461038757600061038c565b610100545b5060026040511461039f576000506103a6565b6005610100555b600b604051146103b75760006103bc565b61ca11315b50600c604051146103ce5760006103d3565b61ca113b5b50600d604051146103e6576000506103f1565b60006000600061ca113c5b600e60405114610402576000610407565b61ca113f5b5060156040511461041957600061042b565b6000600060006000600061ca11611000f15b5060166040511461043d57600061044f565b6000600060006000600061ca11611000f25b50601760405114610461576000610471565b600060006000600061ca11611000f45b50601860405114610483576000610493565b600060006000600061ca11611000fa5b50601f604051146104a55760006104ba565b6000600060006000600064ca1100ca11611000f15b506020604051146104cc5760006104e0565b6000600060006000600063ca110100611000f25b506021604051146104f2576000610504565b600060006000600063ca110100611000f45b505a60205261022a602051600051030360025560006101005500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 14, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("00")),
                callee_1: Account(code=bytes.fromhex("6101005400")),
                callee_2: Account(code=bytes.fromhex("61ca113100")),
                contract: Account(
                    storage={0: 2090, 1: 2891, 2: 90},
                    code=bytes.fromhex(
                        "5a6000525a60205264ca1100ca11315063ca11010031506004356040525a600052600160405114610031576000610036565b610100545b5060026040511461004957600050610050565b6005610100555b600b60405114610061576000610066565b61ca11315b50600c6040511461007857600061007d565b61ca113b5b50600d604051146100905760005061009b565b60006000600061ca113c5b600e604051146100ac5760006100b1565b61ca113f5b506015604051146100c35760006100d5565b6000600060006000600061ca11611000f15b506016604051146100e75760006100f9565b6000600060006000600061ca11611000f25b5060176040511461010b57600061011b565b600060006000600061ca11611000f45b5060186040511461012d57600061013d565b600060006000600061ca11611000fa5b50601f6040511461014f576000610164565b6000600060006000600064ca1100ca11611000f15b5060206040511461017657600061018a565b6000600060006000600063ca110100611000f25b5060216040511461019c5760006101ae565b600060006000600063ca110100611000f45b505a60205261022a60205160005103036000556024356040525a6000526001604051146101dc5760006101e1565b610100545b506002604051146101f4576000506101fb565b6005610100555b600b6040511461020c576000610211565b61ca11315b50600c60405114610223576000610228565b61ca113b5b50600d6040511461023b57600050610246565b60006000600061ca113c5b600e6040511461025757600061025c565b61ca113f5b5060156040511461026e576000610280565b6000600060006000600061ca11611000f15b506016604051146102925760006102a4565b6000600060006000600061ca11611000f25b506017604051146102b65760006102c6565b600060006000600061ca11611000f45b506018604051146102d85760006102e8565b600060006000600061ca11611000fa5b50601f604051146102fa57600061030f565b6000600060006000600064ca1100ca11611000f15b50602060405114610321576000610335565b6000600060006000600063ca110100611000f25b50602160405114610347576000610359565b600060006000600063ca110100611000f45b505a60205261022a60205160005103036001556044356040525a60005260016040511461038757600061038c565b610100545b5060026040511461039f576000506103a6565b6005610100555b600b604051146103b75760006103bc565b61ca11315b50600c604051146103ce5760006103d3565b61ca113b5b50600d604051146103e6576000506103f1565b60006000600061ca113c5b600e60405114610402576000610407565b61ca113f5b5060156040511461041957600061042b565b6000600060006000600061ca11611000f15b5060166040511461043d57600061044f565b6000600060006000600061ca11611000f25b50601760405114610461576000610471565b600060006000600061ca11611000f45b50601860405114610483576000610493565b600060006000600061ca11611000fa5b50601f604051146104a55760006104ba565b6000600060006000600064ca1100ca11611000f15b506020604051146104cc5760006104e0565b6000600060006000600063ca110100611000f25b506021604051146104f2576000610504565b600060006000600063ca110100611000f45b505a60205261022a602051600051030360025560006101005500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 2, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("00")),
                callee_1: Account(code=bytes.fromhex("6101005400")),
                callee_2: Account(code=bytes.fromhex("61ca113100")),
                contract: Account(
                    storage={0: 4991, 1: 91, 2: 91},
                    code=bytes.fromhex(
                        "5a6000525a60205264ca1100ca11315063ca11010031506004356040525a600052600160405114610031576000610036565b610100545b5060026040511461004957600050610050565b6005610100555b600b60405114610061576000610066565b61ca11315b50600c6040511461007857600061007d565b61ca113b5b50600d604051146100905760005061009b565b60006000600061ca113c5b600e604051146100ac5760006100b1565b61ca113f5b506015604051146100c35760006100d5565b6000600060006000600061ca11611000f15b506016604051146100e75760006100f9565b6000600060006000600061ca11611000f25b5060176040511461010b57600061011b565b600060006000600061ca11611000f45b5060186040511461012d57600061013d565b600060006000600061ca11611000fa5b50601f6040511461014f576000610164565b6000600060006000600064ca1100ca11611000f15b5060206040511461017657600061018a565b6000600060006000600063ca110100611000f25b5060216040511461019c5760006101ae565b600060006000600063ca110100611000f45b505a60205261022a60205160005103036000556024356040525a6000526001604051146101dc5760006101e1565b610100545b506002604051146101f4576000506101fb565b6005610100555b600b6040511461020c576000610211565b61ca11315b50600c60405114610223576000610228565b61ca113b5b50600d6040511461023b57600050610246565b60006000600061ca113c5b600e6040511461025757600061025c565b61ca113f5b5060156040511461026e576000610280565b6000600060006000600061ca11611000f15b506016604051146102925760006102a4565b6000600060006000600061ca11611000f25b506017604051146102b65760006102c6565b600060006000600061ca11611000f45b506018604051146102d85760006102e8565b600060006000600061ca11611000fa5b50601f604051146102fa57600061030f565b6000600060006000600064ca1100ca11611000f15b50602060405114610321576000610335565b6000600060006000600063ca110100611000f25b50602160405114610347576000610359565b600060006000600063ca110100611000f45b505a60205261022a60205160005103036001556044356040525a60005260016040511461038757600061038c565b610100545b5060026040511461039f576000506103a6565b6005610100555b600b604051146103b75760006103bc565b61ca11315b50600c604051146103ce5760006103d3565b61ca113b5b50600d604051146103e6576000506103f1565b60006000600061ca113c5b600e60405114610402576000610407565b61ca113f5b5060156040511461041957600061042b565b6000600060006000600061ca11611000f15b5060166040511461043d57600061044f565b6000600060006000600061ca11611000f25b50601760405114610461576000610471565b600060006000600061ca11611000f45b50601860405114610483576000610493565b600060006000600061ca11611000fa5b50601f604051146104a55760006104ba565b6000600060006000600064ca1100ca11611000f15b506020604051146104cc5760006104e0565b6000600060006000600063ca110100611000f25b506021604051146104f2576000610504565b600060006000600063ca110100611000f45b505a60205261022a602051600051030360025560006101005500"  # noqa: E501
                    ),
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
