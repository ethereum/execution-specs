"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stMemoryTest/mload16bitBoundFiller.json
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
    ["tests/static/state_tests/stMemoryTest/mload16bitBoundFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_mload16bit_bound(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xA9DF11BD92FC8535FFCA3AE0A2133C80D5F4ECC5D31D100B94FF03E63F7E74FF
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=17592320524892,
    )

    pre[sender] = Account(balance=0xA00050281798)
    # Source: LLL
    # { [[ 1 ]] (MLOAD 65536) }
    contract = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x10000)) + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x85eaa01ac6288c06360d431d62cd865c92b74a28"),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=100000,
        value=10,
    )

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
