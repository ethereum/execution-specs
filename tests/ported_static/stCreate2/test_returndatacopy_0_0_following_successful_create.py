"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stCreate2
returndatacopy_0_0_following_successful_createFiller.json
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
        "tests/static/state_tests/stCreate2/returndatacopy_0_0_following_successful_createFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_returndatacopy_0_0_following_successful_create(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=47244640256,
    )

    # Source: LLL
    # { (create2 0 0 (lll (seq (SSTORE 0 1) (STOP) ) 0) 0) (RETURNDATACOPY 0 0 0) (SSTORE 0 0) (STOP) }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.PUSH1[0x0]
            + Op.PUSH1[0x7]
            + Op.CODECOPY(dest_offset=0x0, offset=0x1F, size=Op.DUP1)
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x0]
            + Op.POP(Op.CREATE2)
            + Op.RETURNDATACOPY(dest_offset=0x0, offset=0x0, size=0x0)
            + Op.SSTORE(key=0x0, value=0x0)
            + Op.STOP
            + Op.STOP
            + Op.INVALID
            + Op.SSTORE(key=0x0, value=0x1)
            + Op.STOP
            + Op.STOP
        ),
        storage={0x0: 0x1},
        nonce=0,
        address=Address("0x0f572e5295c57f15886f9b263e2f6d2d6c7b5ec6"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x6400000000)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    code=bytes.fromhex(
                        "6000600780601f60003960006000f5506000600060003e60006000550000fe60016000550000"  # noqa: E501
                    )
                ),
                Address("0x75579e0e990d8361c48b86c1b57686589df3264a"): Account(
                    storage={0: 1}
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, 0, 0, 0, fork)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=100000,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
