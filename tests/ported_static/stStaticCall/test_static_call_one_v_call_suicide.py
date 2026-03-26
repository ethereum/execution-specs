"""
test_static_call_one_v_call_suicide

Ported from:
state_tests/stStaticCall/static_CALL_OneVCallSuicideFiller.json
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
    ["state_tests/stStaticCall/static_CALL_OneVCallSuicideFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_static_call_one_v_call_suicide(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_static_call_one_v_call_suicide"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x4f31b3206fbf0e0e598b9b1a7d8ac86302a0ff1d8930738f1bebae9b67173e52
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[sender] = Account(balance=0xe8d4a51000)
    # Source: lll
    # {  [[1]](STATICCALL 60000 <contract:0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0) [[100]] 1 }
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=Op.STATICCALL(gas=0xea60, address=0x9eb21fc7fd6db177a8aaefb4fb2289d2b31c8ed5, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0x64, value=0x1) + Op.STOP,
        balance=100,
        nonce=0,
        address=Address("0x8cb4cc1396942231551322a3ba85da94c3b1ec16"),  # noqa: E501
    )
    # Source: lll
    # { (SELFDESTRUCT <contract:target:0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b>) }
    addr_0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b = pre.deploy_contract(
        code=Op.SELFDESTRUCT(address=0x8cb4cc1396942231551322a3ba85da94c3b1ec16)
        + Op.STOP,
        balance=1,
        nonce=0,
        address=Address("0x9eb21fc7fd6db177a8aaefb4fb2289d2b31c8ed5"),  # noqa: E501
    )


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=600000,
        nonce=0,
        gas_price=10,
    )

    post = {
        addr_0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b: Account(balance=1),
        target: Account(storage={1: 0, 100: 1}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
