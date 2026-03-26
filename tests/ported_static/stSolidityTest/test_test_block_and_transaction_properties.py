"""
test_test_block_and_transaction_properties

Ported from:
state_tests/stSolidityTest/TestBlockAndTransactionPropertiesFiller.json
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
    ["state_tests/stSolidityTest/TestBlockAndTransactionPropertiesFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_test_block_and_transaction_properties(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_test_block_and_transaction_properties"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xa2333eef5630066b928dea5fd85a239f511b5b067d1441ee7ac290d0122b917b
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
    # 0x60606040526000357c010000000000000000000000000000000000000000000000000000000090048063c040622614610044578063e97384dc1461006957610042565b005b610051600480505061008e565b60405180821515815260200191505060405180910390f35b61007660048050506100c9565b60405180821515815260200191505060405180910390f35b60006100986100c9565b600060006101000a81548160ff02191690830217905550600060009054906101000a900460ff1690506100c6565b90565b6000600190508050732adc25665018aa1fe0e6bc666dac8fc2697ff9ba4173ffffffffffffffffffffffffffffffffffffffff1614151561010d57600090506101f7565b6302b8feb04414151561012357600090506101f7565b677fffffffffffffff4514151561013d57600090506101f7565b60784314151561015057600090506101f7565b6078405042505a5073<eoa:sender:0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b>3373ffffffffffffffffffffffffffffffffffffffff1614151561019457600090506101f7565b6064341415156101a757600090506101f7565b60013a1415156101ba57600090506101f7565b73<eoa:sender:0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b>3273ffffffffffffffffffffffffffffffffffffffff161415156101f657600090506101f7565b5b9056
    target = pre.deploy_contract(
        code=Op.MSTORE(offset=0x40, value=0x60) + Op.CALLDATALOAD(offset=0x0)
        + Op.PUSH29[0x100000000000000000000000000000000000000000000000000000000]
        + Op.SWAP1 + Op.DIV
        + Op.JUMPI(pc=Op.PUSH2[0x44], condition=Op.EQ(0xc0406226, Op.DUP1))
        + Op.JUMPI(pc=Op.PUSH2[0x69], condition=Op.EQ(0xe97384dc, Op.DUP1))
        + Op.JUMP(pc=Op.PUSH2[0x42]) + Op.JUMPDEST + Op.STOP + Op.JUMPDEST
        + Op.PUSH2[0x51] + Op.PUSH1[0x4] + Op.POP(Op.DUP1) + Op.POP
        + Op.JUMP(pc=Op.PUSH2[0x8e]) + Op.JUMPDEST + Op.MLOAD(offset=0x40)
        + Op.DUP1
        + Op.MSTORE(offset=Op.DUP2, value=Op.ISZERO(Op.ISZERO(Op.DUP3)))
        + Op.PUSH1[0x20] + Op.ADD + Op.SWAP2 + Op.POP * 2 + Op.MLOAD(offset=0x40)
        + Op.DUP1 + Op.SWAP2 + Op.SUB + Op.SWAP1 + Op.RETURN + Op.JUMPDEST
        + Op.PUSH2[0x76] + Op.PUSH1[0x4] + Op.POP(Op.DUP1) + Op.POP
        + Op.JUMP(pc=Op.PUSH2[0xc9]) + Op.JUMPDEST + Op.MLOAD(offset=0x40)
        + Op.DUP1
        + Op.MSTORE(offset=Op.DUP2, value=Op.ISZERO(Op.ISZERO(Op.DUP3)))
        + Op.PUSH1[0x20] + Op.ADD + Op.SWAP2 + Op.POP * 2 + Op.MLOAD(offset=0x40)
        + Op.DUP1 + Op.SWAP2 + Op.SUB + Op.SWAP1 + Op.RETURN + Op.JUMPDEST
        + Op.PUSH1[0x0] + Op.PUSH2[0x98] + Op.JUMP(pc=Op.PUSH2[0xc9])
        + Op.JUMPDEST + Op.PUSH1[0x0] + Op.EXP(0x100, 0x0)
        + Op.AND(Op.NOT(Op.MUL(0xff, Op.DUP2)), Op.SLOAD(key=Op.DUP2)) + Op.SWAP1  # noqa: E501
        + Op.OR(Op.MUL, Op.DUP4) + Op.SWAP1 + Op.SSTORE + Op.POP
        + Op.PUSH1[0x0] * 2 + Op.SWAP1 + Op.SLOAD + Op.SWAP1 + Op.PUSH2[0x100]
        + Op.EXP + Op.SWAP1 + Op.AND(0xff, Op.DIV) + Op.SWAP1 + Op.POP
        + Op.JUMP(pc=Op.PUSH2[0xc6]) + Op.JUMPDEST + Op.SWAP1 + Op.JUMP
        + Op.JUMPDEST + Op.PUSH1[0x0] + Op.PUSH1[0x1] + Op.SWAP1 + Op.POP
        + Op.POP(Op.DUP1)
        + Op.JUMPI(pc=0x10d, condition=Op.ISZERO(Op.ISZERO(Op.EQ(Op.AND(0xffffffffffffffffffffffffffffffffffffffff, Op.COINBASE), 0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba))))
        + Op.PUSH1[0x0] + Op.SWAP1 + Op.POP + Op.JUMP(pc=0x1f7) + Op.JUMPDEST
        + Op.JUMPI(pc=0x123, condition=Op.ISZERO(Op.ISZERO(Op.EQ(Op.PREVRANDAO, 0x2b8feb0))))
        + Op.PUSH1[0x0] + Op.SWAP1 + Op.POP + Op.JUMP(pc=0x1f7) + Op.JUMPDEST
        + Op.JUMPI(pc=0x13d, condition=Op.ISZERO(Op.ISZERO(Op.EQ(Op.GASLIMIT, 0x7fffffffffffffff))))
        + Op.PUSH1[0x0] + Op.SWAP1 + Op.POP + Op.JUMP(pc=0x1f7) + Op.JUMPDEST
        + Op.JUMPI(pc=0x150, condition=Op.ISZERO(Op.ISZERO(Op.EQ(Op.NUMBER, 0x78))))
        + Op.PUSH1[0x0] + Op.SWAP1 + Op.POP + Op.JUMP(pc=0x1f7) + Op.JUMPDEST
        + Op.POP(Op.BLOCKHASH(block_number=0x78)) + Op.POP(Op.TIMESTAMP)
        + Op.POP(Op.GAS)
        + Op.JUMPI(pc=0x194, condition=Op.ISZERO(Op.ISZERO(Op.EQ(Op.AND(0xffffffffffffffffffffffffffffffffffffffff, Op.CALLER), 0x7f3f285918d9b5e764174551e10b7539b97bbb27))))
        + Op.PUSH1[0x0] + Op.SWAP1 + Op.POP + Op.JUMP(pc=0x1f7) + Op.JUMPDEST
        + Op.JUMPI(pc=0x1a7, condition=Op.ISZERO(Op.ISZERO(Op.EQ(Op.CALLVALUE, 0x64))))
        + Op.PUSH1[0x0] + Op.SWAP1 + Op.POP + Op.JUMP(pc=0x1f7) + Op.JUMPDEST
        + Op.JUMPI(pc=0x1ba, condition=Op.ISZERO(Op.ISZERO(Op.EQ(Op.GASPRICE, 0x1))))
        + Op.PUSH1[0x0] + Op.SWAP1 + Op.POP + Op.JUMP(pc=0x1f7) + Op.JUMPDEST
        + Op.JUMPI(pc=0x1f6, condition=Op.ISZERO(Op.ISZERO(Op.EQ(Op.AND(0xffffffffffffffffffffffffffffffffffffffff, Op.ORIGIN), 0x7f3f285918d9b5e764174551e10b7539b97bbb27))))
        + Op.PUSH1[0x0] + Op.SWAP1 + Op.POP + Op.JUMP(pc=0x1f7) + Op.JUMPDEST * 2
        + Op.SWAP1 + Op.JUMP,
        balance=0x186a0,
        nonce=0,
        address=Address("0xad24d212286ab785efe98ab6f5a3ecde73054ee5"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x5f5e100)


    tx = Transaction(
        sender=sender,
        to=target,
        data=bytes.fromhex("c0406226"),
        gas_limit=350000,
        value=100,
        nonce=0,
        gas_price=10,
    )

    post = {target: Account(storage={0: 0})}

    state_test(env=env, pre=pre, post=post, tx=tx)
