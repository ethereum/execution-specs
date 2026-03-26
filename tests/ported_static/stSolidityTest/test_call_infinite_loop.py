"""
test_call_infinite_loop

Ported from:
state_tests/stSolidityTest/CallInfiniteLoopFiller.json
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
    ["state_tests/stSolidityTest/CallInfiniteLoopFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_call_infinite_loop(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_call_infinite_loop"""
    coinbase = Address("0xeb201d2887816e041f6e807e804f64f3a7a226fe")
    sender = EOA(
        key=0x96c07046493ec8728482079ab999d2994420d9cf4d3491dfd06871b106d9d87b
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

    pre[coinbase] = Account(balance=0, nonce=1)
    # Source: raw
    # 0x60003560e060020a90048063296df0df1460295780634893d88a146035578063981a316514604157005b602f604d565b60006000f35b603b6062565b60006000f35b6047605a565b60006000f35b5b600115605857604e565b565b60606062565b565b6068605a565b56
    target = pre.deploy_contract(
        code=Op.CALLDATALOAD(offset=0x0) + Op.EXP(0x2, 0xe0) + Op.SWAP1 + Op.DIV
        + Op.JUMPI(pc=0x29, condition=Op.EQ(0x296df0df, Op.DUP1))
        + Op.JUMPI(pc=0x35, condition=Op.EQ(0x4893d88a, Op.DUP1))
        + Op.JUMPI(pc=0x41, condition=Op.EQ(0x981a3165, Op.DUP1)) + Op.STOP
        + Op.JUMPDEST + Op.PUSH1[0x2f] + Op.JUMP(pc=0x4d) + Op.JUMPDEST
        + Op.RETURN(offset=0x0, size=0x0) + Op.JUMPDEST + Op.PUSH1[0x3b]
        + Op.JUMP(pc=0x62) + Op.JUMPDEST + Op.RETURN(offset=0x0, size=0x0)
        + Op.JUMPDEST + Op.PUSH1[0x47] + Op.JUMP(pc=0x5a) + Op.JUMPDEST
        + Op.RETURN(offset=0x0, size=0x0) + Op.JUMPDEST * 2
        + Op.JUMPI(pc=0x58, condition=Op.ISZERO(0x1)) + Op.JUMP(pc=0x4e)
        + Op.JUMPDEST + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x60] + Op.JUMP(pc=0x62)
        + Op.JUMPDEST + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x68] + Op.JUMP(pc=0x5a)
        + Op.JUMPDEST + Op.JUMP,
        balance=0x186a0,
        nonce=0,
        address=Address("0xf9b9ccb6160ce3574df5d096ca9fd12ba81d97ee"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x1dcd6500)


    tx = Transaction(
        sender=sender,
        to=target,
        data=bytes.fromhex("296df0df"),
        gas_limit=300000,
        value=1,
        nonce=0,
        gas_price=10,
    )

    post = {sender: Account(nonce=1)}

    state_test(env=env, pre=pre, post=post, tx=tx)
