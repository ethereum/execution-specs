"""
Test_call_to_empty_then_call_error_paris.

Ported from:
state_tests/stEIP158Specific/callToEmptyThenCallErrorParisFiller.json
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
    ["state_tests/stEIP158Specific/callToEmptyThenCallErrorParisFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_call_to_empty_then_call_error_paris(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_call_to_empty_then_call_error_paris."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    addr_2 = Address(0x76FAE819612A29489A1A43208613D8F8557B8898)
    sender = EOA(
        key=0x4F31B3206FBF0E0E598B9B1A7D8AC86302A0FF1D8930738F1BEBAE9B67173E52
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[sender] = Account(balance=0xE8D4A51000)
    # Source: lll
    # { (CALL 0 <eoa:0xee098e6c2a43d9e2c04f08f0c3a87b0ba59079d4> 0 0 0 0 0) (CALL 0 <contract:0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0 0) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.POP(
            Op.CALL(
                gas=0x0,
                address=0x76FAE819612A29489A1A43208613D8F8557B8898,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x0,
            address=0xAB4CDAE660B629C6F7BE5A12139558E6296AD0B5,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        nonce=0,
        address=Address(0x2FD4E62119E6702B1B340B14AAB503AF144D0DA4),  # noqa: E501
    )
    # Source: lll
    # { (GAS) }
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.GAS + Op.STOP,
        nonce=0,
        address=Address(0xAB4CDAE660B629C6F7BE5A12139558E6296AD0B5),  # noqa: E501
    )
    pre[addr_2] = Account(balance=10)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=600000,
    )

    post = {addr_2: Account(balance=10)}

    state_test(env=env, pre=pre, post=post, tx=tx)
