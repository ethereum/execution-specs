"""
Danno Ferrin danno.ferrin@gmail.com

Ported from:
tests/static/state_tests/stEIP150Specific/Transaction64Rule_integerBoundariesFiller.yml

callee code:
    push1 0x00
    push1 0xff
    stop

contract code:
    gas
    push1 0x20
    push1 0x00
    dup2
    dup2
    push2 0x1000
    dup2
    calldataload
    dup4
    dup4
    dup1
    dup1
    dup1
    dup7
    dup7
    call
    pop
    dup7
    gas
    lt
    ... (36 more instructions)
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
    ["tests/static/state_tests/stEIP150Specific/Transaction64Rule_integerBoundariesFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "000000000000000000000000000000007fffffffffffffffffffffffffffffff",
        "0000000000000000000000000000000000000000000000000000000000007fff",
        "7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
        "000000000000000000000000000000000000000000000000000000007fffffff",
        "0000000000000000000000000000000000000000000000007fffffffffffffff",
        "000000000000000000000000000000000000000000000000000000000000007f",
        "000000000000000000000000000000008fffffffffffffffffffffffffffffff",
        "0000000000000000000000000000000000000000000000000000000000008fff",
        "8fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
        "000000000000000000000000000000000000000000000000000000008fffffff",
        "0000000000000000000000000000000000000000000000008fffffffffffffff",
        "000000000000000000000000000000000000000000000000000000000000008f",
    ],
    ids=['case0', 'case1', 'case2', 'case3', 'case4', 'case5', 'case6', 'case7', 'case8', 'case9', 'case10', 'case11'],
)
@pytest.mark.pre_alloc_mutable
def test_transaction64_rule_integer_boundaries(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Danno Ferrin danno.ferrin@gmail.com."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0x000000000000000000000000000000000000c0de")
    callee = Address("0x0000000000000000000000000000000000001000")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=Op.PUSH1[0x0] + Op.PUSH1[0xff] + Op.STOP,
    )
    pre[contract] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.GAS + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.DUP2 + Op.DUP2
        + Op.PUSH2[0x1000] + Op.DUP2 + Op.CALLDATALOAD + Op.DUP4 + Op.DUP4 + Op.DUP1
        + Op.DUP1 + Op.DUP1 + Op.DUP7 + Op.DUP7 + Op.CALL + Op.POP + Op.DUP7 + Op.GAS
        + Op.LT + Op.DUP4 + Op.SSTORE + Op.DUP4 + Op.DUP4 + Op.DUP1 + Op.DUP1
        + Op.DUP1 + Op.DUP7 + Op.DUP7 + Op.CALLCODE + Op.POP + Op.DUP7 + Op.GAS
        + Op.LT + Op.PUSH1[0x1] + Op.SSTORE + Op.DUP4 + Op.DUP4 + Op.DUP2 + Op.DUP2
        + Op.DUP6 + Op.DUP6 + Op.DELEGATECALL + Op.POP + Op.DUP7 + Op.GAS + Op.LT
        + Op.PUSH1[0x2] + Op.SSTORE + Op.STATICCALL + Op.POP + Op.GAS + Op.LT
        + Op.PUSH1[0x3] + Op.SSTORE + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0x10000000000000000, nonce=0)

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
        ),
        to=contract,
        data=tx_data,
        gas_limit=800000,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
