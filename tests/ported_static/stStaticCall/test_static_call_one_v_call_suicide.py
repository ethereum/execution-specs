"""
Test_static_call_one_v_call_suicide.

Ported from:
state_tests/stStaticCall/static_CALL_OneVCallSuicideFiller.json
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
    ["state_tests/stStaticCall/static_CALL_OneVCallSuicideFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.slow
@pytest.mark.pre_alloc_mutable
def test_static_call_one_v_call_suicide(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_static_call_one_v_call_suicide."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
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
    # {  [[1]](STATICCALL 60000 <contract:0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0) [[100]] 1 }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x1,
            value=Op.STATICCALL(
                gas=0xEA60,
                address=0x9EB21FC7FD6DB177A8AAEFB4FB2289D2B31C8ED5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(key=0x64, value=0x1)
        + Op.STOP,
        balance=100,
        nonce=0,
        address=Address(0x8CB4CC1396942231551322A3BA85DA94C3B1EC16),  # noqa: E501
    )
    # Source: lll
    # { (SELFDESTRUCT <contract:target:0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b>) }  # noqa: E501
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.SELFDESTRUCT(
            address=0x8CB4CC1396942231551322A3BA85DA94C3B1EC16
        )
        + Op.STOP,
        balance=1,
        nonce=0,
        address=Address(0x9EB21FC7FD6DB177A8AAEFB4FB2289D2B31C8ED5),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=600000,
    )

    post = {
        addr: Account(balance=1),
        target: Account(storage={1: 0, 100: 1}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
