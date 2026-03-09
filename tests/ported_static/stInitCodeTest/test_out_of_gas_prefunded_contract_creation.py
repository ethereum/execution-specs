"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stInitCodeTest
OutOfGasPrefundedContractCreationFiller.json
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

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stInitCodeTest/OutOfGasPrefundedContractCreationFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit, expected_post",
    [
        (
            154000,
            {
                Address("0x64e2ebd6405af8cb348aec519084d3fff42ebba6"): Account(
                    storage={0: 0x112233}
                )
            },
        ),
        (65000, {}),
        (95000, {}),
    ],
    ids=["case0", "case1", "case2"],
)
@pytest.mark.pre_alloc_mutable
def test_out_of_gas_prefunded_contract_creation(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
    expected_post: dict,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )
    contract = Address("0x6295ee1b4f6dd65047762f924ecd367c17eabf8f")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000000,
    )

    pre[contract] = Account(balance=1, nonce=0)
    pre[sender] = Account(balance=0xF424000)

    tx = Transaction(
        sender=sender,
        to=None,
        data=bytes.fromhex(
            "600980601160003960006001f0500000fe621122336000550000"
        ),
        gas_limit=tx_gas_limit,
        value=1,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
