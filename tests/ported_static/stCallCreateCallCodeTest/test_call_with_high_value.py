"""
call with value and not enough value to send.

Ported from:
tests/static/state_tests/stCallCreateCallCodeTest/callWithHighValueFiller.json
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
        "tests/static/state_tests/stCallCreateCallCodeTest/callWithHighValueFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_call_with_high_value(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Call with value and not enough value to send."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
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

    pre.deploy_contract(
        code=Op.SSTORE(key=0x2, value=0x1) + Op.STOP,
        balance=23,
        nonce=0,
        address=Address("0x9d8c3fed067968360493f6deb5b169a720dac8a2"),  # noqa: E501
    )
    # Source: LLL
    # {  [[ 0 ]] (CALL 150000 <contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5> 1000000000000000001 0 64 0 2 ) }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.CALL(
                    gas=0x249F0,
                    address=0x9D8C3FED067968360493F6DEB5B169A720DAC8A2,
                    value=0xDE0B6B3A7640001,
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x2,
                ),
            )
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0xccc6849cd07c3e5b61ab6d7e798d3c4007615284"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=3000000,
    )

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
