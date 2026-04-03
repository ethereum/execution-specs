"""
Test_zero_value_call_to_empty_paris.

Ported from:
state_tests/stZeroCallsTest/ZeroValue_CALL_ToEmpty_ParisFiller.json
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
    ["state_tests/stZeroCallsTest/ZeroValue_CALL_ToEmpty_ParisFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_zero_value_call_to_empty_paris(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_zero_value_call_to_empty_paris."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    addr = Address(0x76FAE819612A29489A1A43208613D8F8557B8898)
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
    # { [[0]](GAS) [[1]] (CALL 60000 <eoa:0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0 0) [[100]] 1 }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=Op.GAS)
        + Op.SSTORE(
            key=0x1,
            value=Op.CALL(
                gas=0xEA60,
                address=0x76FAE819612A29489A1A43208613D8F8557B8898,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(key=0x64, value=0x1)
        + Op.STOP,
        nonce=0,
        address=Address(0xF202BAE278AC09857F5A56991C7A4679632F5841),  # noqa: E501
    )
    pre[addr] = Account(balance=10)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=600000,
    )

    post = {
        addr: Account(balance=10),
        target: Account(storage={0: 0x8D5B6, 1: 1, 100: 1}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
