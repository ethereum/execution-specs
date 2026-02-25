"""
Ported from:
tests/static/state_tests/stSpecialTest/failed_tx_xcf416c53_ParisFiller.json

contract code:
    push29 0x0100000000000000000000000000000000000000000000000000000000
    push1 0x00
    calldataload
    div
    push4 0x97dd3054
    dup2
    eq
    iszero
    push2 0x65
    jumpi
    push1 0x04
    calldataload
    push1 0x40
    mstore
    push1 0x24
    calldataload
    push1 0x60
    mstore
    push1 0x40
    mload
    ... (30 more instructions)
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
    ["tests/static/state_tests/stSpecialTest/failed_tx_xcf416c53_ParisFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_failed_tx_xcf416c53_paris(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x68795c4aa09d6f4ed3e5deddf8c2ad3049a601da")
    sender = Address("0xadd22153059388891d82c6c8e08d80845352bbb0")
    contract = Address("0x7e6e9b4ca1b88937abeaec23bc4b6986caf05188")
    callee = Address("0x76fae819612a29489a1a43208613d8f8557b8898")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=200000000,
    )

    pre[callee] = Account(balance=10, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH29[0x100000000000000000000000000000000000000000000000000000000]
        + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.DIV + Op.PUSH4[0x97dd3054] + Op.DUP2
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x65] + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x40] + Op.MSTORE + Op.PUSH1[0x24]
        + Op.CALLDATALOAD + Op.PUSH1[0x60] + Op.MSTORE + Op.PUSH1[0x40] + Op.MLOAD
        + Op.PUSH1[0x60] + Op.MLOAD + Op.JUMPDEST + Op.DUP1 + Op.DUP3 + Op.SLT
        + Op.ISZERO + Op.PUSH2[0x62] + Op.JUMPI + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.DUP7 + Op.PUSH1[0x0]
        + Op.CALL + Op.POP + Op.PUSH1[0x1] + Op.DUP3 + Op.ADD + Op.SWAP2 + Op.POP
        + Op.PUSH2[0x40] + Op.JUMP + Op.JUMPDEST + Op.POP + Op.POP + Op.JUMPDEST
        + Op.POP
    ),
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=1)

    tx = Transaction(
        secret_key=Hash(
            "0x0ff8d58222f34f6890ddaa468c023b77d6691ed7d3c4dcddae38336212faf54b"
        ),
        to=contract,
        data=bytes.fromhex(
            "97dd30540000000000000000000000000000000000000000000000000000000000000000"
            "00000000000000000000000000000000000000000000000000000000000002bc"
        ),
        gas_limit=16300000,
        gas_price=10,
        nonce=1,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
