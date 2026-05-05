"""
Test_static_callcodecallcallcode_101_suicide_middle.

Ported from:
state_tests/stStaticCall/static_callcodecallcallcode_101_SuicideMiddleFiller.json
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
    [
        "state_tests/stStaticCall/static_callcodecallcallcode_101_SuicideMiddleFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.slow
@pytest.mark.pre_alloc_mutable
def test_static_callcodecallcallcode_101_suicide_middle(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_static_callcodecallcallcode_101_suicide_middle."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0x1000000000000000000000000000000000000000)
    contract_1 = Address(0x1000000000000000000000000000000000000001)
    contract_2 = Address(0x1000000000000000000000000000000000000002)
    contract_3 = Address(0x1000000000000000000000000000000000000003)
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=30000000,
    )

    # Source: lll
    # {  (MSTORE 3 1) }
    contract_3 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x3, value=0x1) + Op.STOP,
        balance=0x2540BE400,
        nonce=0,
        address=Address(0x1000000000000000000000000000000000000003),  # noqa: E501
    )
    # Source: lll
    # {  [[ 0 ]] (DELEGATECALL 150000 0x1000000000000000000000000000000000000001 0 64 0 64 ) [[ 1 ]] 1 }  # noqa: E501
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.DELEGATECALL(
                gas=0x249F0,
                address=0x1000000000000000000000000000000000000001,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            ),
        )
        + Op.SSTORE(key=0x1, value=0x1)
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0x1000000000000000000000000000000000000000),  # noqa: E501
    )
    # Source: lll
    # {  (MSTORE 3 1) (STATICCALL 100000 0x1000000000000000000000000000000000000002 0 64 0 64 ) (MSTORE 32 1) }  # noqa: E501
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x3, value=0x1)
        + Op.POP(
            Op.STATICCALL(
                gas=0x186A0,
                address=0x1000000000000000000000000000000000000002,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            )
        )
        + Op.MSTORE(offset=0x20, value=0x1)
        + Op.STOP,
        balance=0x2540BE400,
        nonce=0,
        address=Address(0x1000000000000000000000000000000000000001),  # noqa: E501
    )
    # Source: lll
    # { (SELFDESTRUCT 0x1000000000000000000000000000000000000000) (DELEGATECALL 50000 0x1000000000000000000000000000000000000003 0 64 0 64 ) }  # noqa: E501
    contract_2 = pre.deploy_contract(  # noqa: F841
        code=Op.SELFDESTRUCT(
            address=0x1000000000000000000000000000000000000000
        )
        + Op.DELEGATECALL(
            gas=0xC350,
            address=0x1000000000000000000000000000000000000003,
            args_offset=0x0,
            args_size=0x40,
            ret_offset=0x0,
            ret_size=0x40,
        )
        + Op.STOP,
        balance=0x2540BE400,
        nonce=0,
        address=Address(0x1000000000000000000000000000000000000002),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=Bytes(""),
        gas_limit=3000000,
    )

    post = {contract_0: Account(storage={0: 1, 1: 1})}

    state_test(env=env, pre=pre, post=post, tx=tx)
