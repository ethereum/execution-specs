"""
Test_test_overflow.

Ported from:
state_tests/stSolidityTest/TestOverflowFiller.json
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
    ["state_tests/stSolidityTest/TestOverflowFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_test_overflow(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_test_overflow."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0xA9AE12CB2700C0214F86B9796881BC03A1FD5605D0E76D2DA2CA592E62D53E52
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
    )

    # Source: raw
    # 0x6000357c0100000000000000000000000000000000000000000000000000000000900480638040cac41461003a578063c04062261461004c57005b610042610099565b8060005260206000f35b61005461005e565b8060005260206000f35b6000610068610099565b600060006101000a81548160ff02191690830217905550600060009054906101000a900460ff169050610096565b90565b60006000600060006001935083507fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff925060006001840114156100db576100e4565b6000935061013b565b63ffffffff915060006001830163ffffffff1614156101025761010b565b6000935061013b565b67ffffffffffffffff905060006001820167ffffffffffffffff1614156101315761013a565b6000935061013b565b5b5050509056  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.CALLDATALOAD(offset=0x0)
        + Op.PUSH29[
            0x100000000000000000000000000000000000000000000000000000000
        ]
        + Op.SWAP1
        + Op.DIV
        + Op.JUMPI(pc=Op.PUSH2[0x3A], condition=Op.EQ(0x8040CAC4, Op.DUP1))
        + Op.JUMPI(pc=Op.PUSH2[0x4C], condition=Op.EQ(0xC0406226, Op.DUP1))
        + Op.STOP
        + Op.JUMPDEST
        + Op.PUSH2[0x42]
        + Op.JUMP(pc=Op.PUSH2[0x99])
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.RETURN(offset=0x0, size=0x20)
        + Op.JUMPDEST
        + Op.PUSH2[0x54]
        + Op.JUMP(pc=Op.PUSH2[0x5E])
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.RETURN(offset=0x0, size=0x20)
        + Op.JUMPDEST
        + Op.PUSH1[0x0]
        + Op.PUSH2[0x68]
        + Op.JUMP(pc=Op.PUSH2[0x99])
        + Op.JUMPDEST
        + Op.PUSH1[0x0]
        + Op.EXP(0x100, 0x0)
        + Op.AND(Op.NOT(Op.MUL(0xFF, Op.DUP2)), Op.SLOAD(key=Op.DUP2))
        + Op.SWAP1
        + Op.OR(Op.MUL, Op.DUP4)
        + Op.SWAP1
        + Op.SSTORE
        + Op.POP
        + Op.PUSH1[0x0] * 2
        + Op.SWAP1
        + Op.SLOAD
        + Op.SWAP1
        + Op.PUSH2[0x100]
        + Op.EXP
        + Op.SWAP1
        + Op.AND(0xFF, Op.DIV)
        + Op.SWAP1
        + Op.POP
        + Op.JUMP(pc=Op.PUSH2[0x96])
        + Op.JUMPDEST
        + Op.SWAP1
        + Op.JUMP
        + Op.JUMPDEST
        + Op.PUSH1[0x0] * 4
        + Op.PUSH1[0x1]
        + Op.SWAP4
        + Op.POP
        + Op.POP(Op.DUP4)
        + Op.PUSH32[
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        ]
        + Op.SWAP3
        + Op.POP
        + Op.JUMPI(
            pc=Op.PUSH2[0xDB],
            condition=Op.ISZERO(Op.EQ(Op.ADD(Op.DUP5, 0x1), 0x0)),
        )
        + Op.JUMP(pc=Op.PUSH2[0xE4])
        + Op.JUMPDEST
        + Op.PUSH1[0x0]
        + Op.SWAP4
        + Op.POP
        + Op.JUMP(pc=0x13B)
        + Op.JUMPDEST
        + Op.PUSH4[0xFFFFFFFF]
        + Op.SWAP2
        + Op.POP
        + Op.JUMPI(
            pc=0x102,
            condition=Op.ISZERO(
                Op.EQ(Op.AND(0xFFFFFFFF, Op.ADD(Op.DUP4, 0x1)), 0x0)
            ),
        )
        + Op.JUMP(pc=0x10B)
        + Op.JUMPDEST
        + Op.PUSH1[0x0]
        + Op.SWAP4
        + Op.POP
        + Op.JUMP(pc=0x13B)
        + Op.JUMPDEST
        + Op.PUSH8[0xFFFFFFFFFFFFFFFF]
        + Op.SWAP1
        + Op.POP
        + Op.JUMPI(
            pc=0x131,
            condition=Op.ISZERO(
                Op.EQ(Op.AND(0xFFFFFFFFFFFFFFFF, Op.ADD(Op.DUP3, 0x1)), 0x0)
            ),
        )
        + Op.JUMP(pc=0x13A)
        + Op.JUMPDEST
        + Op.PUSH1[0x0]
        + Op.SWAP4
        + Op.POP
        + Op.JUMP(pc=0x13B)
        + Op.JUMPDEST * 2
        + Op.POP * 3
        + Op.SWAP1
        + Op.JUMP,
        balance=0x186A0,
        nonce=0,
        address=Address(0x1A5A251A7E18EBC1A8EBFC47E3F36D9BE03F1627),  # noqa: E501
    )
    pre[sender] = Account(balance=0x12A05F200)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes("c0406226"),
        gas_limit=100000,
    )

    post = {target: Account(storage={0: 1})}

    state_test(env=env, pre=pre, post=post, tx=tx)
