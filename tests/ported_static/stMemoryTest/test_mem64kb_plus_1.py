"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stMemoryTest/mem64kb+1Filler.json
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
    ["tests/static/state_tests/stMemoryTest/mem64kb+1Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_mem64kb_plus_1(
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
    # { (MSTORE 63969 42) [[ 1 ]] (MLOAD 63969) [[ 0 ]] (MSIZE) }
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0xF9E1, value=0x2A)
            + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0xF9E1))
            + Op.SSTORE(key=0x0, value=Op.MSIZE)
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x079111606e69dd3101ac45527bcde41fb2c251e2"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x6400000000)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=100000,
        value=10,
    )

    post = {
        contract: Account(storage={0: 64032, 1: 42}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
