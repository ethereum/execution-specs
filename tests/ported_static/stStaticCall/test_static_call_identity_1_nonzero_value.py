"""
Test_static_call_identity_1_nonzero_value.

Ported from:
state_tests/stStaticCall/static_CallIdentity_1_nonzeroValueFiller.json
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
    ["state_tests/stStaticCall/static_CallIdentity_1_nonzeroValueFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.slow
@pytest.mark.pre_alloc_mutable
def test_static_call_identity_1_nonzero_value(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_static_call_identity_1_nonzero_value."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0xE04D1AC7DDDA0C98397D56A0B501E960D4CD325A39286919AC23C1A07009A869
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    # Source: lll
    # { [[ 2 ]] (STATICCALL 200000 4 0 0 0 32) (CALL 50000 4 0x13 0 0 0 0) [[ 0 ]] (MLOAD 0)}  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x2,
            value=Op.STATICCALL(
                gas=0x30D40,
                address=0x4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x20,
            ),
        )
        + Op.POP(
            Op.CALL(
                gas=0xC350,
                address=0x4,
                value=0x13,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
        + Op.STOP,
        balance=0xBEBC200,
        nonce=0,
        address=Address(0x07F023A2418EB0DC955C465D7E5EF48189F005BE),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=365224,
        value=0x186A0,
    )

    post = {
        Address(0x0000000000000000000000000000000000000004): Account(
            balance=19
        ),
        target: Account(storage={0: 0, 2: 1}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
