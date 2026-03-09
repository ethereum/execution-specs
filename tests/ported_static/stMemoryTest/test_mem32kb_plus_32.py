"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stMemoryTest/mem32kb+32Filler.json
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
    ["tests/static/state_tests/stMemoryTest/mem32kb+32Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_mem32kb_plus_32(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x834185262E53584684BF2B72C64E510013C235D0F45E462DB65900455DF45A35
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=42949672960,
    )

    # Source: LLL
    # { (MSTORE 32000 42) [[ 1 ]] (MLOAD 32000) [[ 0 ]] (MSIZE) }
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x7D00, value=0x2A)
            + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x7D00))
            + Op.SSTORE(key=0x0, value=Op.MSIZE)
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0xb73f7199ef3863783b117a38dbd30d67e44f29e7"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x6400000000)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=100000,
        value=10,
    )

    post = {
        contract: Account(storage={0: 32032, 1: 42}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
