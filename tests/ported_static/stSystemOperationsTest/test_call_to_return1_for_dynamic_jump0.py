"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stSystemOperationsTest
CallToReturn1ForDynamicJump0Filler.json
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
        "tests/static/state_tests/stSystemOperationsTest/CallToReturn1ForDynamicJump0Filler.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_call_to_return1_for_dynamic_jump0(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xE04D1AC7DDDA0C98397D56A0B501E960D4CD325A39286919AC23C1A07009A869
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x1, value=0x1)
            + Op.MSTORE8(offset=0x1F, value=0x2A)
            + Op.RETURN(offset=0x1F, size=0x1)
        ),
        balance=23,
        nonce=0,
        address=Address("0x64963d42a3dff7bf49ce946e12f6c9034c746888"),  # noqa: E501
    )
    # Source: raw bytecode
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.CALL(
                    gas=0x3E8,
                    address=0x64963D42A3DFF7BF49CE946E12F6C9034C746888,
                    value=0x17,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x1F,
                    ret_size=0x1,
                ),
            )
            + Op.JUMP(pc=Op.MLOAD(offset=0x0))
            + Op.JUMPDEST
            + Op.SSTORE(key=0x23, value=0x23)
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x6d968bcf609007ec874b2ac0216c27e131c3be4c"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=300000,
        value=100000,
    )

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
