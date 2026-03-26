"""
test_test_overflow

Ported from:
state_tests/stSolidityTest/TestOverflowFiller.json
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
    """test_test_overflow"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xa9ae12cb2700c0214f86b9796881bc03a1fd5605d0e76d2da2ca592e62d53e52
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    # Source: raw
    # 0x6000357c0100000000000000000000000000000000000000000000000000000000900480638040cac41461003a578063c04062261461004c57005b610042610099565b8060005260206000f35b61005461005e565b8060005260206000f35b6000610068610099565b600060006101000a81548160ff02191690830217905550600060009054906101000a900460ff169050610096565b90565b60006000600060006001935083507fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff925060006001840114156100db576100e4565b6000935061013b565b63ffffffff915060006001830163ffffffff1614156101025761010b565b6000935061013b565b67ffffffffffffffff905060006001820167ffffffffffffffff1614156101315761013a565b6000935061013b565b5b5050509056
    target = pre.deploy_contract(
        code=Op.CALLDATALOAD(offset=0x0)
        + Op.PUSH29[0x100000000000000000000000000000000000000000000000000000000]
        + Op.SWAP1 + Op.DIV
        + Op.JUMPI(pc=Op.PUSH2[0x3a], condition=Op.EQ(0x8040cac4, Op.DUP1))
        + Op.JUMPI(pc=Op.PUSH2[0x4c], condition=Op.EQ(0xc0406226, Op.DUP1))
        + Op.STOP + Op.JUMPDEST + Op.PUSH2[0x42] + Op.JUMP(pc=Op.PUSH2[0x99])
        + Op.JUMPDEST + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.RETURN(offset=0x0, size=0x20) + Op.JUMPDEST + Op.PUSH2[0x54]
        + Op.JUMP(pc=Op.PUSH2[0x5e]) + Op.JUMPDEST
        + Op.MSTORE(offset=0x0, value=Op.DUP1) + Op.RETURN(offset=0x0, size=0x20)
        + Op.JUMPDEST + Op.PUSH1[0x0] + Op.PUSH2[0x68]
        + Op.JUMP(pc=Op.PUSH2[0x99]) + Op.JUMPDEST + Op.PUSH1[0x0]
        + Op.EXP(0x100, 0x0)
        + Op.AND(Op.NOT(Op.MUL(0xff, Op.DUP2)), Op.SLOAD(key=Op.DUP2)) + Op.SWAP1  # noqa: E501
        + Op.OR(Op.MUL, Op.DUP4) + Op.SWAP1 + Op.SSTORE + Op.POP
        + Op.PUSH1[0x0] * 2 + Op.SWAP1 + Op.SLOAD + Op.SWAP1 + Op.PUSH2[0x100]
        + Op.EXP + Op.SWAP1 + Op.AND(0xff, Op.DIV) + Op.SWAP1 + Op.POP
        + Op.JUMP(pc=Op.PUSH2[0x96]) + Op.JUMPDEST + Op.SWAP1 + Op.JUMP
        + Op.JUMPDEST + Op.PUSH1[0x0] * 4 + Op.PUSH1[0x1] + Op.SWAP4 + Op.POP
        + Op.POP(Op.DUP4)
        + Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
        + Op.SWAP3 + Op.POP
        + Op.JUMPI(pc=Op.PUSH2[0xdb], condition=Op.ISZERO(Op.EQ(Op.ADD(Op.DUP5, 0x1), 0x0)))
        + Op.JUMP(pc=Op.PUSH2[0xe4]) + Op.JUMPDEST + Op.PUSH1[0x0] + Op.SWAP4
        + Op.POP + Op.JUMP(pc=0x13b) + Op.JUMPDEST + Op.PUSH4[0xffffffff]
        + Op.SWAP2 + Op.POP
        + Op.JUMPI(pc=0x102, condition=Op.ISZERO(Op.EQ(Op.AND(0xffffffff, Op.ADD(Op.DUP4, 0x1)), 0x0)))
        + Op.JUMP(pc=0x10b) + Op.JUMPDEST + Op.PUSH1[0x0] + Op.SWAP4 + Op.POP
        + Op.JUMP(pc=0x13b) + Op.JUMPDEST + Op.PUSH8[0xffffffffffffffff]
        + Op.SWAP1 + Op.POP
        + Op.JUMPI(pc=0x131, condition=Op.ISZERO(Op.EQ(Op.AND(0xffffffffffffffff, Op.ADD(Op.DUP3, 0x1)), 0x0)))
        + Op.JUMP(pc=0x13a) + Op.JUMPDEST + Op.PUSH1[0x0] + Op.SWAP4 + Op.POP
        + Op.JUMP(pc=0x13b) + Op.JUMPDEST * 2 + Op.POP * 3 + Op.SWAP1 + Op.JUMP,
        balance=0x186a0,
        nonce=0,
        address=Address("0x1a5a251a7e18ebc1a8ebfc47e3f36d9be03f1627"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x12a05f200)


    tx = Transaction(
        sender=sender,
        to=target,
        data=bytes.fromhex("c0406226"),
        gas_limit=100000,
        nonce=0,
        gas_price=10,
    )

    post = {target: Account(storage={0: 1})}

    state_test(env=env, pre=pre, post=post, tx=tx)
