"""
EXTCODEHASH/EXTCODESIZE of an account before and after changing its nonce, balance and storage

Ported from:
tests/static/state_tests/stExtCodeHash/extCodeHashChangedAccountFiller.json

contract code:
    push20 0xd24c8b8f861979e2482a2b7af5505414a6946505
    extcodehash
    push1 0x00
    sstore
    push20 0xd24c8b8f861979e2482a2b7af5505414a6946505
    extcodesize
    push1 0x01
    sstore
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push2 0x03e8
    push20 0xd24c8b8f861979e2482a2b7af5505414a6946505
    push3 0x010000
    call
    pop
    push20 0xd24c8b8f861979e2482a2b7af5505414a6946505
    extcodehash
    push1 0x02
    ... (7 more instructions)

callee code:
    push1 0x00
    push1 0x00
    push1 0x00
    create
    pop
    push2 0x1234
    push1 0x00
    sstore
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
    ["tests/static/state_tests/stExtCodeHash/extCodeHashChangedAccountFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_ext_code_hash_changed_account(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """EXTCODEHASH/EXTCODESIZE of an account before and after changing its nonce, balance and storage."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0x5d8645d9535c54ae9d2d01dba614bc0c249b0dee")
    contract = Address("0xca42bdabdac8da80dc4409e64311488702655f8f")
    callee = Address("0xd24c8b8f861979e2482a2b7af5505414a6946505")
    callee_1 = Address("0xebaf50debf10e08302fe4280c32df010463ca297")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH20[0xd24c8b8f861979e2482a2b7af5505414a6946505] + Op.EXTCODEHASH
        + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH20[0xd24c8b8f861979e2482a2b7af5505414a6946505] + Op.EXTCODESIZE
        + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH2[0x3e8]
        + Op.PUSH20[0xd24c8b8f861979e2482a2b7af5505414a6946505] + Op.PUSH3[0x10000]
        + Op.CALL + Op.POP + Op.PUSH20[0xd24c8b8f861979e2482a2b7af5505414a6946505]
        + Op.EXTCODEHASH + Op.PUSH1[0x2] + Op.SSTORE
        + Op.PUSH20[0xd24c8b8f861979e2482a2b7af5505414a6946505] + Op.EXTCODESIZE
        + Op.PUSH1[0x3] + Op.SSTORE + Op.STOP + Op.STOP
    ),
    )
    pre[callee] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.CREATE + Op.POP
        + Op.PUSH2[0x1234] + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_1] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0xc41b109d1b0ed67f0ea3f5444f18a4e88f76e1489a7253c70079ab9a6c191c00"
        ),
        to=contract,
        data=b"",
        gas_limit=400000,
        gas_price=10,
        nonce=0,
        value=1,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
