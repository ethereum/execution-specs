"""
test_delegatecall1024_oog

Ported from:
state_tests/stDelegatecallTestHomestead/Delegatecall1024OOGFiller.json
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
    ["state_tests/stDelegatecallTestHomestead/Delegatecall1024OOGFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_delegatecall1024_oog(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_delegatecall1024_oog"""
    coinbase = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    addr_0xaaaf5374fce5edbc8e2a8697c15331677e6ebf0b = Address("0xd9b97c712ebce43f3c19179bbef44b550f9e8bc0")  # noqa: E501
    sender = EOA(
        key=0xe7c72b378297589acee4e0ba3272841bcfc5e220f86de253f890274cfee9e474
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

    pre[sender] = Account(balance=0xffffffffffffffffffffffffffffffff)
    pre[addr_0xaaaf5374fce5edbc8e2a8697c15331677e6ebf0b] = Account(balance=7000)
    # Source: lll
    # { [[ 0 ]] (ADD @@0 1) [[ 1 ]] (DELEGATECALL (MUL (SUB (GAS) 10000) (SUB 1 (DIV @@0 1025))) <contract:target:0xbbbf5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0) [[ 2 ]] (ADD 1(MUL @@0 1000)) }
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.ADD(Op.SLOAD(key=0x0), 0x1))
        + Op.SSTORE(key=0x1, value=Op.DELEGATECALL(gas=Op.MUL(Op.SUB(Op.GAS, 0x2710), Op.SUB(0x1, Op.DIV(Op.SLOAD(key=0x0), 0x401))), address=0x62c5c9278da01e6594d6fede061838cf5e597f2b, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0x2, value=Op.ADD(0x1, Op.MUL(Op.SLOAD(key=0x0), 0x3e8)))  # noqa: E501
        + Op.STOP,
        balance=1024,
        nonce=0,
        address=Address("0x62c5c9278da01e6594d6fede061838cf5e597f2b"),  # noqa: E501
    )


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=15720826,
        value=10,
        nonce=0,
        gas_price=10,
    )

    post = {target: Account(storage={0: 146, 1: 1, 2: 0x23a51})}

    state_test(env=env, pre=pre, post=post, tx=tx)
