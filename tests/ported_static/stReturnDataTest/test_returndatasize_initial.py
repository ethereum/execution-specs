"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stReturnDataTest/returndatasize_initialFiller.json
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
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stReturnDataTest/returndatasize_initialFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_returndatasize_initial(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
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
        gas_limit=111669149696,
    )

    # Source: LLL
    # { (SSTORE 0 (RETURNDATASIZE)) }
    contract = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.RETURNDATASIZE) + Op.STOP,
        storage={0x0: 0x1},
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x3a939fcca7da8b1332893bcca91690406f4b7a82"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x6400000000)

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {contract: Account(code=bytes.fromhex("3d60005500"))},
        },
    ]

    post, _exc = resolve_expect_post(EXPECT_ENTRIES, 0, 0, 0, fork)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=100000,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
