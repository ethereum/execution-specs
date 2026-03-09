"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stSolidityTest
TestBlockAndTransactionPropertiesFiller.json
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
    [
        "tests/static/state_tests/stSolidityTest/TestBlockAndTransactionPropertiesFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_test_block_and_transaction_properties(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xA2333EEF5630066B928DEA5FD85A239F511B5B067D1441EE7AC290D0122B917B
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    pre[sender] = Account(balance=0x5F5E100)
    # Source: raw bytecode
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x40, value=0x60)
            + Op.CALLDATALOAD(offset=0x0)
            + Op.PUSH29[
                0x100000000000000000000000000000000000000000000000000000000
            ]
            + Op.SWAP1
            + Op.DIV
            + Op.JUMPI(pc=Op.PUSH2[0x44], condition=Op.EQ(0xC0406226, Op.DUP1))
            + Op.JUMPI(pc=Op.PUSH2[0x69], condition=Op.EQ(0xE97384DC, Op.DUP1))
            + Op.JUMP(pc=Op.PUSH2[0x42])
            + Op.JUMPDEST
            + Op.STOP
            + Op.JUMPDEST
            + Op.PUSH2[0x51]
            + Op.PUSH1[0x4]
            + Op.POP(Op.DUP1)
            + Op.POP
            + Op.JUMP(pc=Op.PUSH2[0x8E])
            + Op.JUMPDEST
            + Op.MLOAD(offset=0x40)
            + Op.DUP1
            + Op.MSTORE(offset=Op.DUP2, value=Op.ISZERO(Op.ISZERO(Op.DUP3)))
            + Op.PUSH1[0x20]
            + Op.ADD
            + Op.SWAP2
            + Op.POP
            + Op.POP
            + Op.MLOAD(offset=0x40)
            + Op.DUP1
            + Op.SWAP2
            + Op.SUB
            + Op.SWAP1
            + Op.RETURN
            + Op.JUMPDEST
            + Op.PUSH2[0x76]
            + Op.PUSH1[0x4]
            + Op.POP(Op.DUP1)
            + Op.POP
            + Op.JUMP(pc=Op.PUSH2[0xC9])
            + Op.JUMPDEST
            + Op.MLOAD(offset=0x40)
            + Op.DUP1
            + Op.MSTORE(offset=Op.DUP2, value=Op.ISZERO(Op.ISZERO(Op.DUP3)))
            + Op.PUSH1[0x20]
            + Op.ADD
            + Op.SWAP2
            + Op.POP
            + Op.POP
            + Op.MLOAD(offset=0x40)
            + Op.DUP1
            + Op.SWAP2
            + Op.SUB
            + Op.SWAP1
            + Op.RETURN
            + Op.JUMPDEST
            + Op.PUSH1[0x0]
            + Op.PUSH2[0x98]
            + Op.JUMP(pc=Op.PUSH2[0xC9])
            + Op.JUMPDEST
            + Op.PUSH1[0x0]
            + Op.EXP(0x100, 0x0)
            + Op.AND(Op.NOT(Op.MUL(0xFF, Op.DUP2)), Op.SLOAD(key=Op.DUP2))
            + Op.SWAP1
            + Op.OR(Op.MUL, Op.DUP4)
            + Op.SWAP1
            + Op.SSTORE
            + Op.POP
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.SLOAD
            + Op.SWAP1
            + Op.PUSH2[0x100]
            + Op.EXP
            + Op.SWAP1
            + Op.AND(0xFF, Op.DIV)
            + Op.SWAP1
            + Op.POP
            + Op.JUMP(pc=Op.PUSH2[0xC6])
            + Op.JUMPDEST
            + Op.SWAP1
            + Op.JUMP
            + Op.JUMPDEST
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x1]
            + Op.SWAP1
            + Op.POP
            + Op.POP(Op.DUP1)
            + Op.JUMPI(
                pc=0x10D,
                condition=Op.ISZERO(
                    Op.ISZERO(
                        Op.EQ(
                            Op.AND(
                                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
                                Op.COINBASE,
                            ),
                            0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA,
                        ),
                    ),
                ),
            )
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.POP
            + Op.JUMP(pc=0x1F7)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x123,
                condition=Op.ISZERO(
                    Op.ISZERO(Op.EQ(Op.PREVRANDAO, 0x2B8FEB0))
                ),
            )
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.POP
            + Op.JUMP(pc=0x1F7)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x13D,
                condition=Op.ISZERO(
                    Op.ISZERO(Op.EQ(Op.GASLIMIT, 0x7FFFFFFFFFFFFFFF)),
                ),
            )
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.POP
            + Op.JUMP(pc=0x1F7)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x150,
                condition=Op.ISZERO(Op.ISZERO(Op.EQ(Op.NUMBER, 0x78))),
            )
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.POP
            + Op.JUMP(pc=0x1F7)
            + Op.JUMPDEST
            + Op.POP(Op.BLOCKHASH(block_number=0x78))
            + Op.POP(Op.TIMESTAMP)
            + Op.POP(Op.GAS)
            + Op.JUMPI(
                pc=0x194,
                condition=Op.ISZERO(
                    Op.ISZERO(
                        Op.EQ(
                            Op.AND(
                                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
                                Op.CALLER,
                            ),
                            0x7F3F285918D9B5E764174551E10B7539B97BBB27,
                        ),
                    ),
                ),
            )
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.POP
            + Op.JUMP(pc=0x1F7)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x1A7,
                condition=Op.ISZERO(Op.ISZERO(Op.EQ(Op.CALLVALUE, 0x64))),
            )
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.POP
            + Op.JUMP(pc=0x1F7)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x1BA,
                condition=Op.ISZERO(Op.ISZERO(Op.EQ(Op.GASPRICE, 0x1))),
            )
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.POP
            + Op.JUMP(pc=0x1F7)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x1F6,
                condition=Op.ISZERO(
                    Op.ISZERO(
                        Op.EQ(
                            Op.AND(
                                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
                                Op.ORIGIN,
                            ),
                            0x7F3F285918D9B5E764174551E10B7539B97BBB27,
                        ),
                    ),
                ),
            )
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.POP
            + Op.JUMP(pc=0x1F7)
            + Op.JUMPDEST
            + Op.JUMPDEST
            + Op.SWAP1
            + Op.JUMP
        ),
        balance=0x186A0,
        nonce=0,
        address=Address("0xad24d212286ab785efe98ab6f5a3ecde73054ee5"),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex("c0406226"),
        gas_limit=350000,
        value=100,
    )

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
