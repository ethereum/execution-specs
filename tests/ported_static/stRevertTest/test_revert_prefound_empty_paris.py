"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stRevertTest/RevertPrefoundEmpty_ParisFiller.json
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
        "tests/static/state_tests/stRevertTest/RevertPrefoundEmpty_ParisFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_revert_prefound_empty_paris(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )
    callee = Address("0x7db299e0885c85039f56fa504a13dd8ce8a56aa7")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[callee] = Account(balance=10, nonce=0)
    # Source: LLL
    # { [[0]] (CREATE 0 0 32) [[1]]12 }
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0, value=Op.CREATE(value=0x0, offset=0x0, size=0x20)
            )
            + Op.SSTORE(key=0x1, value=0xC)
            + Op.STOP
        ),
        balance=1,
        nonce=0,
        address=Address("0xa000000000000000000000000000000000000000"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xE8D4A51000)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=940000,
    )

    post = {
        contract: Account(
            storage={
                0: 0x7DB299E0885C85039F56FA504A13DD8CE8A56AA7,
                1: 12,
            },
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
