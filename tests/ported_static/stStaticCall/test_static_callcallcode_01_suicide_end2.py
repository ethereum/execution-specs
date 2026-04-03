"""
Test_static_callcallcode_01_suicide_end2.

Ported from:
state_tests/stStaticCall/static_callcallcode_01_SuicideEnd2Filler.json
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
    ["state_tests/stStaticCall/static_callcallcode_01_SuicideEnd2Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.slow
@pytest.mark.pre_alloc_mutable
def test_static_callcallcode_01_suicide_end2(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_static_callcallcode_01_suicide_end2."""
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
        gas_limit=30000000,
    )

    # Source: lll
    # {  [[ 0 ]] (STATICCALL 150000 <contract:0x1000000000000000000000000000000000000001> 0 64 0 64 ) [[ 1 ]] 1}  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.STATICCALL(
                gas=0x249F0,
                address=0x5DE1C119E1FC3598726F4D9411DEBD7ED1402187,
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
        address=Address(0x9E10A6AFFFCF5BBA3B47582F2575D787016A56CA),  # noqa: E501
    )
    # Source: lll
    # {  (CALLCODE 50000 <contract:0x1000000000000000000000000000000000000002> 0 0 64 0 64 ) (SELFDESTRUCT <contract:target:0x1000000000000000000000000000000000000000>) }  # noqa: E501
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.POP(
            Op.CALLCODE(
                gas=0xC350,
                address=0xCFB5784A5E49924BECC2D5C5D2EE0A9B141E6216,
                value=0x0,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            )
        )
        + Op.SELFDESTRUCT(address=0x9E10A6AFFFCF5BBA3B47582F2575D787016A56CA)
        + Op.STOP,
        balance=0x2540BE400,
        nonce=0,
        address=Address(0x5DE1C119E1FC3598726F4D9411DEBD7ED1402187),  # noqa: E501
    )
    # Source: lll
    # {  (MSTORE 2 1) }
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x2, value=0x1) + Op.STOP,
        balance=0x2540BE400,
        nonce=0,
        address=Address(0xCFB5784A5E49924BECC2D5C5D2EE0A9B141E6216),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=3000000,
    )

    post = {
        target: Account(storage={0: 0, 1: 1}, balance=0xDE0B6B3A7640000),
        addr_2: Account(storage={2: 0}, balance=0x2540BE400),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
