"""
Test_test_structures_and_variabless.

Ported from:
state_tests/stSolidityTest/TestStructuresAndVariablessFiller.json
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
    ["state_tests/stSolidityTest/TestStructuresAndVariablessFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_test_structures_and_variabless(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_test_structures_and_variabless."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0x6F0117D3E9C684C7D6E1E6B79DC3880DA2BEBE77C765B171C062FDFFD38A673F
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    pre[sender] = Account(balance=0x2540BE400)
    # Source: raw
    # 0x7c010000000000000000000000000000000000000000000000000000000060003504632a9afb838114610039578063c04062261461004b57005b61004161005d565b8060005260206000f35b61005361016c565b8060005260206000f35b600160ff8154141561006e57610076565b506000610169565b60015460035414156100875761008f565b506000610169565b73<eoa:sender:0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b>73ffffffffffffffffffffffffffffffffffffffff60016002540481161614156100cd576100d5565b506000610169565b7f676c6f62616c2064617461203332206c656e67746820737472696e670000000060045414156101045761010c565b506000610169565b6005600080815260200190815260200160002060009054906101000a900473ffffffffffffffffffffffffffffffffffffffff1673<eoa:sender:0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b>141561016057610168565b506000610169565b5b90565b600060ff806001555073<eoa:sender:0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b>6002805473ffffffffffffffffffffffffffffffffffffffff1916821790555060ff80600355507f676c6f62616c2064617461203332206c656e67746820737472696e6700000000806004555073<eoa:sender:0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b>6005600080815260200190815260200160002060006101000a81548173ffffffffffffffffffffffffffffffffffffffff0219169083021790555061022f61005d565b600060006101000a81548160ff0219169083021790555060ff6001600054041690509056  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.DIV(
            Op.CALLDATALOAD(offset=0x0),
            0x100000000000000000000000000000000000000000000000000000000,
        )
        + Op.JUMPI(pc=Op.PUSH2[0x39], condition=Op.EQ(Op.DUP2, 0x2A9AFB83))
        + Op.JUMPI(pc=Op.PUSH2[0x4B], condition=Op.EQ(0xC0406226, Op.DUP1))
        + Op.STOP
        + Op.JUMPDEST
        + Op.PUSH2[0x41]
        + Op.JUMP(pc=Op.PUSH2[0x5D])
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.RETURN(offset=0x0, size=0x20)
        + Op.JUMPDEST
        + Op.PUSH2[0x53]
        + Op.JUMP(pc=0x16C)
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.RETURN(offset=0x0, size=0x20)
        + Op.JUMPDEST
        + Op.PUSH1[0x1]
        + Op.JUMPI(
            pc=Op.PUSH2[0x6E],
            condition=Op.ISZERO(Op.EQ(Op.SLOAD(key=Op.DUP2), 0xFF)),
        )
        + Op.JUMP(pc=Op.PUSH2[0x76])
        + Op.JUMPDEST
        + Op.POP
        + Op.PUSH1[0x0]
        + Op.JUMP(pc=0x169)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=Op.PUSH2[0x87],
            condition=Op.ISZERO(Op.EQ(Op.SLOAD(key=0x3), Op.SLOAD(key=0x1))),
        )
        + Op.JUMP(pc=Op.PUSH2[0x8F])
        + Op.JUMPDEST
        + Op.POP
        + Op.PUSH1[0x0]
        + Op.JUMP(pc=0x169)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=Op.PUSH2[0xCD],
            condition=Op.ISZERO(
                Op.EQ(
                    Op.AND(
                        Op.AND(Op.DUP2, Op.DIV(Op.SLOAD(key=0x2), 0x1)),
                        0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
                    ),
                    sender,
                )
            ),
        )
        + Op.JUMP(pc=Op.PUSH2[0xD5])
        + Op.JUMPDEST
        + Op.POP
        + Op.PUSH1[0x0]
        + Op.JUMP(pc=0x169)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=0x104,
            condition=Op.ISZERO(
                Op.EQ(
                    Op.SLOAD(key=0x4),
                    0x676C6F62616C2064617461203332206C656E67746820737472696E6700000000,  # noqa: E501
                )
            ),
        )
        + Op.JUMP(pc=0x10C)
        + Op.JUMPDEST
        + Op.POP
        + Op.PUSH1[0x0]
        + Op.JUMP(pc=0x169)
        + Op.JUMPDEST
        + Op.PUSH1[0x5]
        + Op.PUSH1[0x0]
        + Op.MSTORE(offset=Op.DUP2, value=Op.DUP1)
        + Op.PUSH1[0x20]
        + Op.ADD
        + Op.SWAP1
        + Op.DUP2
        + Op.MSTORE
        + Op.PUSH1[0x20]
        + Op.SHA3(offset=0x0, size=Op.ADD)
        + Op.PUSH1[0x0]
        + Op.SWAP1
        + Op.SLOAD
        + Op.SWAP1
        + Op.PUSH2[0x100]
        + Op.EXP
        + Op.SWAP1
        + Op.JUMPI(
            pc=0x160,
            condition=Op.ISZERO(
                Op.EQ(
                    sender,
                    Op.AND(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF, Op.DIV),
                )
            ),
        )
        + Op.JUMP(pc=0x168)
        + Op.JUMPDEST
        + Op.POP
        + Op.PUSH1[0x0]
        + Op.JUMP(pc=0x169)
        + Op.JUMPDEST * 2
        + Op.SWAP1
        + Op.JUMP
        + Op.JUMPDEST
        + Op.PUSH1[0x0]
        + Op.PUSH1[0xFF]
        + Op.SSTORE(key=0x1, value=Op.DUP1)
        + Op.POP
        + Op.PUSH20[0xD96ED4431B417993AB4F4D4A656959D13C66E1DC]
        + Op.PUSH1[0x2]
        + Op.OR(
            Op.DUP3,
            Op.AND(
                Op.NOT(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF),
                Op.SLOAD(key=Op.DUP1),
            ),
        )
        + Op.SWAP1
        + Op.SSTORE
        + Op.POP
        + Op.PUSH1[0xFF]
        + Op.SSTORE(key=0x3, value=Op.DUP1)
        + Op.POP
        + Op.PUSH32[
            0x676C6F62616C2064617461203332206C656E67746820737472696E6700000000
        ]
        + Op.SSTORE(key=0x4, value=Op.DUP1)
        + Op.POP
        + Op.PUSH20[0xD96ED4431B417993AB4F4D4A656959D13C66E1DC]
        + Op.PUSH1[0x5]
        + Op.PUSH1[0x0]
        + Op.MSTORE(offset=Op.DUP2, value=Op.DUP1)
        + Op.PUSH1[0x20]
        + Op.ADD
        + Op.SWAP1
        + Op.DUP2
        + Op.MSTORE
        + Op.PUSH1[0x20]
        + Op.SHA3(offset=0x0, size=Op.ADD)
        + Op.EXP(0x100, 0x0)
        + Op.AND(
            Op.NOT(
                Op.MUL(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF, Op.DUP2)
            ),
            Op.SLOAD(key=Op.DUP2),
        )
        + Op.SWAP1
        + Op.OR(Op.MUL, Op.DUP4)
        + Op.SWAP1
        + Op.SSTORE
        + Op.POP
        + Op.PUSH2[0x22F]
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
        + Op.JUMP,
        balance=0x186A0,
        nonce=0,
        address=Address(0x53D3DBDFD3AE109712A4771F7F37A6B1CDA7B864),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes("c0406226"),
        gas_limit=350000,
        value=100,
    )

    post = {
        target: Account(
            storage={
                0: 1,
                1: 255,
                2: sender,
                3: 255,
                4: 0x676C6F62616C2064617461203332206C656E67746820737472696E6700000000,  # noqa: E501
                0x5B8CCBB9D4D8FB16EA74CE3C29A41F1B461FBDAFF4714A0D9A8EB05499746BC: sender,  # noqa: E501
            },
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
