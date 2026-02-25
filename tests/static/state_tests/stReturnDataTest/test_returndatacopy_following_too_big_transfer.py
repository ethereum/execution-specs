"""
This test tries RETURNDATACOPY with a non-zero size after a CALL that fails because of insufficient balance.

Ported from:
tests/static/state_tests/stReturnDataTest/returndatacopy_following_too_big_transferFiller.json

contract code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push3 0x989680
    push20 0x9898dd5e5c526b55ec49b1047e298705c13279f1
    push5 0x0900000000
    call
    pop
    push1 0x20
    push1 0x00
    push1 0x00
    returndatacopy
    push1 0xc8
    push1 0x00
    sstore
    stop

callee code:
    push30 0x111122223333444455556666777788889999aaaabbbbccccddddeeeeffff
    push1 0x00
    mstore
    push1 0x20
    push1 0x00
    return
    stop
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Environment,
    Hash,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["tests/static/state_tests/stReturnDataTest/returndatacopy_following_too_big_transferFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_returndatacopy_following_too_big_transfer(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """This test tries RETURNDATACOPY with a non-zero size after a CALL that fails because of insufficient balance.."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xc102734f6a1e4747310179c0a0fc16e674aa901d")
    contract = Address("0x386e9fc96c1e60f449c2df320f37545cca30f58d")
    callee = Address("0x9898dd5e5c526b55ec49b1047e298705c13279f1")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=111669149696,
    )

    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH3[0x989680] + Op.PUSH20[0x9898dd5e5c526b55ec49b1047e298705c13279f1]
        + Op.PUSH5[0x900000000] + Op.CALL + Op.POP + Op.PUSH1[0x20] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.RETURNDATACOPY + Op.PUSH1[0xc8] + Op.PUSH1[0x0]
        + Op.SSTORE + Op.STOP
    ),
        storage={0x0: 0x1},
    )
    pre[callee] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH30[0x111122223333444455556666777788889999aaaabbbbccccddddeeeeffff]
        + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.RETURN
        + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0x6400000000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x834185262e53584684bf2b72c64e510013c235d0f45e462db65900455df45a35"
        ),
        to=contract,
        data=b"",
        gas_limit=100000,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
