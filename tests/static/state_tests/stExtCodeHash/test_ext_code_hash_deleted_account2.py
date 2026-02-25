"""
2) Account A already exists in the state and contains code
Call to Account B stores Account A code hash to 1, code size to 2, code to 3
Call to Account C runs self destruct on A
Call to Account B stores Account A code hash to 4, code size to 5, code to 6


Ported from:
tests/static/state_tests/stExtCodeHash/extCodeHashDeletedAccount2Filler.yml

callee code:
    push20 0xdeadbeef00000000000000000000000000000000
    balance
    selfdestruct
    stop

contract code:
    push1 0x01
    push1 0x00
    mstore
    push1 0x20
    push1 0x00
    push1 0x20
    push1 0x00
    push1 0x00
    push20 0xe1ed4cfdc92756d14f0f7ab7b6163ba160141de7
    push3 0x0249f0
    call
    pop
    push1 0x20
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0x6fa1b655968fdb5e58d9af61a04c3ce435dd4caf
    push3 0x0249f0
    call
    ... (13 more instructions)

callee_1 code:
    push1 0x20
    push1 0x00
    push1 0x00
    calldatacopy
    push20 0x6fa1b655968fdb5e58d9af61a04c3ce435dd4caf
    extcodehash
    push1 0x00
    mload
    sstore
    push20 0x6fa1b655968fdb5e58d9af61a04c3ce435dd4caf
    extcodesize
    push1 0x20
    mstore
    push1 0x01
    push1 0x00
    mload
    add
    push1 0x00
    mstore
    push1 0x20
    ... (22 more instructions)
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
    ["tests/static/state_tests/stExtCodeHash/extCodeHashDeletedAccount2Filler.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_ext_code_hash_deleted_account2(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """2) Account A already exists in the state and contains code
Call to Account B stores Account A code hash to 1, code size to 2, code to 3
Call to Account C runs self destruct on A
Call to Account B stores Account A code hash to 4, code size to 5, code to 6
."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xebaf50debf10e08302fe4280c32df010463ca297")
    contract = Address("0x81f8b96225e16fc8ce587eefe7c7cbe644a21732")
    callee = Address("0x6fa1b655968fdb5e58d9af61a04c3ce435dd4caf")
    callee_1 = Address("0xe1ed4cfdc92756d14f0f7ab7b6163ba160141de7")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre[callee] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH20[0xdeadbeef00000000000000000000000000000000] + Op.BALANCE
        + Op.SELFDESTRUCT + Op.STOP
    ),
    )
    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x20] + Op.PUSH1[0x0]
        + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xe1ed4cfdc92756d14f0f7ab7b6163ba160141de7] + Op.PUSH3[0x249f0]
        + Op.CALL + Op.POP + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x6fa1b655968fdb5e58d9af61a04c3ce435dd4caf] + Op.PUSH3[0x249f0]
        + Op.CALL + Op.POP + Op.PUSH1[0x4] + Op.PUSH1[0x20] + Op.MSTORE
        + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.PUSH1[0x20] + Op.PUSH1[0x20]
        + Op.PUSH1[0x0] + Op.PUSH20[0xe1ed4cfdc92756d14f0f7ab7b6163ba160141de7]
        + Op.PUSH3[0x249f0] + Op.CALL + Op.STOP
    ),
    )
    pre[callee_1] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.CALLDATACOPY
        + Op.PUSH20[0x6fa1b655968fdb5e58d9af61a04c3ce435dd4caf] + Op.EXTCODEHASH
        + Op.PUSH1[0x0] + Op.MLOAD + Op.SSTORE
        + Op.PUSH20[0x6fa1b655968fdb5e58d9af61a04c3ce435dd4caf] + Op.EXTCODESIZE
        + Op.PUSH1[0x20] + Op.MSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.ADD + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x20] + Op.MLOAD
        + Op.PUSH1[0x0] + Op.MLOAD + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x0]
        + Op.MLOAD + Op.ADD + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x20] + Op.MLOAD
        + Op.PUSH1[0x0] + Op.PUSH1[0x40]
        + Op.PUSH20[0x6fa1b655968fdb5e58d9af61a04c3ce435dd4caf] + Op.EXTCODECOPY
        + Op.PUSH1[0x40] + Op.MLOAD + Op.PUSH1[0x0] + Op.MLOAD + Op.SSTORE + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0xe04d1ac7ddda0c98397d56a0b501e960d4cd325a39286919ac23c1a07009a869"
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


@pytest.mark.ported_from(
    ["tests/static/state_tests/stExtCodeHash/extCodeHashDeletedAccount2CancunFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_ext_code_hash_deleted_account2_cancun(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """2) Account A already exists in the state and contains code
Call to Account B stores Account A code hash to 1, code size to 2, code to 3
Call to Account C runs self destruct on A
Call to Account B stores Account A code hash to 4, code size to 5, code to 6
Just in case copy of extCodeHashDeletedAccount2 test with dynamic account suicide for Cancun
."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0x095e7baea6a6c7c4c2dfeb977efac326af552d87")
    callee = Address("0xbbbbbbbb00000000000000000000000000000000")
    callee_1 = Address("0xcccccccc00000000000000000000000000000000")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre[contract] = Account(
        balance=0x1bc16d674ec80000,
        nonce=0,
        code=(
        Op.PUSH1[0x4a] + Op.DUP1 + Op.PUSH1[0x8f] + Op.PUSH1[0x0] + Op.CODECOPY
        + Op.PUSH1[0x0] + Op.PUSH8[0xde0b6b3a7640000] + Op.CREATE + Op.POP
        + Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x20] + Op.PUSH1[0x0]
        + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xbbbbbbbb00000000000000000000000000000000] + Op.PUSH3[0x249f0]
        + Op.CALL + Op.POP + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xd2571607e241ecf590ed94b12d87c94babe36db6] + Op.PUSH3[0x249f0]
        + Op.CALL + Op.POP + Op.PUSH1[0x4] + Op.PUSH1[0x20] + Op.MSTORE
        + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.PUSH1[0x20] + Op.PUSH1[0x20]
        + Op.PUSH1[0x0] + Op.PUSH20[0xbbbbbbbb00000000000000000000000000000000]
        + Op.PUSH3[0x249f0] + Op.CALL + Op.STOP + Op.INVALID + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xcccccccc00000000000000000000000000000000] + Op.PUSH3[0x186a0]
        + Op.CALL + Op.POP + Op.PUSH1[0x18] + Op.DUP1 + Op.PUSH1[0x32] + Op.PUSH1[0x0]
        + Op.CODECOPY + Op.PUSH1[0x0] + Op.RETURN + Op.STOP + Op.INVALID
        + Op.PUSH20[0xdeadbeef00000000000000000000000000000000] + Op.BALANCE
        + Op.SELFDESTRUCT + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.CALLDATACOPY
        + Op.PUSH20[0xd2571607e241ecf590ed94b12d87c94babe36db6] + Op.EXTCODEHASH
        + Op.PUSH1[0x0] + Op.MLOAD + Op.SSTORE
        + Op.PUSH20[0xd2571607e241ecf590ed94b12d87c94babe36db6] + Op.EXTCODESIZE
        + Op.PUSH1[0x20] + Op.MSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.ADD + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x20] + Op.MLOAD
        + Op.PUSH1[0x0] + Op.MLOAD + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x0]
        + Op.MLOAD + Op.ADD + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x20] + Op.MLOAD
        + Op.PUSH1[0x0] + Op.PUSH1[0x40]
        + Op.PUSH20[0xd2571607e241ecf590ed94b12d87c94babe36db6] + Op.EXTCODECOPY
        + Op.PUSH1[0x40] + Op.MLOAD + Op.PUSH1[0x0] + Op.MLOAD + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_1] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP,
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
