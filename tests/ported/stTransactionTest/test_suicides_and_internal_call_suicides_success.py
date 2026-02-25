"""
Ported from:
tests/static/state_tests/stTransactionTest/SuicidesAndInternalCallSuicidesSuccessFiller.json

callee code:
    push1 0x01
    selfdestruct
    stop

contract code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x01
    push1 0x00
    push1 0x00
    calldataload
    call
    pop
    push1 0x00
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
    ["tests/static/state_tests/stTransactionTest/SuicidesAndInternalCallSuicidesSuccessFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "00000000000000000000000000000000000000000000000000000000000055f0",
        "000000000000000000000000000000000000000000000000000000000000aaf0",
    ],
    ids=['case0', 'case1'],
)
@pytest.mark.pre_alloc_mutable
def test_suicides_and_internal_call_suicides_success(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    callee = Address("0x0000000000000000000000000000000000000000")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[callee] = Account(balance=0, nonce=0, code=Op.PUSH1[0x1] + Op.SELFDESTRUCT + Op.STOP)
    pre[sender] = Account(balance=0xaba9500, nonce=0)
    pre[contract] = Account(
        balance=1000,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.CALL
        + Op.POP + Op.PUSH1[0x0] + Op.SELFDESTRUCT + Op.STOP
    ),
    )

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
        ),
        to=contract,
        data=tx_data,
        gas_limit=150000,
        gas_price=10,
        nonce=0,
        value=10,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
