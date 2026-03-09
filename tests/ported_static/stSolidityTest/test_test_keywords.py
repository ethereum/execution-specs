"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stSolidityTest/TestKeywordsFiller.json
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
    ["tests/static/state_tests/stSolidityTest/TestKeywordsFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_test_keywords(
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
        gas_limit=100000000,
    )

    pre[sender] = Account(balance=0x5F5E100)
    # Source: raw bytecode
    contract = pre.deploy_contract(
        code=(
            Op.DIV(
                Op.CALLDATALOAD(offset=0x0),
                0x100000000000000000000000000000000000000000000000000000000,
            )
            + Op.JUMPI(pc=0x37, condition=Op.EQ(Op.DUP2, 0x380E4396))
            + Op.JUMPI(pc=0x47, condition=Op.EQ(0xC0406226, Op.DUP1))
            + Op.STOP
            + Op.JUMPDEST
            + Op.PUSH1[0x3D]
            + Op.JUMP(pc=0x84)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x0, value=Op.DUP1)
            + Op.RETURN(offset=0x0, size=0x20)
            + Op.JUMPDEST
            + Op.PUSH1[0x4D]
            + Op.JUMP(pc=0x57)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x0, value=Op.DUP1)
            + Op.RETURN(offset=0x0, size=0x20)
            + Op.JUMPDEST
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x5F]
            + Op.JUMP(pc=0x84)
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
            + Op.JUMPDEST
            + Op.PUSH1[0x0]
            + Op.DUP1
            + Op.DUP2
            + Op.JUMPI(pc=0xCD, condition=Op.ISZERO(0x1))
            + Op.JUMPDEST
            + Op.JUMPI(pc=0xA1, condition=Op.ISZERO(Op.SLT(Op.DUP3, 0xA)))
            + Op.PUSH1[0x1]
            + Op.SWAP1
            + Op.SWAP2
            + Op.ADD
            + Op.SWAP1
            + Op.JUMP(pc=0x8F)
            + Op.JUMPDEST
            + Op.JUMPI(pc=0xAC, condition=Op.EQ(0xA, Op.DUP2))
            + Op.JUMP(pc=0xC9)
            + Op.JUMPDEST
            + Op.POP
            + Op.PUSH1[0xA]
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0xC8,
                condition=Op.ISZERO(Op.GT(Op.AND(0xFF, Op.DUP2), 0x0)),
            )
            + Op.PUSH1[0x1]
            + Op.SWAP2
            + Op.DUP3
            + Op.SWAP1
            + Op.SUB
            + Op.SWAP2
            + Op.SWAP1
            + Op.SUB
            + Op.JUMP(pc=0xB0)
            + Op.JUMPDEST
            + Op.JUMPDEST
            + Op.JUMP(pc=0xD5)
            + Op.JUMPDEST
            + Op.PUSH1[0x0]
            + Op.SWAP3
            + Op.POP
            + Op.JUMP(pc=0xED)
            + Op.JUMPDEST
            + Op.JUMPI(pc=0xE0, condition=Op.EQ(0x0, Op.DUP2))
            + Op.JUMP(pc=0xE8)
            + Op.JUMPDEST
            + Op.PUSH1[0x1]
            + Op.SWAP3
            + Op.POP
            + Op.JUMP(pc=0xED)
            + Op.JUMPDEST
            + Op.PUSH1[0x0]
            + Op.SWAP3
            + Op.POP
            + Op.JUMPDEST
            + Op.POP
            + Op.POP
            + Op.SWAP1
            + Op.JUMP
        ),
        balance=0x186A0,
        nonce=0,
        address=Address("0xe7dcb339943a6db535ffe618ec32d1e4e5a50f37"),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex("c0406226"),
        gas_limit=350000,
        value=1,
    )

    post = {
        contract: Account(storage={0: 1}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
