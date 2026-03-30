"""
Test_static_call_oog_additional_gas_costs2_paris.

Ported from:
state_tests/stStaticCall/static_call_OOG_additionalGasCosts2_ParisFiller.json
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
        "state_tests/stStaticCall/static_call_OOG_additionalGasCosts2_ParisFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.slow
@pytest.mark.pre_alloc_mutable
def test_static_call_oog_additional_gas_costs2_paris(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_static_call_oog_additional_gas_costs2_paris."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    addr = Address(0x76FAE819612A29489A1A43208613D8F8557B8898)
    sender = EOA(
        key=0xE04D1AC7DDDA0C98397D56A0B501E960D4CD325A39286919AC23C1A07009A869
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=3000000000,
    )

    # Source: lll
    # { [[ 0 ]] (STATICCALL 6000 <eoa:0x1000000000000000000000000000000000000001> 0 64 0 64 )  [[ 1 ]] (GAS) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.STATICCALL(
                gas=0x1770,
                address=0x76FAE819612A29489A1A43208613D8F8557B8898,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            ),
        )
        + Op.SSTORE(key=0x1, value=Op.GAS)
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0xB836BAD7C1AE4C13AC3CBEC9A4445EA8B80E3A31),  # noqa: E501
    )
    pre[addr] = Account(balance=10)
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=30000,
    )

    post = {
        target: Account(storage={}),
        addr: Account(balance=10),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
