"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stReturnDataTest
call_ecrec_success_empty_then_returndatasizeFiller.json
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
        "tests/static/state_tests/stReturnDataTest/call_ecrec_success_empty_then_returndatasizeFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_call_ecrec_success_empty_then_returndatasize(
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
    # { (seq (CALL 0x9000 0x1 0 0 0 0 0xaa) (SSTORE 0 (RETURNDATASIZE)) )}
    contract = pre.deploy_contract(
        code=(
            Op.POP(
                Op.CALL(
                    gas=0x9000,
                    address=0x1,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0xAA,
                ),
            )
            + Op.SSTORE(key=0x0, value=Op.RETURNDATASIZE)
            + Op.STOP
        ),
        storage={0x0: 0x60A7},
        nonce=0,
        address=Address("0x77e2f61794bcfd86b1c2380c34aab5fb7c25e95e"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x6400000000)

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    code=bytes.fromhex(
                        "60aa60006000600060006001619000f1503d60005500"
                    )
                )
            },
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
