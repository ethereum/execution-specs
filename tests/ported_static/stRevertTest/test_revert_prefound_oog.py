"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stRevertTest/RevertPrefoundOOGFiller.json
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
    ["tests/static/state_tests/stRevertTest/RevertPrefoundOOGFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_revert_prefound_oog(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x4F31B3206FBF0E0E598B9B1A7D8AC86302A0FF1D8930738F1BEBAE9B67173E52
    )
    callee = Address("0x85fdde91fd0ce22a2968e1f1b2ebb9f9e5a180ba")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    # Source: LLL
    # { [[0]] (CREATE 0 0 32) (KECCAK256 0x00 0x2fffff) }
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0, value=Op.CREATE(value=0x0, offset=0x0, size=0x20)
            )
            + Op.SHA3(offset=0x0, size=0x2FFFFF)
            + Op.STOP
        ),
        balance=1,
        nonce=0,
        address=Address("0x35b3f8ca79c46f2cbc3db596a2162ade570b0add"),  # noqa: E501
    )
    pre[callee] = Account(balance=1, nonce=0)
    pre[sender] = Account(balance=0xE8D4A51000)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=930000,
    )

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
