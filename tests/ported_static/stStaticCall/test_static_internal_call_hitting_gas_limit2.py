"""
Test_static_internal_call_hitting_gas_limit2.

Ported from:
state_tests/stStaticCall/static_InternalCallHittingGasLimit2Filler.json
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
    [
        "state_tests/stStaticCall/static_InternalCallHittingGasLimit2Filler.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.slow
@pytest.mark.pre_alloc_mutable
def test_static_internal_call_hitting_gas_limit2(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_static_internal_call_hitting_gas_limit2."""
    coinbase = Address(0x2ADF5374FCE5EDBC8E2A8697C15331677E6EBF0B)
    sender = EOA(
        key=0x7C857D62C76CE09F2E8EC3FA9277578C67B69C6547364568FDDB841071E5BD7
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=47766,
    )

    pre[sender] = Account(balance=0xF4240)
    # Source: lll
    # { [[ 1 ]] (STATICCALL 25000 <contract:0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x1,
            value=Op.STATICCALL(
                gas=0x61A8,
                address=0x285BB5C8A71646AB9A5796D4A718CC4826AF8D06,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.STOP,
        nonce=0,
        address=Address(0xF0801B78978104BAE7D7D679F8E3990492825C3E),  # noqa: E501
    )
    # Source: lll
    # { (def 'i 0x80) (for {} (< @i 50000) [i](+ @i 1) (EXTCODESIZE 1)) }
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.JUMPDEST
        + Op.JUMPI(
            pc=0x1C, condition=Op.ISZERO(Op.LT(Op.MLOAD(offset=0x80), 0xC350))
        )
        + Op.POP(Op.EXTCODESIZE(address=0x1))
        + Op.MSTORE(offset=0x80, value=Op.ADD(Op.MLOAD(offset=0x80), 0x1))
        + Op.JUMP(pc=0x0)
        + Op.JUMPDEST
        + Op.STOP,
        nonce=0,
        address=Address(0x285BB5C8A71646AB9A5796D4A718CC4826AF8D06),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=47766,
        value=10,
    )

    post = {target: Account(storage={1: 0})}

    state_test(env=env, pre=pre, post=post, tx=tx)
