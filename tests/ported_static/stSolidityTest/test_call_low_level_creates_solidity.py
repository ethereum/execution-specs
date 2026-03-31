"""
Test_call_low_level_creates_solidity.

Ported from:
state_tests/stSolidityTest/CallLowLevelCreatesSolidityFiller.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    StateTestFiller,
    Transaction,
    Fork,
)
from execution_testing.vm import Op

from execution_testing.forks import Amsterdam

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stSolidityTest/CallLowLevelCreatesSolidityFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_call_low_level_creates_solidity(
    state_test: StateTestFiller,
    fork: Fork,
    pre: Alloc,
) -> None:
    """Test_call_low_level_creates_solidity."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0xA2333EEF5630066B928DEA5FD85A239F511B5B067D1441EE7AC290D0122B917B
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    # Source: raw
    # 0x60003560e060020a9004806330debb4214610021578063c04062261461003257005b61002c6004356100c7565b60006000f35b61003a610044565b8060005260206000f35b60006000600160008190555073<contract:target:0x095e7baea6a6c7c4c2dfeb977efac326af552d87>600181905550606a6100d2600039606a60006000f0905080600160a060020a03166319ab453c600060008260e060020a026000526004600154600160a060020a03168152602001600060008660325a03f16100bc57005b505060005491505090565b80600081905550505600605e80600c6000396000f30060003560e060020a9004806319ab453c14601557005b601e6004356024565b60006000f35b80600160a060020a03166330debb42600060008260e060020a02600052600460e18152602001600060008660325a03f1605957005b50505056  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.CALLDATALOAD(offset=0x0)
        + Op.EXP(0x2, 0xE0)
        + Op.SWAP1
        + Op.DIV
        + Op.JUMPI(pc=Op.PUSH2[0x21], condition=Op.EQ(0x30DEBB42, Op.DUP1))
        + Op.JUMPI(pc=Op.PUSH2[0x32], condition=Op.EQ(0xC0406226, Op.DUP1))
        + Op.STOP
        + Op.JUMPDEST
        + Op.PUSH2[0x2C]
        + Op.CALLDATALOAD(offset=0x4)
        + Op.JUMP(pc=Op.PUSH2[0xC7])
        + Op.JUMPDEST
        + Op.RETURN(offset=0x0, size=0x0)
        + Op.JUMPDEST
        + Op.PUSH2[0x3A]
        + Op.JUMP(pc=Op.PUSH2[0x44])
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.RETURN(offset=0x0, size=0x20)
        + Op.JUMPDEST
        + Op.PUSH1[0x0] * 2
        + Op.PUSH1[0x1]
        + Op.PUSH1[0x0]
        + Op.DUP2
        + Op.SWAP1
        + Op.SSTORE
        + Op.POP
        + Op.PUSH20[0x5DA6FBE439A0C3AB33F813671A4E7767EE0A263B]
        + Op.PUSH1[0x1]
        + Op.DUP2
        + Op.SWAP1
        + Op.SSTORE
        + Op.POP
        + Op.CODECOPY(dest_offset=0x0, offset=Op.PUSH2[0xD2], size=0x6A)
        + Op.CREATE(value=0x0, offset=0x0, size=0x6A)
        + Op.SWAP1
        + Op.POP
        + Op.AND(Op.SUB(Op.EXP(0x2, 0xA0), 0x1), Op.DUP1)
        + Op.PUSH4[0x19AB453C]
        + Op.PUSH1[0x0] * 2
        + Op.MSTORE(offset=0x0, value=Op.MUL(Op.EXP(0x2, 0xE0), Op.DUP3))
        + Op.PUSH1[0x4]
        + Op.MSTORE(
            offset=Op.DUP2,
            value=Op.AND(Op.SUB(Op.EXP(0x2, 0xA0), 0x1), Op.SLOAD(key=0x1)),
        )
        + Op.PUSH1[0x20]
        + Op.ADD
        + Op.PUSH1[0x0] * 2
        + Op.DUP7
        + Op.SUB(Op.GAS, 0x32)
        + Op.JUMPI(pc=Op.PUSH2[0xBC], condition=Op.CALL)
        + Op.STOP
        + Op.JUMPDEST
        + Op.POP * 2
        + Op.SLOAD(key=0x0)
        + Op.SWAP2
        + Op.POP * 2
        + Op.SWAP1
        + Op.JUMP
        + Op.JUMPDEST
        + Op.DUP1
        + Op.PUSH1[0x0]
        + Op.DUP2
        + Op.SWAP1
        + Op.SSTORE
        + Op.POP * 2
        + Op.JUMP
        + Op.STOP
        + Op.PUSH1[0x5E]
        + Op.CODECOPY(dest_offset=0x0, offset=0xC, size=Op.DUP1)
        + Op.PUSH1[0x0]
        + Op.RETURN
        + Op.STOP
        + Op.CALLDATALOAD(offset=0x0)
        + Op.EXP(0x2, 0xE0)
        + Op.SWAP1
        + Op.DIV
        + Op.JUMPI(pc=0x15, condition=Op.EQ(0x19AB453C, Op.DUP1))
        + Op.STOP
        + Op.JUMPDEST
        + Op.PUSH1[0x1E]
        + Op.CALLDATALOAD(offset=0x4)
        + Op.JUMP(pc=0x24)
        + Op.JUMPDEST
        + Op.RETURN(offset=0x0, size=0x0)
        + Op.JUMPDEST
        + Op.AND(Op.SUB(Op.EXP(0x2, 0xA0), 0x1), Op.DUP1)
        + Op.PUSH4[0x30DEBB42]
        + Op.PUSH1[0x0] * 2
        + Op.MSTORE(offset=0x0, value=Op.MUL(Op.EXP(0x2, 0xE0), Op.DUP3))
        + Op.PUSH1[0x4]
        + Op.MSTORE(offset=Op.DUP2, value=0xE1)
        + Op.PUSH1[0x20]
        + Op.ADD
        + Op.PUSH1[0x0] * 2
        + Op.DUP7
        + Op.SUB(Op.GAS, 0x32)
        + Op.JUMPI(pc=0x59, condition=Op.CALL)
        + Op.STOP
        + Op.JUMPDEST
        + Op.POP * 3
        + Op.JUMP,
        balance=0x186A0,
        nonce=0,
        address=Address(0x5DA6FBE439A0C3AB33F813671A4E7767EE0A263B),  # noqa: E501
    )
    pre[sender] = Account(balance=0x5F5E100)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes("c0406226"),
        gas_limit=2350000 if fork >= Amsterdam else 350000,
        value=1,
    )

    post = {
        target: Account(
            storage={
                0: 225,
                1: 0x5DA6FBE439A0C3AB33F813671A4E7767EE0A263B,
            },
            nonce=1,
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
