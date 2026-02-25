"""
callcode happen to a contract that is dynamically created from within the contract (to itself)

Ported from:
tests/static/state_tests/stCallCodes/callcodeDynamicCode2SelfCallFiller.json

callee code:
    push1 0x46
    dup1
    push1 0x27
    push1 0x00
    codecopy
    push1 0x00
    push1 0x00
    create
    push1 0x0a
    sstore
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push1 0x00
    push1 0x0a
    sload
    push3 0x0186a0
    callcode
    push1 0x0b
    ... (35 more instructions)

contract code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    calldataload
    push3 0x0c3500
    call
    stop

callee_1 code:
    push32 0x604060006040600060007313136008b64ff592819b2fa6d43f2835c452020e62
    push1 0x00
    mstore
    push32 0x0186a0f2600b5533600c55000000000000000000000000000000000000000000
    push1 0x20
    mstore
    push1 0x40
    push1 0x00
    push1 0x01
    create
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
    ["tests/static/state_tests/stCallCodes/callcodeDynamicCode2SelfCallFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "000000000000000000000000a000000000000000000000000000000000000000",
        "0000000000000000000000001000000000000000000000000000000000000000",
    ],
    ids=['case0', 'case1'],
)
@pytest.mark.pre_alloc_mutable
def test_callcode_dynamic_code2_self_call(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """callcode happen to a contract that is dynamically created from within the contract (to itself)."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0x1100000000000000000000000000000000000000")
    callee = Address("0x1000000000000000000000000000000000000000")
    callee_1 = Address("0xa000000000000000000000000000000000000000")

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
        Op.PUSH1[0x46] + Op.DUP1 + Op.PUSH1[0x27] + Op.PUSH1[0x0] + Op.CODECOPY
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.CREATE + Op.PUSH1[0xa] + Op.SSTORE
        + Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0xa] + Op.SLOAD + Op.PUSH3[0x186a0] + Op.CALLCODE
        + Op.PUSH1[0xb] + Op.SSTORE + Op.STOP + Op.INVALID + Op.PUSH1[0x40]
        + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x13136008b64ff592819b2fa6d43f2835c452020e] + Op.PUSH3[0x186a0]
        + Op.CALLCODE + Op.PUSH1[0x7a] + Op.SSTORE + Op.PUSH1[0x12] + Op.DUP1
        + Op.PUSH1[0x34] + Op.PUSH1[0x0] + Op.CODECOPY + Op.PUSH1[0x0] + Op.RETURN
        + Op.STOP + Op.INVALID + Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE
        + Op.ADDRESS + Op.PUSH1[0x14] + Op.SSTORE + Op.ORIGIN + Op.PUSH1[0x15]
        + Op.SSTORE + Op.CALLER + Op.PUSH1[0x16] + Op.SSTORE + Op.STOP
    ),
    )
    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH3[0xc3500]
        + Op.CALL + Op.STOP
    ),
    )
    pre[callee_1] = Account(
        balance=0x2710,
        nonce=0,
        code=(
        Op.PUSH32[0x604060006040600060007313136008b64ff592819b2fa6d43f2835c452020e62]
        + Op.PUSH1[0x0] + Op.MSTORE
        + Op.PUSH32[0x186a0f2600b5533600c55000000000000000000000000000000000000000000]
        + Op.PUSH1[0x20] + Op.MSTORE + Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x1]
        + Op.CREATE + Op.STOP
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
