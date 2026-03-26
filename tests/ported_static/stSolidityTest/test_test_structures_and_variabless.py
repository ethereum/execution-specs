"""
test_test_structures_and_variabless

Ported from:
state_tests/stSolidityTest/TestStructuresAndVariablessFiller.json
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
    ["state_tests/stSolidityTest/TestStructuresAndVariablessFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_test_structures_and_variabless(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_test_structures_and_variabless"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x6f0117d3e9c684c7d6e1e6b79dc3880da2bebe77c765b171c062fdffd38a673f
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
    # 0x7c010000000000000000000000000000000000000000000000000000000060003504632a9afb838114610039578063c04062261461004b57005b61004161005d565b8060005260206000f35b61005361016c565b8060005260206000f35b600160ff8154141561006e57610076565b506000610169565b60015460035414156100875761008f565b506000610169565b73<eoa:sender:0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b>73ffffffffffffffffffffffffffffffffffffffff60016002540481161614156100cd576100d5565b506000610169565b7f676c6f62616c2064617461203332206c656e67746820737472696e670000000060045414156101045761010c565b506000610169565b6005600080815260200190815260200160002060009054906101000a900473ffffffffffffffffffffffffffffffffffffffff1673<eoa:sender:0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b>141561016057610168565b506000610169565b5b90565b600060ff806001555073<eoa:sender:0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b>6002805473ffffffffffffffffffffffffffffffffffffffff1916821790555060ff80600355507f676c6f62616c2064617461203332206c656e67746820737472696e6700000000806004555073<eoa:sender:0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b>6005600080815260200190815260200160002060006101000a81548173ffffffffffffffffffffffffffffffffffffffff0219169083021790555061022f61005d565b600060006101000a81548160ff0219169083021790555060ff6001600054041690509056
    target = pre.deploy_contract(
        code=Op.DIV(Op.CALLDATALOAD(offset=0x0), 0x100000000000000000000000000000000000000000000000000000000)
        + Op.JUMPI(pc=Op.PUSH2[0x39], condition=Op.EQ(Op.DUP2, 0x2a9afb83))
        + Op.JUMPI(pc=Op.PUSH2[0x4b], condition=Op.EQ(0xc0406226, Op.DUP1))
        + Op.STOP + Op.JUMPDEST + Op.PUSH2[0x41] + Op.JUMP(pc=Op.PUSH2[0x5d])
        + Op.JUMPDEST + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.RETURN(offset=0x0, size=0x20) + Op.JUMPDEST + Op.PUSH2[0x53]
        + Op.JUMP(pc=0x16c) + Op.JUMPDEST + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.RETURN(offset=0x0, size=0x20) + Op.JUMPDEST + Op.PUSH1[0x1]
        + Op.JUMPI(pc=Op.PUSH2[0x6e], condition=Op.ISZERO(Op.EQ(Op.SLOAD(key=Op.DUP2), 0xff)))  # noqa: E501
        + Op.JUMP(pc=Op.PUSH2[0x76]) + Op.JUMPDEST + Op.POP + Op.PUSH1[0x0]
        + Op.JUMP(pc=0x169) + Op.JUMPDEST
        + Op.JUMPI(pc=Op.PUSH2[0x87], condition=Op.ISZERO(Op.EQ(Op.SLOAD(key=0x3), Op.SLOAD(key=0x1))))  # noqa: E501
        + Op.JUMP(pc=Op.PUSH2[0x8f]) + Op.JUMPDEST + Op.POP + Op.PUSH1[0x0]
        + Op.JUMP(pc=0x169) + Op.JUMPDEST
        + Op.JUMPI(pc=Op.PUSH2[0xcd], condition=Op.ISZERO(Op.EQ(Op.AND(Op.AND(Op.DUP2, Op.DIV(Op.SLOAD(key=0x2), 0x1)), 0xffffffffffffffffffffffffffffffffffffffff), 0xd96ed4431b417993ab4f4d4a656959d13c66e1dc)))  # noqa: E501
        + Op.JUMP(pc=Op.PUSH2[0xd5]) + Op.JUMPDEST + Op.POP + Op.PUSH1[0x0]
        + Op.JUMP(pc=0x169) + Op.JUMPDEST
        + Op.JUMPI(pc=0x104, condition=Op.ISZERO(Op.EQ(Op.SLOAD(key=0x4), 0x676c6f62616c2064617461203332206c656e67746820737472696e6700000000)))  # noqa: E501
        + Op.JUMP(pc=0x10c) + Op.JUMPDEST + Op.POP + Op.PUSH1[0x0]
        + Op.JUMP(pc=0x169) + Op.JUMPDEST + Op.PUSH1[0x5] + Op.PUSH1[0x0]
        + Op.MSTORE(offset=Op.DUP2, value=Op.DUP1) + Op.PUSH1[0x20] + Op.ADD
        + Op.SWAP1 + Op.DUP2 + Op.MSTORE + Op.PUSH1[0x20]
        + Op.SHA3(offset=0x0, size=Op.ADD) + Op.PUSH1[0x0] + Op.SWAP1 + Op.SLOAD
        + Op.SWAP1 + Op.PUSH2[0x100] + Op.EXP + Op.SWAP1
        + Op.JUMPI(pc=0x160, condition=Op.ISZERO(Op.EQ(0xd96ed4431b417993ab4f4d4a656959d13c66e1dc, Op.AND(0xffffffffffffffffffffffffffffffffffffffff, Op.DIV))))
        + Op.JUMP(pc=0x168) + Op.JUMPDEST + Op.POP + Op.PUSH1[0x0]
        + Op.JUMP(pc=0x169) + Op.JUMPDEST * 2 + Op.SWAP1 + Op.JUMP + Op.JUMPDEST
        + Op.PUSH1[0x0] + Op.PUSH1[0xff] + Op.SSTORE(key=0x1, value=Op.DUP1)
        + Op.POP + Op.PUSH20[0xd96ed4431b417993ab4f4d4a656959d13c66e1dc]
        + Op.PUSH1[0x2]
        + Op.OR(Op.DUP3, Op.AND(Op.NOT(0xffffffffffffffffffffffffffffffffffffffff), Op.SLOAD(key=Op.DUP1)))  # noqa: E501
        + Op.SWAP1 + Op.SSTORE + Op.POP + Op.PUSH1[0xff]
        + Op.SSTORE(key=0x3, value=Op.DUP1) + Op.POP
        + Op.PUSH32[0x676c6f62616c2064617461203332206c656e67746820737472696e6700000000]
        + Op.SSTORE(key=0x4, value=Op.DUP1) + Op.POP
        + Op.PUSH20[0xd96ed4431b417993ab4f4d4a656959d13c66e1dc] + Op.PUSH1[0x5]
        + Op.PUSH1[0x0] + Op.MSTORE(offset=Op.DUP2, value=Op.DUP1)
        + Op.PUSH1[0x20] + Op.ADD + Op.SWAP1 + Op.DUP2 + Op.MSTORE
        + Op.PUSH1[0x20] + Op.SHA3(offset=0x0, size=Op.ADD) + Op.EXP(0x100, 0x0)
        + Op.AND(Op.NOT(Op.MUL(0xffffffffffffffffffffffffffffffffffffffff, Op.DUP2)), Op.SLOAD(key=Op.DUP2))  # noqa: E501
        + Op.SWAP1 + Op.OR(Op.MUL, Op.DUP4) + Op.SWAP1 + Op.SSTORE + Op.POP
        + Op.PUSH2[0x22f] + Op.JUMP(pc=Op.PUSH2[0x5d]) + Op.JUMPDEST
        + Op.PUSH1[0x0] + Op.EXP(0x100, 0x0)
        + Op.AND(Op.NOT(Op.MUL(0xff, Op.DUP2)), Op.SLOAD(key=Op.DUP2)) + Op.SWAP1  # noqa: E501
        + Op.OR(Op.MUL, Op.DUP4) + Op.SWAP1 + Op.SSTORE + Op.POP
        + Op.AND(Op.DIV(Op.SLOAD(key=0x0), 0x1), 0xff) + Op.SWAP1 + Op.POP
        + Op.SWAP1 + Op.JUMP,
        balance=0x186a0,
        nonce=0,
        address=Address("0x53d3dbdfd3ae109712a4771f7f37a6b1cda7b864"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x2540be400)


    tx = Transaction(
        sender=sender,
        to=target,
        data=bytes.fromhex("c0406226"),
        gas_limit=350000,
        value=100,
        nonce=0,
        gas_price=10,
    )

    post = {
        target: Account(
                storage={
            0: 1,
            1: 255,
            2: 0xd96ed4431b417993ab4f4d4a656959d13c66e1dc,
            3: 255,
            4: 0x676c6f62616c2064617461203332206c656e67746820737472696e6700000000,
            0x5b8ccbb9d4d8fb16ea74ce3c29a41f1b461fbdaff4714a0d9a8eb05499746bc: 0xd96ed4431b417993ab4f4d4a656959d13c66e1dc,
        },
            ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
