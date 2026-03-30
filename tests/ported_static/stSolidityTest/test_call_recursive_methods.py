"""
Test_call_recursive_methods.

Ported from:
state_tests/stSolidityTest/CallRecursiveMethodsFiller.json
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
    ["state_tests/stSolidityTest/CallRecursiveMethodsFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_call_recursive_methods(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_call_recursive_methods."""
    coinbase = Address(0xEB201D2887816E041F6E807E804F64F3A7A226FE)
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

    pre[coinbase] = Account(balance=0, nonce=1)
    # Source: raw
    # 0x7c01000000000000000000000000000000000000000000000000000000006000350463296df0df811460415780634893d88a14604d578063981a316514605957005b60476065565b60006000f35b6053607a565b60006000f35b605f6072565b60006000f35b5b6001156070576066565b565b6078607a565b565b60806072565b56  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.DIV(
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
        + Op.JUMPDEST * 2
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
        + Op.JUMP,
        balance=0x186A0,
        nonce=0,
        address=Address(0xC7C7851C7F3291BED1039BB4FFA166C290A605A9),  # noqa: E501
    )
    pre[sender] = Account(balance=0x12A05F200)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes("981a3165"),
        gas_limit=60000,
        value=1,
    )

    post = {sender: Account(nonce=1)}

    state_test(env=env, pre=pre, post=post, tx=tx)
