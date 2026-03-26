"""
Ori Pomerantz qbzzt1@gmail.com

Ported from:
state_tests/stEIP150singleCodeGasPrices/eip2929Filler.yml
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
from execution_testing.vm import Op
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)

REFERENCE_SPEC_GIT_PATH = "N/A"

REFERENCE_SPEC_VERSION = "N/A"

TX_DATA = [
    "048071d3000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
    "048071d3000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000001",
    "048071d3000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000002",
    "048071d3000000000000000000000000000000000000000000000000000000000000000b000000000000000000000000000000000000000000000000000000000000000b000000000000000000000000000000000000000000000000000000000000000b",
    "048071d3000000000000000000000000000000000000000000000000000000000000000c000000000000000000000000000000000000000000000000000000000000000c000000000000000000000000000000000000000000000000000000000000000c",
    "048071d3000000000000000000000000000000000000000000000000000000000000000d000000000000000000000000000000000000000000000000000000000000000d000000000000000000000000000000000000000000000000000000000000000d",
    "048071d3000000000000000000000000000000000000000000000000000000000000000e000000000000000000000000000000000000000000000000000000000000000e000000000000000000000000000000000000000000000000000000000000000e",
    "048071d3000000000000000000000000000000000000000000000000000000000000001500000000000000000000000000000000000000000000000000000000000000150000000000000000000000000000000000000000000000000000000000000015",
    "048071d3000000000000000000000000000000000000000000000000000000000000001600000000000000000000000000000000000000000000000000000000000000160000000000000000000000000000000000000000000000000000000000000016",
    "048071d3000000000000000000000000000000000000000000000000000000000000001700000000000000000000000000000000000000000000000000000000000000170000000000000000000000000000000000000000000000000000000000000017",
    "048071d3000000000000000000000000000000000000000000000000000000000000001800000000000000000000000000000000000000000000000000000000000000180000000000000000000000000000000000000000000000000000000000000018",
    "048071d3000000000000000000000000000000000000000000000000000000000000001f000000000000000000000000000000000000000000000000000000000000001f000000000000000000000000000000000000000000000000000000000000001f",
    "048071d3000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000020",
    "048071d3000000000000000000000000000000000000000000000000000000000000002100000000000000000000000000000000000000000000000000000000000000210000000000000000000000000000000000000000000000000000000000000021",
    "048071d3000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000001",
    "048071d3000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000021",
    "048071d3000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000021",
    "048071d3000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000021",
    "048071d3000000000000000000000000000000000000000000000000000000000000002100000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000002",
    "048071d3000000000000000000000000000000000000000000000000000000000000000b000000000000000000000000000000000000000000000000000000000000000c000000000000000000000000000000000000000000000000000000000000000e",
    "048071d3000000000000000000000000000000000000000000000000000000000000000b000000000000000000000000000000000000000000000000000000000000000e000000000000000000000000000000000000000000000000000000000000000c",
    "048071d3000000000000000000000000000000000000000000000000000000000000000c000000000000000000000000000000000000000000000000000000000000000b000000000000000000000000000000000000000000000000000000000000000e",
    "048071d3000000000000000000000000000000000000000000000000000000000000000c000000000000000000000000000000000000000000000000000000000000000e000000000000000000000000000000000000000000000000000000000000000b",
    "048071d3000000000000000000000000000000000000000000000000000000000000000e000000000000000000000000000000000000000000000000000000000000000c000000000000000000000000000000000000000000000000000000000000000b",
    "048071d3000000000000000000000000000000000000000000000000000000000000000e000000000000000000000000000000000000000000000000000000000000000b000000000000000000000000000000000000000000000000000000000000000c",
    "048071d3000000000000000000000000000000000000000000000000000000000000001500000000000000000000000000000000000000000000000000000000000000160000000000000000000000000000000000000000000000000000000000000015",
    "048071d3000000000000000000000000000000000000000000000000000000000000001600000000000000000000000000000000000000000000000000000000000000160000000000000000000000000000000000000000000000000000000000000015",
    "048071d3000000000000000000000000000000000000000000000000000000000000001700000000000000000000000000000000000000000000000000000000000000180000000000000000000000000000000000000000000000000000000000000017",
    "048071d3000000000000000000000000000000000000000000000000000000000000001700000000000000000000000000000000000000000000000000000000000000180000000000000000000000000000000000000000000000000000000000000018",
    "048071d3000000000000000000000000000000000000000000000000000000000000000b00000000000000000000000000000000000000000000000000000000000000150000000000000000000000000000000000000000000000000000000000000016",
    "048071d3000000000000000000000000000000000000000000000000000000000000000c00000000000000000000000000000000000000000000000000000000000000150000000000000000000000000000000000000000000000000000000000000016",
    "048071d3000000000000000000000000000000000000000000000000000000000000000e00000000000000000000000000000000000000000000000000000000000000150000000000000000000000000000000000000000000000000000000000000016",
    "048071d3000000000000000000000000000000000000000000000000000000000000000b00000000000000000000000000000000000000000000000000000000000000160000000000000000000000000000000000000000000000000000000000000015",
    "048071d3000000000000000000000000000000000000000000000000000000000000000c00000000000000000000000000000000000000000000000000000000000000160000000000000000000000000000000000000000000000000000000000000015",
    "048071d3000000000000000000000000000000000000000000000000000000000000000e00000000000000000000000000000000000000000000000000000000000000160000000000000000000000000000000000000000000000000000000000000015",
    "048071d3000000000000000000000000000000000000000000000000000000000000000b000000000000000000000000000000000000000000000000000000000000000c000000000000000000000000000000000000000000000000000000000000001f",
    "048071d3000000000000000000000000000000000000000000000000000000000000000b000000000000000000000000000000000000000000000000000000000000001f000000000000000000000000000000000000000000000000000000000000000e",
    "048071d3000000000000000000000000000000000000000000000000000000000000001f000000000000000000000000000000000000000000000000000000000000000e000000000000000000000000000000000000000000000000000000000000000b",
]
TX_GAS = [16777216]
TX_VALUE = [1]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/stEIP150singleCodeGasPrices/eip2929Filler.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0, 0, 0,
            id="nop-nop-nop",
        ),
        pytest.param(
            1, 0, 0,
            id="sload-sload-sload",
        ),
        pytest.param(
            2, 0, 0,
            id="sstore-sstore-sstore",
        ),
        pytest.param(
            3, 0, 0,
            id="addr-addr-addr",
        ),
        pytest.param(
            4, 0, 0,
            id="addr-addr-addr",
        ),
        pytest.param(
            5, 0, 0,
            id="copy-copy-copy",
        ),
        pytest.param(
            6, 0, 0,
            id="addr-addr-addr",
        ),
        pytest.param(
            7, 0, 0,
            id="call8-call8-call8",
        ),
        pytest.param(
            8, 0, 0,
            id="call8-call8-call8",
        ),
        pytest.param(
            9, 0, 0,
            id="call5-call5-call5",
        ),
        pytest.param(
            10, 0, 0,
            id="call5-call5-call5",
        ),
        pytest.param(
            11, 0, 0,
            id="faraddr-faraddr-faraddr",
        ),
        pytest.param(
            12, 0, 0,
            id="farcall8-farcall8-farcall8",
        ),
        pytest.param(
            13, 0, 0,
            id="farcall5-farcall5-farcall5",
        ),
        pytest.param(
            14, 0, 0,
            id="sload-sstore-sload",
        ),
        pytest.param(
            15, 0, 0,
            id="sload-farcall8-farcall5",
        ),
        pytest.param(
            16, 0, 0,
            id="sload-sstore-farcall5",
        ),
        pytest.param(
            17, 0, 0,
            id="farcall8-sload-farcall5",
        ),
        pytest.param(
            18, 0, 0,
            id="farcall5-sload-sstore",
        ),
        pytest.param(
            19, 0, 0,
            id="addr-addr-addr",
        ),
        pytest.param(
            20, 0, 0,
            id="addr-addr-addr",
        ),
        pytest.param(
            21, 0, 0,
            id="addr-addr-addr",
        ),
        pytest.param(
            22, 0, 0,
            id="addr-addr-addr",
        ),
        pytest.param(
            23, 0, 0,
            id="addr-addr-addr",
        ),
        pytest.param(
            24, 0, 0,
            id="addr-addr-addr",
        ),
        pytest.param(
            25, 0, 0,
            id="call8-call8-call8",
        ),
        pytest.param(
            26, 0, 0,
            id="call8-call8-call8",
        ),
        pytest.param(
            27, 0, 0,
            id="call5-call5-call5",
        ),
        pytest.param(
            28, 0, 0,
            id="call5-call5-call5",
        ),
        pytest.param(
            29, 0, 0,
            id="addr-call8-call8",
        ),
        pytest.param(
            30, 0, 0,
            id="addr-call8-call8",
        ),
        pytest.param(
            31, 0, 0,
            id="addr-call8-call8",
        ),
        pytest.param(
            32, 0, 0,
            id="addr-call8-call8",
        ),
        pytest.param(
            33, 0, 0,
            id="addr-call8-call8",
        ),
        pytest.param(
            34, 0, 0,
            id="addr-call8-call8",
        ),
        pytest.param(
            35, 0, 0,
            id="addr-addr-faraddr",
        ),
        pytest.param(
            36, 0, 0,
            id="addr-faraddr-addr",
        ),
        pytest.param(
            37, 0, 0,
            id="faraddr-addr-addr",
        ),
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
    """Ori Pomerantz qbzzt1@gmail."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    contract_0 = Address("0x000000000000000000000000000000000000ca11")
    contract_1 = Address("0x000000000000000000000000000000ca1100ca11")
    contract_2 = Address("0x00000000000000000000000000000000ca110100")
    contract_3 = Address("0xcccccccccccccccccccccccccccccccccccccccc")
    sender = EOA(
        key=0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    # Source: raw
    # 0x00
    contract_0 = pre.deploy_contract(
        code=Op.STOP,
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0x000000000000000000000000000000000000ca11"),  # noqa: E501
    )
    # Source: lll
    # {
    #      (balance 0xca11)
    # }
    contract_1 = pre.deploy_contract(
        code=Op.BALANCE(address=0xca11) + Op.STOP,
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0x000000000000000000000000000000ca1100ca11"),  # noqa: E501
    )
    # Source: lll
    # {
    #     @@0x100
    # }
    contract_2 = pre.deploy_contract(
        code=Op.SLOAD(key=0x100) + Op.STOP,
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0x00000000000000000000000000000000ca110100"),  # noqa: E501
    )
    # Source: lll
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
    #        (if (= @operation 13) (extcodecopy 0xca11 0 0 0) NOP) ; EXTCODECOPY
    #        (if (= @operation 14) (extcodehash 0xca11) NOP) ; EXTCODEHASH
    #        (if (= @operation 21) (call 0x1000 0xca11 0 0 0 0 0) NOP) ; CALL
    #        (if (= @operation 22) (callcode 0x1000 0xca11 0 0 0 0 0) NOP) ; CALLCODE
    # ... (35 more lines)
    contract_3 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.MSTORE(offset=0x20, value=Op.GAS)
        + Op.POP(Op.BALANCE(address=0xca1100ca11))
        + Op.POP(Op.BALANCE(address=0xca110100))
        + Op.MSTORE(offset=0x40, value=Op.CALLDATALOAD(offset=0x4))
        + Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.JUMPI(pc=Op.PUSH2[0x31], condition=Op.EQ(Op.MLOAD(offset=0x40), 0x1))
        + Op.PUSH1[0x0] + Op.JUMP(pc=Op.PUSH2[0x36]) + Op.JUMPDEST
        + Op.SLOAD(key=0x100) + Op.JUMPDEST + Op.POP
        + Op.JUMPI(pc=Op.PUSH2[0x49], condition=Op.EQ(Op.MLOAD(offset=0x40), 0x2))
        + Op.POP(0x0) + Op.JUMP(pc=Op.PUSH2[0x50]) + Op.JUMPDEST
        + Op.SSTORE(key=0x100, value=0x5) + Op.JUMPDEST
        + Op.JUMPI(pc=Op.PUSH2[0x61], condition=Op.EQ(Op.MLOAD(offset=0x40), 0xb))
        + Op.PUSH1[0x0] + Op.JUMP(pc=Op.PUSH2[0x66]) + Op.JUMPDEST
        + Op.BALANCE(address=0xca11) + Op.JUMPDEST + Op.POP
        + Op.JUMPI(pc=Op.PUSH2[0x78], condition=Op.EQ(Op.MLOAD(offset=0x40), 0xc))
        + Op.PUSH1[0x0] + Op.JUMP(pc=Op.PUSH2[0x7d]) + Op.JUMPDEST
        + Op.EXTCODESIZE(address=0xca11) + Op.JUMPDEST + Op.POP
        + Op.JUMPI(pc=Op.PUSH2[0x90], condition=Op.EQ(Op.MLOAD(offset=0x40), 0xd))
        + Op.POP(0x0) + Op.JUMP(pc=Op.PUSH2[0x9b]) + Op.JUMPDEST
        + Op.EXTCODECOPY(address=0xca11, dest_offset=0x0, offset=0x0, size=0x0)
        + Op.JUMPDEST
        + Op.JUMPI(pc=Op.PUSH2[0xac], condition=Op.EQ(Op.MLOAD(offset=0x40), 0xe))
        + Op.PUSH1[0x0] + Op.JUMP(pc=Op.PUSH2[0xb1]) + Op.JUMPDEST
        + Op.EXTCODEHASH(address=0xca11) + Op.JUMPDEST + Op.POP
        + Op.JUMPI(pc=Op.PUSH2[0xc3], condition=Op.EQ(Op.MLOAD(offset=0x40), 0x15))
        + Op.PUSH1[0x0] + Op.JUMP(pc=Op.PUSH2[0xd5]) + Op.JUMPDEST
        + Op.CALL(gas=0x1000, address=0xca11, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0)
        + Op.JUMPDEST + Op.POP
        + Op.JUMPI(pc=Op.PUSH2[0xe7], condition=Op.EQ(Op.MLOAD(offset=0x40), 0x16))
        + Op.PUSH1[0x0] + Op.JUMP(pc=Op.PUSH2[0xf9]) + Op.JUMPDEST
        + Op.CALLCODE(gas=0x1000, address=0xca11, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0)
        + Op.JUMPDEST + Op.POP
        + Op.JUMPI(pc=0x10b, condition=Op.EQ(Op.MLOAD(offset=0x40), 0x17))
        + Op.PUSH1[0x0] + Op.JUMP(pc=0x11b) + Op.JUMPDEST
        + Op.DELEGATECALL(gas=0x1000, address=0xca11, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0)
        + Op.JUMPDEST + Op.POP
        + Op.JUMPI(pc=0x12d, condition=Op.EQ(Op.MLOAD(offset=0x40), 0x18))
        + Op.PUSH1[0x0] + Op.JUMP(pc=0x13d) + Op.JUMPDEST
        + Op.STATICCALL(gas=0x1000, address=0xca11, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0)
        + Op.JUMPDEST + Op.POP
        + Op.JUMPI(pc=0x14f, condition=Op.EQ(Op.MLOAD(offset=0x40), 0x1f))
        + Op.PUSH1[0x0] + Op.JUMP(pc=0x164) + Op.JUMPDEST
        + Op.CALL(gas=0x1000, address=0xca1100ca11, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0)
        + Op.JUMPDEST + Op.POP
        + Op.JUMPI(pc=0x176, condition=Op.EQ(Op.MLOAD(offset=0x40), 0x20))
        + Op.PUSH1[0x0] + Op.JUMP(pc=0x18a) + Op.JUMPDEST
        + Op.CALLCODE(gas=0x1000, address=0xca110100, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0)
        + Op.JUMPDEST + Op.POP
        + Op.JUMPI(pc=0x19c, condition=Op.EQ(Op.MLOAD(offset=0x40), 0x21))
        + Op.PUSH1[0x0] + Op.JUMP(pc=0x1ae) + Op.JUMPDEST
        + Op.DELEGATECALL(gas=0x1000, address=0xca110100, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0)
        + Op.JUMPDEST + Op.POP + Op.MSTORE(offset=0x20, value=Op.GAS)
        + Op.SSTORE(key=0x0, value=Op.SUB(Op.SUB(Op.MLOAD(offset=0x0), Op.MLOAD(offset=0x20)), 0x22a))  # noqa: E501
        + Op.MSTORE(offset=0x40, value=Op.CALLDATALOAD(offset=0x24))
        + Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.JUMPI(pc=0x1dc, condition=Op.EQ(Op.MLOAD(offset=0x40), 0x1))
        + Op.PUSH1[0x0] + Op.JUMP(pc=0x1e1) + Op.JUMPDEST + Op.SLOAD(key=0x100)
        + Op.JUMPDEST + Op.POP
        + Op.JUMPI(pc=0x1f4, condition=Op.EQ(Op.MLOAD(offset=0x40), 0x2))
        + Op.POP(0x0) + Op.JUMP(pc=0x1fb) + Op.JUMPDEST
        + Op.SSTORE(key=0x100, value=0x5) + Op.JUMPDEST
        + Op.JUMPI(pc=0x20c, condition=Op.EQ(Op.MLOAD(offset=0x40), 0xb))
        + Op.PUSH1[0x0] + Op.JUMP(pc=0x211) + Op.JUMPDEST
        + Op.BALANCE(address=0xca11) + Op.JUMPDEST + Op.POP
        + Op.JUMPI(pc=0x223, condition=Op.EQ(Op.MLOAD(offset=0x40), 0xc))
        + Op.PUSH1[0x0] + Op.JUMP(pc=0x228) + Op.JUMPDEST
        + Op.EXTCODESIZE(address=0xca11) + Op.JUMPDEST + Op.POP
        + Op.JUMPI(pc=0x23b, condition=Op.EQ(Op.MLOAD(offset=0x40), 0xd))
        + Op.POP(0x0) + Op.JUMP(pc=0x246) + Op.JUMPDEST
        + Op.EXTCODECOPY(address=0xca11, dest_offset=0x0, offset=0x0, size=0x0)
        + Op.JUMPDEST
        + Op.JUMPI(pc=0x257, condition=Op.EQ(Op.MLOAD(offset=0x40), 0xe))
        + Op.PUSH1[0x0] + Op.JUMP(pc=0x25c) + Op.JUMPDEST
        + Op.EXTCODEHASH(address=0xca11) + Op.JUMPDEST + Op.POP
        + Op.JUMPI(pc=0x26e, condition=Op.EQ(Op.MLOAD(offset=0x40), 0x15))
        + Op.PUSH1[0x0] + Op.JUMP(pc=0x280) + Op.JUMPDEST
        + Op.CALL(gas=0x1000, address=0xca11, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0)
        + Op.JUMPDEST + Op.POP
        + Op.JUMPI(pc=0x292, condition=Op.EQ(Op.MLOAD(offset=0x40), 0x16))
        + Op.PUSH1[0x0] + Op.JUMP(pc=0x2a4) + Op.JUMPDEST
        + Op.CALLCODE(gas=0x1000, address=0xca11, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0)
        + Op.JUMPDEST + Op.POP
        + Op.JUMPI(pc=0x2b6, condition=Op.EQ(Op.MLOAD(offset=0x40), 0x17))
        + Op.PUSH1[0x0] + Op.JUMP(pc=0x2c6) + Op.JUMPDEST
        + Op.DELEGATECALL(gas=0x1000, address=0xca11, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0)
        + Op.JUMPDEST + Op.POP
        + Op.JUMPI(pc=0x2d8, condition=Op.EQ(Op.MLOAD(offset=0x40), 0x18))
        + Op.PUSH1[0x0] + Op.JUMP(pc=0x2e8) + Op.JUMPDEST
        + Op.STATICCALL(gas=0x1000, address=0xca11, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0)
        + Op.JUMPDEST + Op.POP
        + Op.JUMPI(pc=0x2fa, condition=Op.EQ(Op.MLOAD(offset=0x40), 0x1f))
        + Op.PUSH1[0x0] + Op.JUMP(pc=0x30f) + Op.JUMPDEST
        + Op.CALL(gas=0x1000, address=0xca1100ca11, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0)
        + Op.JUMPDEST + Op.POP
        + Op.JUMPI(pc=0x321, condition=Op.EQ(Op.MLOAD(offset=0x40), 0x20))
        + Op.PUSH1[0x0] + Op.JUMP(pc=0x335) + Op.JUMPDEST
        + Op.CALLCODE(gas=0x1000, address=0xca110100, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0)
        + Op.JUMPDEST + Op.POP
        + Op.JUMPI(pc=0x347, condition=Op.EQ(Op.MLOAD(offset=0x40), 0x21))
        + Op.PUSH1[0x0] + Op.JUMP(pc=0x359) + Op.JUMPDEST
        + Op.DELEGATECALL(gas=0x1000, address=0xca110100, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0)
        + Op.JUMPDEST + Op.POP + Op.MSTORE(offset=0x20, value=Op.GAS)
        + Op.SSTORE(key=0x1, value=Op.SUB(Op.SUB(Op.MLOAD(offset=0x0), Op.MLOAD(offset=0x20)), 0x22a))  # noqa: E501
        + Op.MSTORE(offset=0x40, value=Op.CALLDATALOAD(offset=0x44))
        + Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.JUMPI(pc=0x387, condition=Op.EQ(Op.MLOAD(offset=0x40), 0x1))
        + Op.PUSH1[0x0] + Op.JUMP(pc=0x38c) + Op.JUMPDEST + Op.SLOAD(key=0x100)
        + Op.JUMPDEST + Op.POP
        + Op.JUMPI(pc=0x39f, condition=Op.EQ(Op.MLOAD(offset=0x40), 0x2))
        + Op.POP(0x0) + Op.JUMP(pc=0x3a6) + Op.JUMPDEST
        + Op.SSTORE(key=0x100, value=0x5) + Op.JUMPDEST
        + Op.JUMPI(pc=0x3b7, condition=Op.EQ(Op.MLOAD(offset=0x40), 0xb))
        + Op.PUSH1[0x0] + Op.JUMP(pc=0x3bc) + Op.JUMPDEST
        + Op.BALANCE(address=0xca11) + Op.JUMPDEST + Op.POP
        + Op.JUMPI(pc=0x3ce, condition=Op.EQ(Op.MLOAD(offset=0x40), 0xc))
        + Op.PUSH1[0x0] + Op.JUMP(pc=0x3d3) + Op.JUMPDEST
        + Op.EXTCODESIZE(address=0xca11) + Op.JUMPDEST + Op.POP
        + Op.JUMPI(pc=0x3e6, condition=Op.EQ(Op.MLOAD(offset=0x40), 0xd))
        + Op.POP(0x0) + Op.JUMP(pc=0x3f1) + Op.JUMPDEST
        + Op.EXTCODECOPY(address=0xca11, dest_offset=0x0, offset=0x0, size=0x0)
        + Op.JUMPDEST
        + Op.JUMPI(pc=0x402, condition=Op.EQ(Op.MLOAD(offset=0x40), 0xe))
        + Op.PUSH1[0x0] + Op.JUMP(pc=0x407) + Op.JUMPDEST
        + Op.EXTCODEHASH(address=0xca11) + Op.JUMPDEST + Op.POP
        + Op.JUMPI(pc=0x419, condition=Op.EQ(Op.MLOAD(offset=0x40), 0x15))
        + Op.PUSH1[0x0] + Op.JUMP(pc=0x42b) + Op.JUMPDEST
        + Op.CALL(gas=0x1000, address=0xca11, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0)
        + Op.JUMPDEST + Op.POP
        + Op.JUMPI(pc=0x43d, condition=Op.EQ(Op.MLOAD(offset=0x40), 0x16))
        + Op.PUSH1[0x0] + Op.JUMP(pc=0x44f) + Op.JUMPDEST
        + Op.CALLCODE(gas=0x1000, address=0xca11, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0)
        + Op.JUMPDEST + Op.POP
        + Op.JUMPI(pc=0x461, condition=Op.EQ(Op.MLOAD(offset=0x40), 0x17))
        + Op.PUSH1[0x0] + Op.JUMP(pc=0x471) + Op.JUMPDEST
        + Op.DELEGATECALL(gas=0x1000, address=0xca11, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0)
        + Op.JUMPDEST + Op.POP
        + Op.JUMPI(pc=0x483, condition=Op.EQ(Op.MLOAD(offset=0x40), 0x18))
        + Op.PUSH1[0x0] + Op.JUMP(pc=0x493) + Op.JUMPDEST
        + Op.STATICCALL(gas=0x1000, address=0xca11, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0)
        + Op.JUMPDEST + Op.POP
        + Op.JUMPI(pc=0x4a5, condition=Op.EQ(Op.MLOAD(offset=0x40), 0x1f))
        + Op.PUSH1[0x0] + Op.JUMP(pc=0x4ba) + Op.JUMPDEST
        + Op.CALL(gas=0x1000, address=0xca1100ca11, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0)
        + Op.JUMPDEST + Op.POP
        + Op.JUMPI(pc=0x4cc, condition=Op.EQ(Op.MLOAD(offset=0x40), 0x20))
        + Op.PUSH1[0x0] + Op.JUMP(pc=0x4e0) + Op.JUMPDEST
        + Op.CALLCODE(gas=0x1000, address=0xca110100, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0)
        + Op.JUMPDEST + Op.POP
        + Op.JUMPI(pc=0x4f2, condition=Op.EQ(Op.MLOAD(offset=0x40), 0x21))
        + Op.PUSH1[0x0] + Op.JUMP(pc=0x504) + Op.JUMPDEST
        + Op.DELEGATECALL(gas=0x1000, address=0xca110100, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0)
        + Op.JUMPDEST + Op.POP + Op.MSTORE(offset=0x20, value=Op.GAS)
        + Op.SSTORE(key=0x2, value=Op.SUB(Op.SUB(Op.MLOAD(offset=0x0), Op.MLOAD(offset=0x20)), 0x22a))  # noqa: E501
        + Op.SSTORE(key=0x100, value=0x0) + Op.STOP,
        storage={256: 24743},
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0xcccccccccccccccccccccccccccccccccccccccc"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xba1a9ce0ba1a9ce)

    expect_entries_: list[dict] = [
        {
            "indexes": {'data': [0], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {contract_3: Account(storage={0: 0})},
        },
        {
            "indexes": {'data': [1], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {contract_3: Account(storage={0: 2090, 1: 90, 2: 90})},
        },
        {
            "indexes": {'data': [2], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {contract_3: Account(storage={0: 4991, 1: 91, 2: 91})},
        },
        {
            "indexes": {'data': [14], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {contract_3: Account(storage={0: 2090, 1: 2891, 2: 90})},
        },
        {
            "indexes": {'data': [3, 4, 6, 19, 20, 21, 22, 23, 24], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {contract_3: Account(storage={0: 2590, 1: 90, 2: 90})},
        },
        {
            "indexes": {'data': [5], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {contract_3: Account(storage={0: 2597, 1: 97, 2: 97})},
        },
        {
            "indexes": {'data': [8, 25, 26, 7], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {contract_3: Account(storage={0: 2608, 1: 108, 2: 108})},
        },
        {
            "indexes": {'data': [9, 10, 27, 28], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {contract_3: Account(storage={0: 2605, 1: 105, 2: 105})},
        },
        {
            "indexes": {'data': [32, 33, 34, 29, 30, 31], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {contract_3: Account(storage={0: 2590, 1: 108, 2: 108})},
        },
        {
            "indexes": {'data': [11], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {contract_3: Account(storage={0: 2711, 1: 211, 2: 211})},
        },
        {
            "indexes": {'data': [35], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {contract_3: Account(storage={0: 2590, 1: 90, 2: 211})},
        },
        {
            "indexes": {'data': [36], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {contract_3: Account(storage={0: 2590, 1: 211, 2: 90})},
        },
        {
            "indexes": {'data': [37], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {contract_3: Account(storage={0: 2711, 1: 90, 2: 90})},
        },
        {
            "indexes": {'data': [12], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {contract_3: Account(storage={0: 2211, 1: 211, 2: 211})},
        },
        {
            "indexes": {'data': [13], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {contract_3: Account(storage={0: 2208, 1: 208, 2: 208})},
        },
        {
            "indexes": {'data': [15], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {contract_3: Account(storage={0: 2090, 1: 211, 2: 208})},
        },
        {
            "indexes": {'data': [16], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {contract_3: Account(storage={0: 2090, 1: 2891, 2: 208})},
        },
        {
            "indexes": {'data': [17], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {contract_3: Account(storage={0: 2211, 1: 90, 2: 208})},
        },
        {
            "indexes": {'data': [18], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {contract_3: Account(storage={0: 2208, 1: 90, 2: 2891})},
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=contract_3,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        value=TX_VALUE[v],
        nonce=0,
        gas_price=10,
        error=_exc,
    )


    state_test(env=env, pre=pre, post=post, tx=tx)
