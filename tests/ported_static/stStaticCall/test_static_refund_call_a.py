"""
Test_static_refund_call_a.

Ported from:
state_tests/stStaticCall/static_refund_CallAFiller.json
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
    ["state_tests/stStaticCall/static_refund_CallAFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.slow
@pytest.mark.pre_alloc_mutable
def test_static_refund_call_a(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_static_refund_call_a."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0xD28CE7E8C6CA72F9B2DD5AA5C41F48198119E86E443C50DE70F3FBA602247FE8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    # Source: lll
    # { [[ 0 ]] (STATICCALL 5500 <contract:0xaaae7baea6a6c7c4c2dfeb977efac326af552aaa> 0 0 0 0 ) [[ 1 ]] 1}  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.STATICCALL(
                gas=0x157C,
                address=0xF4C9FC42FAEDA49049E3B8E2B97A17CC2FE95718,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(key=0x1, value=0x1)
        + Op.STOP,
        storage={1: 1},
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0xD15BDAF597BADAA25173C995D18F65D1B514A062),  # noqa: E501
    )
    pre[sender] = Account(balance=0xBEBC200)
    # Source: lll
    # { [[ 1 ]] 0 }
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x0) + Op.STOP,
        storage={1: 1},
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0xF4C9FC42FAEDA49049E3B8E2B97A17CC2FE95718),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=200000,
        value=10,
    )

    post = {
        target: Account(storage={0: 0, 1: 1}, balance=0xDE0B6B3A764000A),
        addr: Account(storage={1: 1}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
