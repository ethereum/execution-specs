"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stReturnDataTest
returndatacopy_following_createFiller.json
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
        "tests/static/state_tests/stReturnDataTest/returndatacopy_following_createFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_returndatacopy_following_create(
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

    callee = pre.deploy_contract(
        code=(
            Op.MSTORE(
                offset=0x0,
                value=0x111122223333444455556666777788889999AAAABBBBCCCCDDDDEEEEFFFF,  # noqa: E501
            )
            + Op.RETURN(offset=0x0, size=0x20)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x9898dd5e5c526b55ec49b1047e298705c13279f1"),  # noqa: E501
    )
    # Source: LLL
    # { (seq (create (STOP)) (RETURNDATACOPY 0 0 32) (SSTORE 0 (MLOAD 0)) )}
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=0x0)
            + Op.MSTORE(offset=0x0, value=Op.MSIZE)
            + Op.PUSH1[0x2]
            + Op.CODECOPY(
                dest_offset=Op.MLOAD(offset=0x0),
                offset=0x28,
                size=Op.DUP1,
            )
            + Op.MLOAD(offset=0x0)
            + Op.PUSH1[0x0]
            + Op.POP(Op.CREATE)
            + Op.RETURNDATACOPY(dest_offset=0x0, offset=0x0, size=0x20)
            + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
            + Op.STOP
            + Op.INVALID
            + Op.STOP
            + Op.STOP
        ),
        storage={0x0: 0x1},
        nonce=0,
        address=Address("0xb2f12f3b77dad19c11029cb8ee4eecb144e05ad3"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x6400000000)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "7d111122223333444455556666777788889999aaaabbbbccccddddeeeeffff60005260206000f300"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 1},
                    code=bytes.fromhex(
                        "6000600052596000526002806028600051396000516000f0506020600060003e60005160005500fe0000"  # noqa: E501
                    ),
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
