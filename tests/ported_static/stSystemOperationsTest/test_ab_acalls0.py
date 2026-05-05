"""
Test_ab_acalls0.

Ported from:
state_tests/stSystemOperationsTest/ABAcalls0Filler.json
"""

import pytest
from execution_testing import (
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
    ["state_tests/stSystemOperationsTest/ABAcalls0Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_ab_acalls0(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_ab_acalls0."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    # Source: lll
    # {  [[ (PC) ]] (CALL 100000 <contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5> 24 0 0 0 0) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=Op.PC,
            value=Op.CALL(
                gas=0x186A0,
                address=0x44EB1162303B6A60F2F8882D43D661787B3011E6,
                value=0x18,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0xD6CD6EC9ADCA299F2BBFD754FF8BCF6A4B9AAE40),  # noqa: E501
    )
    # Source: lll
    # { [[ (PC) ]] (ADD 1 (CALL 50000 <contract:target:0x095e7baea6a6c7c4c2dfeb977efac326af552d87> 23 0 0 0 0)) }  # noqa: E501
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=Op.PC,
            value=Op.ADD(
                0x1,
                Op.CALL(
                    gas=0xC350,
                    address=0xD6CD6EC9ADCA299F2BBFD754FF8BCF6A4B9AAE40,
                    value=0x17,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            ),
        )
        + Op.STOP,
        balance=23,
        nonce=0,
        address=Address(0x44EB1162303B6A60F2F8882D43D661787B3011E6),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=1000000,
        value=0x186A0,
    )

    post = {
        target: Account(storage={36: 1}),
        addr: Account(storage={38: 1}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
