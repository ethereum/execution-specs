"""
Test_returndatasize_following_successful_create.

Ported from:
state_tests/stReturnDataTest/returndatasize_following_successful_createFiller.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    StateTestFiller,
    Transaction,
    Fork,
)
from execution_testing.vm import Op

from execution_testing.forks import Amsterdam

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stReturnDataTest/returndatasize_following_successful_createFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_returndatasize_following_successful_create(
    state_test: StateTestFiller,
    fork: Fork,
    pre: Alloc,
) -> None:
    """Test_returndatasize_following_successful_create."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
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

    # Source: lll
    # { (seq (CREATE 0 0 (lll (seq (mstore 0 0x112233) (RETURN 0 32) (STOP) ) 0)) (SSTORE 0 (RETURNDATASIZE)) (STOP) )}  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.PUSH1[0xE]
        + Op.CODECOPY(dest_offset=0x0, offset=0x15, size=Op.DUP1)
        + Op.PUSH1[0x0] * 2
        + Op.POP(Op.CREATE)
        + Op.SSTORE(key=0x0, value=Op.RETURNDATASIZE)
        + Op.STOP * 2
        + Op.INVALID
        + Op.MSTORE(offset=0x0, value=0x112233)
        + Op.RETURN(offset=0x0, size=0x20)
        + Op.STOP * 2,
        storage={0: 1},
        nonce=0,
        address=Address(0xE7E262CA8EF9761ACCA450874326B1F3F483A73F),  # noqa: E501
    )
    pre[sender] = Account(balance=0x6400000000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=2100000 if fork >= Amsterdam else 100000,
    )

    post = {target: Account(storage={0: 0})}

    state_test(env=env, pre=pre, post=post, tx=tx)
