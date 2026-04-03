"""
Test_test_contract_interaction.

Ported from:
state_tests/stSolidityTest/TestContractInteractionFiller.json
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
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stSolidityTest/TestContractInteractionFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_test_contract_interaction(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_test_contract_interaction."""
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
    # 0x7c01000000000000000000000000000000000000000000000000000000006000350463c04062268114610039578063ed973fe91461004b57005b6100416100ea565b8060005260206000f35b61005361005d565b8060005260206000f35b60006000608161011a600039608160006000f0905073ffffffffffffffffffffffffffffffffffffffff811663b9c3d0a5602060007fb9c3d0a50000000000000000000000000000000000000000000000000000000081526004600060008660325a03f16100c757005b505060005160e1146100d8576100e1565b600191506100e6565b600091505b5090565b60006100f461005d565b600060006101000a81548160ff0219169083021790555060ff600160005404169050905600607580600c6000396000f3007c01000000000000000000000000000000000000000000000000000000006000350462f55d9d81146036578063b9c3d0a514604557005b603f6004356055565b60006000f35b604b6070565b8060005260206000f35b8073ffffffffffffffffffffffffffffffffffffffff16ff50565b60e19056  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.DIV(
            Op.CALLDATALOAD(offset=0x0),
            0x100000000000000000000000000000000000000000000000000000000,
        )
        + Op.JUMPI(pc=Op.PUSH2[0x39], condition=Op.EQ(Op.DUP2, 0xC0406226))
        + Op.JUMPI(pc=Op.PUSH2[0x4B], condition=Op.EQ(0xED973FE9, Op.DUP1))
        + Op.STOP
        + Op.JUMPDEST
        + Op.PUSH2[0x41]
        + Op.JUMP(pc=Op.PUSH2[0xEA])
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.RETURN(offset=0x0, size=0x20)
        + Op.JUMPDEST
        + Op.PUSH2[0x53]
        + Op.JUMP(pc=Op.PUSH2[0x5D])
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.RETURN(offset=0x0, size=0x20)
        + Op.JUMPDEST
        + Op.PUSH1[0x0] * 2
        + Op.CODECOPY(dest_offset=0x0, offset=0x11A, size=0x81)
        + Op.CREATE(value=0x0, offset=0x0, size=0x81)
        + Op.SWAP1
        + Op.POP
        + Op.AND(Op.DUP2, 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
        + Op.PUSH4[0xB9C3D0A5]
        + Op.PUSH1[0x20]
        + Op.PUSH1[0x0]
        + Op.MSTORE(
            offset=Op.DUP2,
            value=0xB9C3D0A500000000000000000000000000000000000000000000000000000000,  # noqa: E501
        )
        + Op.PUSH1[0x4]
        + Op.PUSH1[0x0] * 2
        + Op.DUP7
        + Op.SUB(Op.GAS, 0x32)
        + Op.JUMPI(pc=Op.PUSH2[0xC7], condition=Op.CALL)
        + Op.STOP
        + Op.JUMPDEST
        + Op.POP * 2
        + Op.JUMPI(
            pc=Op.PUSH2[0xD8], condition=Op.EQ(0xE1, Op.MLOAD(offset=0x0))
        )
        + Op.JUMP(pc=Op.PUSH2[0xE1])
        + Op.JUMPDEST
        + Op.PUSH1[0x1]
        + Op.SWAP2
        + Op.POP
        + Op.JUMP(pc=Op.PUSH2[0xE6])
        + Op.JUMPDEST
        + Op.PUSH1[0x0]
        + Op.SWAP2
        + Op.POP
        + Op.JUMPDEST
        + Op.POP
        + Op.SWAP1
        + Op.JUMP
        + Op.JUMPDEST
        + Op.PUSH1[0x0]
        + Op.PUSH2[0xF4]
        + Op.JUMP(pc=Op.PUSH2[0x5D])
        + Op.JUMPDEST
        + Op.PUSH1[0x0]
        + Op.EXP(0x100, 0x0)
        + Op.AND(Op.NOT(Op.MUL(0xFF, Op.DUP2)), Op.SLOAD(key=Op.DUP2))
        + Op.SWAP1
        + Op.OR(Op.MUL, Op.DUP4)
        + Op.SWAP1
        + Op.SSTORE
        + Op.POP
        + Op.AND(Op.DIV(Op.SLOAD(key=0x0), 0x1), 0xFF)
        + Op.SWAP1
        + Op.POP
        + Op.SWAP1
        + Op.JUMP
        + Op.STOP
        + Op.PUSH1[0x75]
        + Op.CODECOPY(dest_offset=0x0, offset=0xC, size=Op.DUP1)
        + Op.PUSH1[0x0]
        + Op.RETURN
        + Op.STOP
        + Op.DIV(
            Op.CALLDATALOAD(offset=0x0),
            0x100000000000000000000000000000000000000000000000000000000,
        )
        + Op.JUMPI(pc=0x36, condition=Op.EQ(Op.DUP2, 0xF55D9D))
        + Op.JUMPI(pc=0x45, condition=Op.EQ(0xB9C3D0A5, Op.DUP1))
        + Op.STOP
        + Op.JUMPDEST
        + Op.PUSH1[0x3F]
        + Op.CALLDATALOAD(offset=0x4)
        + Op.JUMP(pc=0x55)
        + Op.JUMPDEST
        + Op.RETURN(offset=0x0, size=0x0)
        + Op.JUMPDEST
        + Op.PUSH1[0x4B]
        + Op.JUMP(pc=0x70)
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.RETURN(offset=0x0, size=0x20)
        + Op.JUMPDEST
        + Op.SELFDESTRUCT(
            address=Op.AND(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF, Op.DUP1)
        )
        + Op.POP
        + Op.JUMP
        + Op.JUMPDEST
        + Op.PUSH1[0xE1]
        + Op.SWAP1
        + Op.JUMP,
        balance=0x186A0,
        nonce=0,
        address=Address(0x087DFEC56D6DA95FD3A1BCF8CCF995EE51645950),  # noqa: E501
    )
    pre[sender] = Account(balance=0x5F5E100)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes("c0406226"),
        gas_limit=350000,
        value=1,
    )

    post = {target: Account(storage={0: 1}, nonce=1)}

    state_test(env=env, pre=pre, post=post, tx=tx)
