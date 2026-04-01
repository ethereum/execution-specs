"""
Recursive call.

Ported from:
state_tests/stCallCreateCallCodeTest/CallLoseGasOOGFiller.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    Fork,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Amsterdam
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stCallCreateCallCodeTest/CallLoseGasOOGFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_call_lose_gas_oog(
    state_test: StateTestFiller,
    fork: Fork,
    pre: Alloc,
) -> None:
    """Recursive call."""
    coinbase = Address(0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B)
    addr = Address(0xD9B97C712EBCE43F3C19179BBEF44B550F9E8BC0)
    sender = EOA(
        key=0xE7C72B378297589ACEE4E0BA3272841BCFC5E220F86DE253F890274CFEE9E474
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    pre[sender] = Account(balance=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
    pre[addr] = Account(balance=7000)
    # Source: lll
    # { [[ 0 ]] (ADD @@0 1) [[ 1 ]] (CALL (ADD 1(MUL @@0 100000)) <contract:target:0xbbbf5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0 0) [[ 2 ]] (ADD 1(MUL @@0 1000)) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=Op.ADD(Op.SLOAD(key=0x0), 0x1))
        + Op.SSTORE(
            key=0x1,
            value=Op.CALL(
                gas=Op.ADD(0x1, Op.MUL(Op.SLOAD(key=0x0), 0x186A0)),
                address=0x180F2D7E0C9A56B7BB287E2F50101660110B641F,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(
            key=0x2, value=Op.ADD(0x1, Op.MUL(Op.SLOAD(key=0x0), 0x3E8))
        )
        + Op.STOP,
        balance=1024,
        nonce=0,
        address=Address(0x180F2D7E0C9A56B7BB287E2F50101660110B641F),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=2200000 if fork >= Amsterdam else 200000,
        value=10,
    )

    post = {target: Account(storage={0: 1, 2: 1001})}

    state_test(env=env, pre=pre, post=post, tx=tx)
