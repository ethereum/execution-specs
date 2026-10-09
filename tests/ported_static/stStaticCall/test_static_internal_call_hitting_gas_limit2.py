"""
Test_static_internal_call_hitting_gas_limit2.

Ported from:
state_tests/stStaticCall/static_InternalCallHittingGasLimit2Filler.json

@manually-enhanced: Do not overwrite.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytes,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stStaticCall/static_InternalCallHittingGasLimit2Filler.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.slow
def test_static_internal_call_hitting_gas_limit2(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_static_internal_call_hitting_gas_limit2."""
    sender = pre.fund_eoa(amount=0xF4240)

    # Source: lll
    # { (def 'i 0x80) (for {} (< @i 50000) [i](+ @i 1) (EXTCODESIZE 1)) }
    addr = pre.deploy_contract(
        code=Op.JUMPDEST
        + Op.JUMPI(
            pc=0x1C, condition=Op.ISZERO(Op.LT(Op.MLOAD(offset=0x80), 0xC350))
        )
        + Op.POP(Op.EXTCODESIZE(address=0x1))
        + Op.MSTORE(offset=0x80, value=Op.ADD(Op.MLOAD(offset=0x80), 0x1))
        + Op.JUMP(pc=0x0)
        + Op.JUMPDEST
        + Op.STOP,
    )
    # Source: lll
    # { [[ 1 ]] (STATICCALL 25000 <contract:0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0) }  # noqa: E501
    target = pre.deploy_contract(
        code=Op.SSTORE(
            key=0x1,
            value=Op.STATICCALL(
                gas=0x61A8,
                address=addr,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.STOP,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=47766,
        value=10,
    )

    post = {target: Account(storage={1: 0})}

    state_test(pre=pre, post=post, tx=tx)
