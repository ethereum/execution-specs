"""
returndatasize_following_successful_create for create2.

Ported from:
tests/static/state_tests/stCreate2
returndatasize_following_successful_createFiller.json
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
        "tests/static/state_tests/stCreate2/returndatasize_following_successful_createFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_returndatasize_following_successful_create(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Returndatasize_following_successful_create for create2."""
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
    # { (seq (CREATE2 0 0 (lll (seq (mstore 0 0x112233) (RETURN 0 32)) 0) 0) (SSTORE 0 (RETURNDATASIZE)) (STOP) )}  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.PUSH1[0x0]
            + Op.PUSH1[0xD]
            + Op.CODECOPY(dest_offset=0x0, offset=0x17, size=Op.DUP1)
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x0]
            + Op.POP(Op.CREATE2)
            + Op.SSTORE(key=0x0, value=Op.RETURNDATASIZE)
            + Op.STOP
            + Op.STOP
            + Op.INVALID
            + Op.MSTORE(offset=0x0, value=0x112233)
            + Op.RETURN(offset=0x0, size=0x20)
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
                        "6000600d80601760003960006000f5503d6000550000fe6211223360005260206000f300"  # noqa: E501
                    )
                ),
                Address("0x69c6738cb9ceec5b62ae47911b782e1af0b80a3c"): Account(
                    code=bytes.fromhex(
                        "0000000000000000000000000000000000000000000000000000000000112233"  # noqa: E501
                    )
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
