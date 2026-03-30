"""
Test_call_infinite_loop.

Ported from:
state_tests/stSolidityTest/CallInfiniteLoopFiller.json
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
    ["state_tests/stSolidityTest/CallInfiniteLoopFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_call_infinite_loop(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_call_infinite_loop."""
    coinbase = Address(0xEB201D2887816E041F6E807E804F64F3A7A226FE)
    sender = EOA(
        key=0x96C07046493EC8728482079AB999D2994420D9CF4D3491DFD06871B106D9D87B
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[coinbase] = Account(balance=0, nonce=1)
    # Source: raw
    # 0x60003560e060020a90048063296df0df1460295780634893d88a146035578063981a316514604157005b602f604d565b60006000f35b603b6062565b60006000f35b6047605a565b60006000f35b5b600115605857604e565b565b60606062565b565b6068605a565b56  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.CALLDATALOAD(offset=0x0)
        + Op.EXP(0x2, 0xE0)
        + Op.SWAP1
        + Op.DIV
        + Op.JUMPI(pc=0x29, condition=Op.EQ(0x296DF0DF, Op.DUP1))
        + Op.JUMPI(pc=0x35, condition=Op.EQ(0x4893D88A, Op.DUP1))
        + Op.JUMPI(pc=0x41, condition=Op.EQ(0x981A3165, Op.DUP1))
        + Op.STOP
        + Op.JUMPDEST
        + Op.PUSH1[0x2F]
        + Op.JUMP(pc=0x4D)
        + Op.JUMPDEST
        + Op.RETURN(offset=0x0, size=0x0)
        + Op.JUMPDEST
        + Op.PUSH1[0x3B]
        + Op.JUMP(pc=0x62)
        + Op.JUMPDEST
        + Op.RETURN(offset=0x0, size=0x0)
        + Op.JUMPDEST
        + Op.PUSH1[0x47]
        + Op.JUMP(pc=0x5A)
        + Op.JUMPDEST
        + Op.RETURN(offset=0x0, size=0x0)
        + Op.JUMPDEST * 2
        + Op.JUMPI(pc=0x58, condition=Op.ISZERO(0x1))
        + Op.JUMP(pc=0x4E)
        + Op.JUMPDEST
        + Op.JUMP
        + Op.JUMPDEST
        + Op.PUSH1[0x60]
        + Op.JUMP(pc=0x62)
        + Op.JUMPDEST
        + Op.JUMP
        + Op.JUMPDEST
        + Op.PUSH1[0x68]
        + Op.JUMP(pc=0x5A)
        + Op.JUMPDEST
        + Op.JUMP,
        balance=0x186A0,
        nonce=0,
        address=Address(0xF9B9CCB6160CE3574DF5D096CA9FD12BA81D97EE),  # noqa: E501
    )
    pre[sender] = Account(balance=0x1DCD6500)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes("296df0df"),
        gas_limit=300000,
        value=1,
    )

    post = {sender: Account(nonce=1)}

    state_test(env=env, pre=pre, post=post, tx=tx)
