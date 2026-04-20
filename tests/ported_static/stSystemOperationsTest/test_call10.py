"""
Test_call10.

Ported from:
state_tests/stSystemOperationsTest/Call10Filler.json
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
    ["state_tests/stSystemOperationsTest/Call10Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_call10(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_call10."""
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
    )

    pre[sender] = Account(balance=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
    pre[addr] = Account(balance=7000)
    # Source: lll
    # { (def 'i 0x80) (for {} (< @i 10) [i](+ @i 1) [[ 0 ]](CALL 0xfffffffffff <eoa:0xaaaf5374fce5edbc8e2a8697c15331677e6ebf0b> 1 0 50000 0 0) ) [[ 1 ]] @i}  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.JUMPDEST
        + Op.JUMPI(
            pc=0x42, condition=Op.ISZERO(Op.LT(Op.MLOAD(offset=0x80), 0xA))
        )
        + Op.SSTORE(
            key=0x0,
            value=Op.CALL(
                gas=0xFFFFFFFFFFF,
                address=0xD9B97C712EBCE43F3C19179BBEF44B550F9E8BC0,
                value=0x1,
                args_offset=0x0,
                args_size=0xC350,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.MSTORE(offset=0x80, value=Op.ADD(Op.MLOAD(offset=0x80), 0x1))
        + Op.JUMP(pc=0x0)
        + Op.JUMPDEST
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x80))
        + Op.STOP,
        balance=1000,
        nonce=0,
        address=Address(0xFDA03FA18CBDA0970E18071F363BEA4C9C90DFB6),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=200000,
        value=10,
    )

    post = {target: Account(storage={0: 1, 1: 10})}

    state_test(env=env, pre=pre, post=post, tx=tx)
