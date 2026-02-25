"""
4) Call creates Account A
Call to Account B stores Account A hash to 1
Call to Account C runs self destruct on A
Call to Account B stores Account a hash to 2


Ported from:
tests/static/state_tests/stExtCodeHash/extCodeHashDeletedAccount4Filler.yml

contract code:
    push1 0x00
    push1 0x3d
    dup1
    push1 0x94
    push1 0x00
    codecopy
    push1 0x00
    push1 0x00
    create2
    push1 0x00
    mstore
    push1 0x00
    mload
    push1 0x00
    sstore
    push1 0x01
    push1 0x20
    mstore
    push1 0x20
    push1 0x00
    ... (46 more instructions)

callee code:
    push1 0x20
    push1 0x00
    push1 0x00
    calldatacopy
    push20 0xc5691dc90d9fd2a2e9a5fa5bd28bf77ffd60aa78
    extcodehash
    push1 0x00
    mload
    sstore
    push1 0x01
    push1 0x00
    mload
    add
    push1 0x00
    mstore
    push20 0xc5691dc90d9fd2a2e9a5fa5bd28bf77ffd60aa78
    extcodesize
    push1 0x00
    mload
    sstore
    ... (19 more instructions)

callee_1 code:
    push1 0x20
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0xc5691dc90d9fd2a2e9a5fa5bd28bf77ffd60aa78
    push3 0x0249f0
    call
    stop

callee_2 code:
    push20 0xbbbbbbbb00000000000000000000000000000000
    selfdestruct
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
    ["tests/static/state_tests/stExtCodeHash/extCodeHashDeletedAccount4Filler.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_ext_code_hash_deleted_account4(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """4) Call creates Account A
Call to Account B stores Account A hash to 1
Call to Account C runs self destruct on A
Call to Account B stores Account a hash to 2
."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0x095e7baea6a6c7c4c2dfeb977efac326af552d87")
    callee = Address("0xbbbbbbbb00000000000000000000000000000000")
    callee_1 = Address("0xcccccccc00000000000000000000000000000000")
    callee_2 = Address("0xdddddddd00000000000000000000000000000000")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x3d] + Op.DUP1 + Op.PUSH1[0x94] + Op.PUSH1[0x0]
        + Op.CODECOPY + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.CREATE2 + Op.PUSH1[0x0]
        + Op.MSTORE + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x20] + Op.MSTORE + Op.PUSH1[0x20] + Op.PUSH1[0x0]
        + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.PUSH1[0x0]
        + Op.PUSH20[0xbbbbbbbb00000000000000000000000000000000] + Op.PUSH3[0x249f0]
        + Op.CALL + Op.POP + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xcccccccc00000000000000000000000000000000] + Op.PUSH3[0x249f0]
        + Op.CALL + Op.POP + Op.PUSH1[0x4] + Op.PUSH1[0x40] + Op.MSTORE
        + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.PUSH1[0x20] + Op.PUSH1[0x40]
        + Op.PUSH1[0x0] + Op.PUSH20[0xbbbbbbbb00000000000000000000000000000000]
        + Op.PUSH3[0x249f0] + Op.CALL + Op.POP + Op.STOP + Op.STOP + Op.INVALID
        + Op.PUSH20[0xdddddddd00000000000000000000000000000000] + Op.EXTCODESIZE
        + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x0]
        + Op.PUSH1[0x20] + Op.PUSH20[0xdddddddd00000000000000000000000000000000]
        + Op.EXTCODECOPY + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x20] + Op.RETURN
        + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.CALLDATACOPY
        + Op.PUSH20[0xc5691dc90d9fd2a2e9a5fa5bd28bf77ffd60aa78] + Op.EXTCODEHASH
        + Op.PUSH1[0x0] + Op.MLOAD + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x0]
        + Op.MLOAD + Op.ADD + Op.PUSH1[0x0] + Op.MSTORE
        + Op.PUSH20[0xc5691dc90d9fd2a2e9a5fa5bd28bf77ffd60aa78] + Op.EXTCODESIZE
        + Op.PUSH1[0x0] + Op.MLOAD + Op.SSTORE + Op.PUSH1[0x0] + Op.MLOAD + Op.SLOAD
        + Op.PUSH1[0x0] + Op.PUSH1[0x20]
        + Op.PUSH20[0xc5691dc90d9fd2a2e9a5fa5bd28bf77ffd60aa78] + Op.EXTCODECOPY
        + Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.MLOAD + Op.ADD + Op.PUSH1[0x0]
        + Op.MSTORE + Op.PUSH1[0x20] + Op.MLOAD + Op.PUSH1[0x0] + Op.MLOAD + Op.SSTORE
        + Op.STOP
    ),
    )
    pre[callee_1] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0xc5691dc90d9fd2a2e9a5fa5bd28bf77ffd60aa78]
        + Op.PUSH3[0x249f0] + Op.CALL + Op.STOP
    ),
    )
    pre[callee_2] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH20[0xbbbbbbbb00000000000000000000000000000000] + Op.SELFDESTRUCT
        + Op.STOP
    ),
    )

    tx = Transaction(
        secret_key=Hash(
            "0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
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
