"""
Ported from:
tests/static/state_tests/stEIP158Specific/EXP_EmptyFiller.json

contract code:
    gas
    push1 0x00
    mstore
    push1 0x0c
    push1 0x00
    exp
    push1 0x01
    sstore
    gas
    push1 0x00
    mload
    sub
    push1 0x02
    sstore
    gas
    push1 0x00
    mstore
    push1 0x00
    push1 0x0c
    exp
    ... (93 more instructions)
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
    ["tests/static/state_tests/stEIP158Specific/EXP_EmptyFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_exp_empty(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xfaa10b404ab607779993c016cd5da73ae1f29d7e")
    contract = Address("0x8a3c9879fc69c8c45c1201c27da63312e9e9f6fe")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.GAS + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0xc] + Op.PUSH1[0x0] + Op.EXP
        + Op.PUSH1[0x1] + Op.SSTORE + Op.GAS + Op.PUSH1[0x0] + Op.MLOAD + Op.SUB
        + Op.PUSH1[0x2] + Op.SSTORE + Op.GAS + Op.PUSH1[0x0] + Op.MSTORE
        + Op.PUSH1[0x0] + Op.PUSH1[0xc] + Op.EXP + Op.PUSH1[0x3] + Op.SSTORE + Op.GAS
        + Op.PUSH1[0x0] + Op.MLOAD + Op.SUB + Op.PUSH1[0x4] + Op.SSTORE + Op.GAS
        + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH8[0xffffffffffffffff] + Op.PUSH1[0x0]
        + Op.EXP + Op.PUSH1[0x5] + Op.SSTORE + Op.GAS + Op.PUSH1[0x0] + Op.MLOAD
        + Op.SUB + Op.PUSH1[0x6] + Op.SSTORE + Op.GAS + Op.PUSH1[0x0] + Op.MSTORE
        + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x0] + Op.EXP
        + Op.PUSH1[0x7] + Op.SSTORE + Op.GAS + Op.PUSH1[0x0] + Op.MLOAD + Op.SUB
        + Op.PUSH1[0x8] + Op.SSTORE + Op.GAS + Op.PUSH1[0x0] + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
        + Op.PUSH1[0x0] + Op.EXP + Op.PUSH1[0x9] + Op.SSTORE + Op.GAS + Op.PUSH1[0x0]
        + Op.MLOAD + Op.SUB + Op.PUSH1[0xa] + Op.SSTORE + Op.GAS + Op.PUSH1[0x0]
        + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH8[0xffffffffffffffff] + Op.EXP
        + Op.PUSH1[0xb] + Op.SSTORE + Op.GAS + Op.PUSH1[0x0] + Op.MLOAD + Op.SUB
        + Op.PUSH1[0xc] + Op.SSTORE + Op.GAS + Op.PUSH1[0x0] + Op.MSTORE
        + Op.PUSH1[0x0] + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.EXP
        + Op.PUSH1[0xd] + Op.SSTORE + Op.GAS + Op.PUSH1[0x0] + Op.MLOAD + Op.SUB
        + Op.PUSH1[0xe] + Op.SSTORE + Op.GAS + Op.PUSH1[0x0] + Op.MSTORE
        + Op.PUSH1[0x0]
        + Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
        + Op.EXP + Op.PUSH1[0xf] + Op.SSTORE + Op.GAS + Op.PUSH1[0x0] + Op.MLOAD
        + Op.SUB + Op.PUSH1[0x64] + Op.SSTORE + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xe8d4a51000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x4f31b3206fbf0e0e598b9b1a7d8ac86302a0ff1d8930738f1bebae9b67173e52"
        ),
        to=contract,
        data=b"",
        gas_limit=600000,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
