"""
Ported from:
tests/static/state_tests/stStaticCall/static_ABAcalls0Filler.json

callee code:
    pc
    push1 0x01
    mstore
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0x7a365d98665a08e6ed6c1638c8ea6775fa649048
    push2 0xc350
    staticcall
    stop

callee_1 code:
    pc
    push1 0x01
    mstore
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0x718a83e869d6f4dea50a650b9825cbfe683bdf16
    push3 0x0186a0
    staticcall
    stop

callee_2 code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0xc54c4be163add3cc0efe5268a599a308dab12c74
    push2 0xc350
    staticcall
    push1 0x01
    add
    pc
    sstore
    stop

callee_3 code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0x9a95017e0dbf52bb87ddfda883b69d6188d574ca
    push3 0x0186a0
    staticcall
    pc
    sstore
    stop

contract code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    callvalue
    push1 0x00
    calldataload
    gas
    call
    push1 0x00
    sstore
    push1 0x01
    push1 0x01
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
    ["tests/static/state_tests/stStaticCall/static_ABAcalls0Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "000000000000000000000000c54c4be163add3cc0efe5268a599a308dab12c74",
        "0000000000000000000000007a365d98665a08e6ed6c1638c8ea6775fa649048",
    ],
    ids=['case0', 'case1'],
)
@pytest.mark.pre_alloc_mutable
def test_static_ab_acalls0(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xebaf50debf10e08302fe4280c32df010463ca297")
    contract = Address("0xfddb268f64fd5a90f618bbee0bd38e0c24b0a945")
    callee = Address("0x718a83e869d6f4dea50a650b9825cbfe683bdf16")
    callee_1 = Address("0x7a365d98665a08e6ed6c1638c8ea6775fa649048")
    callee_2 = Address("0x9a95017e0dbf52bb87ddfda883b69d6188d574ca")
    callee_3 = Address("0xc54c4be163add3cc0efe5268a599a308dab12c74")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[callee] = Account(
        balance=23,
        nonce=0,
        code=(
        Op.PC + Op.PUSH1[0x1] + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x7a365d98665a08e6ed6c1638c8ea6775fa649048] + Op.PUSH2[0xc350]
        + Op.STATICCALL + Op.STOP
    ),
    )
    pre[callee_1] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PC + Op.PUSH1[0x1] + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x718a83e869d6f4dea50a650b9825cbfe683bdf16] + Op.PUSH3[0x186a0]
        + Op.STATICCALL + Op.STOP
    ),
    )
    pre[callee_2] = Account(
        balance=23,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xc54c4be163add3cc0efe5268a599a308dab12c74] + Op.PUSH2[0xc350]
        + Op.STATICCALL + Op.PUSH1[0x1] + Op.ADD + Op.PC + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_3] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x9a95017e0dbf52bb87ddfda883b69d6188d574ca] + Op.PUSH3[0x186a0]
        + Op.STATICCALL + Op.PC + Op.SSTORE + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.CALLVALUE
        + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.GAS + Op.CALL + Op.PUSH1[0x0]
        + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP
    ),
    )

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
