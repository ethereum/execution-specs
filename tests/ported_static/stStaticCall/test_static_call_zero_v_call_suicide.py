"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stStaticCall/static_CALL_ZeroVCallSuicideFiller.json
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
    [
        "tests/static/state_tests/stStaticCall/static_CALL_ZeroVCallSuicideFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
@pytest.mark.slow
def test_static_call_zero_v_call_suicide(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
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

    pre.deploy_contract(
        code=(
            Op.SELFDESTRUCT(address=0x7A0DDD9CCF14D217E4C1AE6B7C2C770CD4E929EE)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x79968a94dbedb20475585e9dd4dae6333add4c01"),  # noqa: E501
    )
    # Source: LLL
    # { (STATICCALL 60000 <contract:0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0) }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.STATICCALL(
                gas=0xEA60,
                address=0x79968A94DBEDB20475585E9DD4DAE6333ADD4C01,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x7a0ddd9ccf14d217e4c1ae6b7c2c770cd4e929ee"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xE8D4A51000)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=600000,
    )

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
