"""
Get account A (aaaaaaaa00000000000000000000000000000000) code hash, code size, and code
Calls Account A's code which causes self destruction of A
Get account A codehash, code size and code
It is still getting the same values because selfdestruct is performed
at the end of transaction during state finalization stage.


Ported from:
tests/static/state_tests/stExtCodeHash/extCodeHashDeletedAccountFiller.yml

contract code:
    push1 0x20
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0xdeadbeef00000000000000000000000000000000
    push3 0x0249f0
    call
    pop
    push1 0x20
    push1 0x00
    push1 0x00
    returndatacopy
    push1 0x00
    mload
    push1 0x00
    sstore
    push1 0x20
    push1 0x00
    push1 0x00
    ... (92 more instructions)

callee code:
    push20 0xdeadbeef00000000000000000000000000000000
    selfdestruct
    stop

callee_1 code:
    push20 0xaaaaaaaa00000000000000000000000000000000
    extcodehash
    push1 0x00
    mstore
    push1 0x20
    push1 0x00
    return
    stop

callee_2 code:
    push20 0xaaaaaaaa00000000000000000000000000000000
    extcodesize
    push1 0x00
    mstore
    push1 0x20
    push1 0x00
    return
    stop

callee_3 code:
    push20 0xaaaaaaaa00000000000000000000000000000000
    extcodesize
    push1 0x00
    push1 0x00
    push20 0xaaaaaaaa00000000000000000000000000000000
    extcodecopy
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
    ["tests/static/state_tests/stExtCodeHash/extCodeHashDeletedAccountFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_ext_code_hash_deleted_account(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Get account A (aaaaaaaa00000000000000000000000000000000) code hash, code size, and code
Calls Account A's code which causes self destruction of A
Get account A codehash, code size and code
It is still getting the same values because selfdestruct is performed
at the end of transaction during state finalization stage.
."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0x095e7baea6a6c7c4c2dfeb977efac326af552d87")
    callee = Address("0xaaaaaaaa00000000000000000000000000000000")
    callee_1 = Address("0xdeadbeef00000000000000000000000000000000")
    callee_2 = Address("0xdeadbeef00000000000000000000000000000001")
    callee_3 = Address("0xdeadbeef00000000000000000000000000000002")

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
        Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0xdeadbeef00000000000000000000000000000000]
        + Op.PUSH3[0x249f0] + Op.CALL + Op.POP + Op.PUSH1[0x20] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.RETURNDATACOPY + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x0]
        + Op.SSTORE + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0xdeadbeef00000000000000000000000000000001]
        + Op.PUSH3[0x249f0] + Op.CALL + Op.POP + Op.PUSH1[0x20] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.RETURNDATACOPY + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x1]
        + Op.SSTORE + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0xdeadbeef00000000000000000000000000000002]
        + Op.PUSH3[0x249f0] + Op.CALL + Op.POP + Op.PUSH1[0x20] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.RETURNDATACOPY + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x2]
        + Op.SSTORE + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0xaaaaaaaa00000000000000000000000000000000]
        + Op.PUSH3[0x249f0] + Op.CALL + Op.POP + Op.PUSH1[0x20] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xdeadbeef00000000000000000000000000000000] + Op.PUSH3[0x249f0]
        + Op.CALL + Op.POP + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.RETURNDATACOPY + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x3] + Op.SSTORE
        + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0xdeadbeef00000000000000000000000000000001]
        + Op.PUSH3[0x249f0] + Op.CALL + Op.POP + Op.PUSH1[0x20] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.RETURNDATACOPY + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x4]
        + Op.SSTORE + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0xdeadbeef00000000000000000000000000000002]
        + Op.PUSH3[0x249f0] + Op.CALL + Op.POP + Op.PUSH1[0x20] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.RETURNDATACOPY + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x5]
        + Op.SSTORE + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH20[0xdeadbeef00000000000000000000000000000000] + Op.SELFDESTRUCT
        + Op.STOP
    ),
    )
    pre[callee_1] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH20[0xaaaaaaaa00000000000000000000000000000000] + Op.EXTCODEHASH
        + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.RETURN
        + Op.STOP
    ),
    )
    pre[callee_2] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH20[0xaaaaaaaa00000000000000000000000000000000] + Op.EXTCODESIZE
        + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.RETURN
        + Op.STOP
    ),
    )
    pre[callee_3] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH20[0xaaaaaaaa00000000000000000000000000000000] + Op.EXTCODESIZE
        + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xaaaaaaaa00000000000000000000000000000000] + Op.EXTCODECOPY
        + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.RETURN + Op.STOP
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


@pytest.mark.ported_from(
    ["tests/static/state_tests/stExtCodeHash/extCodeHashDeletedAccountCancunFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_ext_code_hash_deleted_account_cancun(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Get account A (aaaaaaaa00000000000000000000000000000000) code hash, code size, and code
Calls Account A's code which causes self destruction of A
Get account A codehash, code size and code
It is still getting the same values because selfdestruct is performed
at the end of transaction during state finalization stage.
Same as extCodeHashDeletedAccount test but with dynamic account suicide for Cancun
."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0x095e7baea6a6c7c4c2dfeb977efac326af552d87")
    callee = Address("0xbbbbbbbb00000000000000000000000000000000")
    callee_1 = Address("0xdeadbeef00000000000000000000000000000000")
    callee_2 = Address("0xdeadbeef00000000000000000000000000000001")
    callee_3 = Address("0xdeadbeef00000000000000000000000000000002")

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
        Op.PUSH1[0x49] + Op.DUP1 + Op.PUSH2[0x169] + Op.PUSH1[0x0] + Op.CODECOPY
        + Op.PUSH1[0x0] + Op.PUSH8[0xde0b6b3a7640000] + Op.CREATE + Op.POP
        + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0xdeadbeef00000000000000000000000000000000]
        + Op.PUSH3[0x249f0] + Op.CALL + Op.POP + Op.PUSH1[0x20] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.RETURNDATACOPY + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x0]
        + Op.SSTORE + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0xdeadbeef00000000000000000000000000000001]
        + Op.PUSH3[0x249f0] + Op.CALL + Op.POP + Op.PUSH1[0x20] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.RETURNDATACOPY + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x1]
        + Op.SSTORE + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0xdeadbeef00000000000000000000000000000002]
        + Op.PUSH3[0x249f0] + Op.CALL + Op.POP + Op.PUSH1[0x20] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.RETURNDATACOPY + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x2]
        + Op.SSTORE + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0xd2571607e241ecf590ed94b12d87c94babe36db6]
        + Op.PUSH3[0x249f0] + Op.CALL + Op.POP + Op.PUSH1[0x20] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xdeadbeef00000000000000000000000000000000] + Op.PUSH3[0x249f0]
        + Op.CALL + Op.POP + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.RETURNDATACOPY + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x3] + Op.SSTORE
        + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0xdeadbeef00000000000000000000000000000001]
        + Op.PUSH3[0x249f0] + Op.CALL + Op.POP + Op.PUSH1[0x20] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.RETURNDATACOPY + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x4]
        + Op.SSTORE + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0xdeadbeef00000000000000000000000000000002]
        + Op.PUSH3[0x249f0] + Op.CALL + Op.POP + Op.PUSH1[0x20] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.RETURNDATACOPY + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x5]
        + Op.SSTORE + Op.STOP + Op.INVALID + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xbbbbbbbb00000000000000000000000000000000] + Op.PUSH3[0x186a0]
        + Op.CALL + Op.POP + Op.PUSH1[0x17] + Op.DUP1 + Op.PUSH1[0x32] + Op.PUSH1[0x0]
        + Op.CODECOPY + Op.PUSH1[0x0] + Op.RETURN + Op.STOP + Op.INVALID
        + Op.PUSH20[0xdeadbeef00000000000000000000000000000000] + Op.SELFDESTRUCT
        + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP,
    )
    pre[callee_1] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH20[0xd2571607e241ecf590ed94b12d87c94babe36db6] + Op.EXTCODEHASH
        + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.RETURN
        + Op.STOP
    ),
    )
    pre[callee_2] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH20[0xd2571607e241ecf590ed94b12d87c94babe36db6] + Op.EXTCODESIZE
        + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.RETURN
        + Op.STOP
    ),
    )
    pre[callee_3] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH20[0xd2571607e241ecf590ed94b12d87c94babe36db6] + Op.EXTCODESIZE
        + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xd2571607e241ecf590ed94b12d87c94babe36db6] + Op.EXTCODECOPY
        + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.RETURN + Op.STOP
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
