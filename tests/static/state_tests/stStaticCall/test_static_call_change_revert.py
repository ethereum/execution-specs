"""
Ported from:
tests/static/state_tests/stStaticCall/static_callChangeRevertFiller.json

callee code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x01
    push20 0x47c4ed3d93429cb8304737e2327b522e8928c9f3
    push3 0x0186a0
    call
    push1 0x00
    sstore
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0x47c4ed3d93429cb8304737e2327b522e8928c9f3
    push3 0x0186a0
    staticcall
    push1 0x01
    sstore
    push1 0x00
    ... (10 more instructions)

callee_1 code:
    push1 0x01
    push1 0x01
    mstore
    push1 0x01
    sload
    push1 0x01
    sstore
    stop

contract code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    calldataload
    push3 0x055730
    call
    stop

callee_2 code:
    push1 0x01
    push1 0x01
    mstore
    stop

callee_3 code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x01
    push20 0xc031fc0aa7b61a5d7d962afee8838dec6948abb7
    push3 0x0186a0
    call
    push1 0x00
    sstore
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0xc031fc0aa7b61a5d7d962afee8838dec6948abb7
    push3 0x0186a0
    staticcall
    push1 0x01
    sstore
    push1 0x00
    ... (10 more instructions)

callee_4 code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x01
    push20 0xc031fc0aa7b61a5d7d962afee8838dec6948abb7
    push3 0x0186a0
    call
    push1 0x00
    sstore
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0xc031fc0aa7b61a5d7d962afee8838dec6948abb7
    push3 0x0186a0
    staticcall
    push1 0x01
    sstore
    push1 0x00
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
    ["tests/static/state_tests/stStaticCall/static_callChangeRevertFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "000000000000000000000000e6f1fdaa1c99007971c641e10af3a8fac0b641c8",
        "000000000000000000000000ea22ec955ac71d8e4380541212bd20818d704567",
        "0000000000000000000000002c004389edaae817e664b6d660f46735756b56d3",
    ],
    ids=['case0', 'case1', 'case2'],
)
@pytest.mark.pre_alloc_mutable
def test_static_call_change_revert(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xebaf50debf10e08302fe4280c32df010463ca297")
    contract = Address("0x492bb18adce7da2bed3592742fb4e3df9086fb4c")
    callee = Address("0x2c004389edaae817e664b6d660f46735756b56d3")
    callee_1 = Address("0x47c4ed3d93429cb8304737e2327b522e8928c9f3")
    callee_2 = Address("0xc031fc0aa7b61a5d7d962afee8838dec6948abb7")
    callee_3 = Address("0xe6f1fdaa1c99007971c641e10af3a8fac0b641c8")
    callee_4 = Address("0xea22ec955ac71d8e4380541212bd20818d704567")

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
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x1] + Op.PUSH20[0x47c4ed3d93429cb8304737e2327b522e8928c9f3]
        + Op.PUSH3[0x186a0] + Op.CALL + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x47c4ed3d93429cb8304737e2327b522e8928c9f3] + Op.PUSH3[0x186a0]
        + Op.STATICCALL + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x1]
        + Op.PUSH20[0x47c4ed3d93429cb8304737e2327b522e8928c9f3] + Op.PUSH3[0x186a0]
        + Op.CALL + Op.PUSH1[0x2] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_1] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.MSTORE + Op.PUSH1[0x1] + Op.SLOAD
        + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP
    ),
    )
    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH3[0x55730]
        + Op.CALL + Op.STOP
    ),
    )
    pre[callee_2] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.MSTORE + Op.STOP,
    )
    pre[callee_3] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x1] + Op.PUSH20[0xc031fc0aa7b61a5d7d962afee8838dec6948abb7]
        + Op.PUSH3[0x186a0] + Op.CALL + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xc031fc0aa7b61a5d7d962afee8838dec6948abb7] + Op.PUSH3[0x186a0]
        + Op.STATICCALL + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x1]
        + Op.PUSH20[0xc031fc0aa7b61a5d7d962afee8838dec6948abb7] + Op.PUSH3[0x186a0]
        + Op.CALL + Op.PUSH1[0x2] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_4] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x1] + Op.PUSH20[0xc031fc0aa7b61a5d7d962afee8838dec6948abb7]
        + Op.PUSH3[0x186a0] + Op.CALL + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xc031fc0aa7b61a5d7d962afee8838dec6948abb7] + Op.PUSH3[0x186a0]
        + Op.STATICCALL + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x1]
        + Op.PUSH20[0xc031fc0aa7b61a5d7d962afee8838dec6948abb7] + Op.PUSH3[0x186a0]
        + Op.CALL + Op.PUSH1[0x2] + Op.SSTORE + Op.JUMPDEST + Op.PUSH2[0xc350]
        + Op.PUSH1[0x80] + Op.MLOAD + Op.LT + Op.ISZERO + Op.PUSH1[0x8f] + Op.JUMPI
        + Op.PUSH1[0x1] + Op.EXTCODESIZE + Op.POP + Op.PUSH1[0x1] + Op.PUSH1[0x80]
        + Op.MLOAD + Op.ADD + Op.PUSH1[0x80] + Op.MSTORE + Op.PUSH1[0x73] + Op.JUMP
        + Op.JUMPDEST + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0xe04d1ac7ddda0c98397d56a0b501e960d4cd325a39286919ac23c1a07009a869"
        ),
        to=contract,
        data=tx_data,
        gas_limit=1000000,
        gas_price=10,
        nonce=0,
        value=100000,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
