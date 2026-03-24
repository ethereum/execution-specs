"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stReturnDataTest
returndatacopy_following_successful_createFiller.json
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
    [
        "tests/static/state_tests/stReturnDataTest/returndatacopy_following_successful_createFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_returndatacopy_following_successful_create(
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
        gas_limit=111669149696,
    )

    # Source: LLL
    # { (create (STOP)) (RETURNDATACOPY 0 1 32) (SSTORE 0 (MLOAD 0)) }
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
            + Op.RETURNDATACOPY(dest_offset=0x0, offset=0x1, size=0x20)
            + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
            + Op.STOP
            + Op.INVALID
            + Op.STOP
            + Op.STOP
        ),
        storage={0x0: 0x2},
        nonce=0,
        address=Address("0xbabe109963095efa4c742d15426f841a7033d6aa"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x6400000000)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=100000,
    )

    post = {
        contract: Account(storage={0: 2}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
