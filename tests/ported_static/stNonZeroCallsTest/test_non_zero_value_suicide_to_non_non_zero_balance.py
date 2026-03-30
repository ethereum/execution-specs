"""
Test_non_zero_value_suicide_to_non_non_zero_balance.

Ported from:
state_tests/stNonZeroCallsTest/NonZeroValue_SUICIDE_ToNonNonZeroBalanceFiller.json
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
        "state_tests/stNonZeroCallsTest/NonZeroValue_SUICIDE_ToNonNonZeroBalanceFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_non_zero_value_suicide_to_non_non_zero_balance(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_non_zero_value_suicide_to_non_non_zero_balance."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    addr = Address(0x9089DA66E8BBC08846842A301905501BC8525DC4)
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
    # { (SELFDESTRUCT <eoa:0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b>) }
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SELFDESTRUCT(
            address=0x9089DA66E8BBC08846842A301905501BC8525DC4
        )
        + Op.STOP,
        balance=1,
        nonce=0,
        address=Address(0xEB9A4C7A191790631D13FC4927446F5EF9D201FC),  # noqa: E501
    )
    pre[addr] = Account(balance=100)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=600000,
    )

    post = {
        target: Account(
            storage={},
            code=bytes.fromhex(
                "739089da66e8bbc08846842a301905501bc8525dc4ff00"
            ),
            balance=0,
            nonce=0,
        ),
        addr: Account(balance=101),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
