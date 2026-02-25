"""
transaction to B | B call to A | A delegatecall/callcode to C (C has selfdestruct) | A selfdestructed. returned to B. now we could check extcodehash of A (in account B code)

Ported from:
tests/static/state_tests/stExtCodeHash/extCodeHashSubcallSuicideFiller.yml

callee code:
    push1 0x20
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0xc000000000000000000000000000000000000000
    push3 0x055730
    callcode
    stop

contract code:
    push20 0xa000000000000000000000000000000000000000
    extcodehash
    push1 0x01
    sstore
    push20 0xa000000000000000000000000000000000000000
    extcodesize
    push1 0x02
    sstore
    push1 0x20
    push1 0x00
    push1 0x00
    push20 0xa000000000000000000000000000000000000000
    extcodecopy
    push1 0x00
    mload
    push1 0x03
    sstore
    push1 0x20
    push1 0x00
    push1 0x00
    ... (34 more instructions)

callee_1 code:
    push20 0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b
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
    ["tests/static/state_tests/stExtCodeHash/extCodeHashSubcallSuicideFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_ext_code_hash_subcall_suicide(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """transaction to B | B call to A | A delegatecall/callcode to C (C has selfdestruct) | A selfdestructed. returned to B. now we could check extcodehash of A (in account B code)."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0xb000000000000000000000000000000000000000")
    callee = Address("0xa000000000000000000000000000000000000000")
    callee_1 = Address("0xc000000000000000000000000000000000000000")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[callee] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0xc000000000000000000000000000000000000000]
        + Op.PUSH3[0x55730] + Op.CALLCODE + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH20[0xa000000000000000000000000000000000000000] + Op.EXTCODEHASH
        + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH20[0xa000000000000000000000000000000000000000] + Op.EXTCODESIZE
        + Op.PUSH1[0x2] + Op.SSTORE + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xa000000000000000000000000000000000000000] + Op.EXTCODECOPY
        + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x3] + Op.SSTORE + Op.PUSH1[0x20]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xa000000000000000000000000000000000000000] + Op.PUSH3[0x55730]
        + Op.CALL + Op.POP + Op.PUSH20[0xa000000000000000000000000000000000000000]
        + Op.EXTCODEHASH + Op.PUSH1[0x4] + Op.SSTORE
        + Op.PUSH20[0xa000000000000000000000000000000000000000] + Op.EXTCODESIZE
        + Op.PUSH1[0x5] + Op.SSTORE + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xa000000000000000000000000000000000000000] + Op.EXTCODECOPY
        + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x6] + Op.SSTORE + Op.PUSH1[0x20]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xa000000000000000000000000000000000000000] + Op.PUSH3[0x55730]
        + Op.CALL + Op.PUSH1[0x7] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_1] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH20[0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b] + Op.SELFDESTRUCT
        + Op.STOP
    ),
    )

    tx = Transaction(
        secret_key=Hash(
            "0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
        ),
        to=contract,
        data=b"",
        gas_limit=500000,
        gas_price=10,
        nonce=0,
        value=1,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
