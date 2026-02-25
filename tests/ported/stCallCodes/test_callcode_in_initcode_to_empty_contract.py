"""
callcode inside create contract init to non-existent contract

Ported from:
tests/static/state_tests/stCallCodes/callcodeInInitcodeToEmptyContractFiller.json

callee code:
    push1 0x2d
    dup1
    push1 0x0f
    push1 0x00
    codecopy
    push1 0x00
    push1 0x00
    create
    stop
    invalid
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x01
    push20 0x1000000000000000000000000000000000000001
    push3 0x07a120
    callcode
    push1 0x01
    sstore
    ... (4 more instructions)

contract code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    calldataload
    push3 0x0493e0
    call
    stop

callee_1 code:
    push1 0x00
    push1 0x2d
    dup1
    push1 0x11
    push1 0x00
    codecopy
    push1 0x00
    push1 0x00
    create2
    stop
    invalid
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x01
    push20 0x1000000000000000000000000000000000000001
    push3 0x07a120
    callcode
    push1 0x01
    ... (5 more instructions)
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
    ["tests/static/state_tests/stCallCodes/callcodeInInitcodeToEmptyContractFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "0000000000000000000000001000000000000000000000000000000000000000",
        "0000000000000000000000002000000000000000000000000000000000000000",
    ],
    ids=['case0', 'case1'],
)
@pytest.mark.pre_alloc_mutable
def test_callcode_in_initcode_to_empty_contract(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """callcode inside create contract init to non-existent contract."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0x1100000000000000000000000000000000000000")
    callee = Address("0x1000000000000000000000000000000000000000")
    callee_1 = Address("0x2000000000000000000000000000000000000000")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[callee] = Account(
        balance=0x2710,
        nonce=0,
        code=(
        Op.PUSH1[0x2d] + Op.DUP1 + Op.PUSH1[0xf] + Op.PUSH1[0x0] + Op.CODECOPY
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.CREATE + Op.STOP + Op.INVALID
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x1] + Op.PUSH20[0x1000000000000000000000000000000000000001]
        + Op.PUSH3[0x7a120] + Op.CALLCODE + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SSTORE + Op.STOP
    ),
    )
    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH3[0x493e0]
        + Op.CALL + Op.STOP
    ),
    )
    pre[callee_1] = Account(
        balance=0x2710,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x2d] + Op.DUP1 + Op.PUSH1[0x11] + Op.PUSH1[0x0]
        + Op.CODECOPY + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.CREATE2 + Op.STOP
        + Op.INVALID + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x1] + Op.PUSH20[0x1000000000000000000000000000000000000001]
        + Op.PUSH3[0x7a120] + Op.CALLCODE + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SSTORE + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0x2386f26fc10000, nonce=0)

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
        ),
        to=contract,
        data=tx_data,
        gas_limit=1453081,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
