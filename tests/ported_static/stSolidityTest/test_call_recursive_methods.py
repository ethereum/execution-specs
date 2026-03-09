"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stSolidityTest/CallRecursiveMethodsFiller.json
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
        "tests/static/state_tests/stSolidityTest/CallRecursiveMethodsFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_call_recursive_methods(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0xeb201d2887816e041f6e807e804f64f3a7a226fe")
    sender = EOA(
        key=0xA9AE12CB2700C0214F86B9796881BC03A1FD5605D0E76D2DA2CA592E62D53E52
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[sender] = Account(balance=0x12A05F200)
    # Source: raw bytecode
    contract = pre.deploy_contract(
        code=(
            Op.DIV(
                Op.CALLDATALOAD(offset=0x0),
                0x100000000000000000000000000000000000000000000000000000000,
            )
            + Op.JUMPI(pc=0x41, condition=Op.EQ(Op.DUP2, 0x296DF0DF))
            + Op.JUMPI(pc=0x4D, condition=Op.EQ(0x4893D88A, Op.DUP1))
            + Op.JUMPI(pc=0x59, condition=Op.EQ(0x981A3165, Op.DUP1))
            + Op.STOP
            + Op.JUMPDEST
            + Op.PUSH1[0x47]
            + Op.JUMP(pc=0x65)
            + Op.JUMPDEST
            + Op.RETURN(offset=0x0, size=0x0)
            + Op.JUMPDEST
            + Op.PUSH1[0x53]
            + Op.JUMP(pc=0x7A)
            + Op.JUMPDEST
            + Op.RETURN(offset=0x0, size=0x0)
            + Op.JUMPDEST
            + Op.PUSH1[0x5F]
            + Op.JUMP(pc=0x72)
            + Op.JUMPDEST
            + Op.RETURN(offset=0x0, size=0x0)
            + Op.JUMPDEST
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x70, condition=Op.ISZERO(0x1))
            + Op.JUMP(pc=0x66)
            + Op.JUMPDEST
            + Op.JUMP
            + Op.JUMPDEST
            + Op.PUSH1[0x78]
            + Op.JUMP(pc=0x7A)
            + Op.JUMPDEST
            + Op.JUMP
            + Op.JUMPDEST
            + Op.PUSH1[0x80]
            + Op.JUMP(pc=0x72)
            + Op.JUMPDEST
            + Op.JUMP
        ),
        balance=0x186A0,
        nonce=0,
        address=Address("0xc7c7851c7f3291bed1039bb4ffa166c290a605a9"),  # noqa: E501
    )
    pre[coinbase] = Account(balance=0, nonce=1)

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex("981a3165"),
        gas_limit=60000,
        value=1,
    )

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
