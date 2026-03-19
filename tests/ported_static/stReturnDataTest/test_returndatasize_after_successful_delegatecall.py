"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stReturnDataTest
returndatasize_after_successful_delegatecallFiller.json
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
        "tests/static/state_tests/stReturnDataTest/returndatasize_after_successful_delegatecallFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_returndatasize_after_successful_delegatecall(
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
    # { (seq (DELEGATECALL 60000 <contract:0x1000000000000000000000000000000000000002> 0 0 0 0) (SSTORE 0 (RETURNDATASIZE)))}  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.POP(
                Op.DELEGATECALL(
                    gas=0xEA60,
                    address=0x7C17DBBFA29DC8391BFA19022ECB4FDA54FC826A,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(key=0x0, value=Op.RETURNDATASIZE)
            + Op.STOP
        ),
        storage={
            0x0: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
        },
        nonce=0,
        address=Address("0x1c7cce7753e67952a031524e6505e53f170520be"),  # noqa: E501
    )
    callee = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=Op.CALLER)
            + Op.RETURN(offset=0x0, size=0x14)
            + Op.STOP
        ),
        balance=0x6400000000,
        nonce=0,
        address=Address("0x7c17dbbfa29dc8391bfa19022ecb4fda54fc826a"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x6400000000)

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 20},
                    code=bytes.fromhex(
                        "6000600060006000737c17dbbfa29dc8391bfa19022ecb4fda54fc826a61ea60f4503d60005500"  # noqa: E501
                    ),
                ),
                callee: Account(code=bytes.fromhex("3360005260146000f300")),
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
