"""
1) Account A already exists in the state and contains code
Call to Account B do the following:
- stores Account A code hash to 1
- stores Account A code size to 2
- stores Account A code to 3
- Run selfdestruct on A
- stores Account A code hash to 4
- stores Account A code size to 5
- stores Account A code to 6


Ported from:
tests/static/state_tests/stExtCodeHash/extCodeHashDeletedAccount1Filler.yml

callee code:
    push20 0x6fa1b655968fdb5e58d9af61a04c3ce435dd4caf
    extcodehash
    push1 0x01
    sstore
    push20 0x6fa1b655968fdb5e58d9af61a04c3ce435dd4caf
    extcodesize
    push1 0x02
    sstore
    push1 0x02
    sload
    push1 0x00
    push1 0x00
    push20 0x6fa1b655968fdb5e58d9af61a04c3ce435dd4caf
    extcodecopy
    push1 0x00
    mload
    push1 0x03
    sstore
    push1 0x20
    push1 0x00
    ... (26 more instructions)

callee_1 code:
    push20 0xdeadbeef00000000000000000000000000000000
    balance
    selfdestruct
    stop

contract code:
    push1 0x20
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0x55a5d644515a8aa5ee0d37f3a506fbc0d7183752
    push3 0x03f7a0
    call
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
    ["tests/static/state_tests/stExtCodeHash/extCodeHashDeletedAccount1Filler.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_ext_code_hash_deleted_account1(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """1) Account A already exists in the state and contains code
Call to Account B do the following:
- stores Account A code hash to 1
- stores Account A code size to 2
- stores Account A code to 3
- Run selfdestruct on A
- stores Account A code hash to 4
- stores Account A code size to 5
- stores Account A code to 6
."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xebaf50debf10e08302fe4280c32df010463ca297")
    contract = Address("0x8548c4f1bac37bae8007072eff53d7166078473a")
    callee = Address("0x55a5d644515a8aa5ee0d37f3a506fbc0d7183752")
    callee_1 = Address("0x6fa1b655968fdb5e58d9af61a04c3ce435dd4caf")

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
        Op.PUSH20[0x6fa1b655968fdb5e58d9af61a04c3ce435dd4caf] + Op.EXTCODEHASH
        + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH20[0x6fa1b655968fdb5e58d9af61a04c3ce435dd4caf] + Op.EXTCODESIZE
        + Op.PUSH1[0x2] + Op.SSTORE + Op.PUSH1[0x2] + Op.SLOAD + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0x6fa1b655968fdb5e58d9af61a04c3ce435dd4caf]
        + Op.EXTCODECOPY + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x3] + Op.SSTORE
        + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0x6fa1b655968fdb5e58d9af61a04c3ce435dd4caf]
        + Op.PUSH3[0x249f0] + Op.CALL + Op.POP
        + Op.PUSH20[0x6fa1b655968fdb5e58d9af61a04c3ce435dd4caf] + Op.EXTCODEHASH
        + Op.PUSH1[0x4] + Op.SSTORE
        + Op.PUSH20[0x6fa1b655968fdb5e58d9af61a04c3ce435dd4caf] + Op.EXTCODESIZE
        + Op.PUSH1[0x5] + Op.SSTORE + Op.PUSH1[0x5] + Op.SLOAD + Op.PUSH1[0x0]
        + Op.PUSH1[0x20] + Op.PUSH20[0x6fa1b655968fdb5e58d9af61a04c3ce435dd4caf]
        + Op.EXTCODECOPY + Op.PUSH1[0x20] + Op.MLOAD + Op.PUSH1[0x6] + Op.SSTORE
        + Op.STOP
    ),
    )
    pre[callee_1] = Account(
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
        Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0x55a5d644515a8aa5ee0d37f3a506fbc0d7183752]
        + Op.PUSH3[0x3f7a0] + Op.CALL + Op.STOP
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
    ["tests/static/state_tests/stExtCodeHash/extCodeHashDeletedAccount1CancunFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_ext_code_hash_deleted_account1_cancun(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """1) Account A already exists in the state and contains code
Call to Account B do the following:
- stores Account A code hash to 1
- stores Account A code size to 2
- stores Account A code to 3
- Run selfdestruct on A
- stores Account A code hash to 4
- stores Account A code size to 5
- stores Account A code to 6
Same as extCodeHashDeletedAccount1Cancun test but with dynamic account suicide for Cancun
."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0x095e7baea6a6c7c4c2dfeb977efac326af552d87")
    callee = Address("0xaaaaaaaa00000000000000000000000000000000")
    callee_1 = Address("0xbbbbbbbb00000000000000000000000000000000")
    callee_2 = Address("0xcccccccc00000000000000000000000000000000")

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
        Op.PUSH1[0x4a] + Op.DUP1 + Op.PUSH1[0x3b] + Op.PUSH1[0x0] + Op.CODECOPY
        + Op.PUSH1[0x0] + Op.PUSH8[0xde0b6b3a7640000] + Op.CREATE + Op.POP
        + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0xbbbbbbbb00000000000000000000000000000000]
        + Op.PUSH3[0x3f7a0] + Op.CALL + Op.STOP + Op.INVALID + Op.PUSH1[0x0]
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
        Op.PUSH20[0xdeadbeef00000000000000000000000000000000] + Op.BALANCE
        + Op.SELFDESTRUCT + Op.STOP
    ),
    )
    pre[callee_1] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH20[0xd2571607e241ecf590ed94b12d87c94babe36db6] + Op.EXTCODEHASH
        + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH20[0xd2571607e241ecf590ed94b12d87c94babe36db6] + Op.EXTCODESIZE
        + Op.PUSH1[0x2] + Op.SSTORE + Op.PUSH1[0x2] + Op.SLOAD + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0xd2571607e241ecf590ed94b12d87c94babe36db6]
        + Op.EXTCODECOPY + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x3] + Op.SSTORE
        + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0xd2571607e241ecf590ed94b12d87c94babe36db6]
        + Op.PUSH3[0x249f0] + Op.CALL + Op.POP
        + Op.PUSH20[0xd2571607e241ecf590ed94b12d87c94babe36db6] + Op.EXTCODEHASH
        + Op.PUSH1[0x4] + Op.SSTORE
        + Op.PUSH20[0xd2571607e241ecf590ed94b12d87c94babe36db6] + Op.EXTCODESIZE
        + Op.PUSH1[0x5] + Op.SSTORE + Op.PUSH1[0x5] + Op.SLOAD + Op.PUSH1[0x0]
        + Op.PUSH1[0x20] + Op.PUSH20[0xd2571607e241ecf590ed94b12d87c94babe36db6]
        + Op.EXTCODECOPY + Op.PUSH1[0x20] + Op.MLOAD + Op.PUSH1[0x6] + Op.SSTORE
        + Op.STOP
    ),
    )
    pre[callee_2] = Account(
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
