"""
Ported from:
tests/static/state_tests/stSolidityTest/TestStoreGasPricesFiller.json

contract code:
    push29 0x0100000000000000000000000000000000000000000000000000000000
    push1 0x00
    calldataload
    div
    push4 0xc0406226
    dup2
    eq
    push1 0x2d
    jumpi
    stop
    jumpdest
    push1 0x33
    push1 0x3d
    jump
    jumpdest
    dup1
    push1 0x00
    mstore
    push1 0x20
    push1 0x00
    ... (78 more instructions)
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
    ["tests/static/state_tests/stSolidityTest/TestStoreGasPricesFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.pre_alloc_mutable
def test_test_store_gas_prices(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0x4a609d84854dbf90b31517f914f50ad91f02a9ae")
    contract = Address("0xfe58f48415dcf9d527f770e3148b769a76ef83f1")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    pre[sender] = Account(balance=0x746a528800, nonce=0)
    pre[contract] = Account(
        balance=0x186a0,
        nonce=0,
        code=(
        Op.PUSH29[0x100000000000000000000000000000000000000000000000000000000]
        + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.DIV + Op.PUSH4[0xc0406226] + Op.DUP2
        + Op.EQ + Op.PUSH1[0x2d] + Op.JUMPI + Op.STOP + Op.JUMPDEST + Op.PUSH1[0x33]
        + Op.PUSH1[0x3d] + Op.JUMP + Op.JUMPDEST + Op.DUP1 + Op.PUSH1[0x0] + Op.MSTORE
        + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.RETURN + Op.JUMPDEST + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.GAS + Op.PUSH1[0x1] + Op.PUSH1[0x20] + Op.SSTORE
        + Op.SWAP1 + Op.POP + Op.GAS + Op.DUP2 + Op.SUB + Op.PUSH1[0x0] + Op.SSTORE
        + Op.GAS + Op.PUSH1[0x2] + Op.PUSH1[0x20] + Op.SSTORE + Op.SWAP1 + Op.POP
        + Op.GAS + Op.DUP2 + Op.SUB + Op.PUSH1[0x1] + Op.SSTORE + Op.GAS
        + Op.PUSH1[0x2] + Op.PUSH1[0x20] + Op.SSTORE + Op.SWAP1 + Op.POP + Op.GAS
        + Op.DUP2 + Op.SUB + Op.PUSH1[0x2] + Op.SSTORE + Op.GAS
        + Op.PUSH6[0x168aa8d53fe6] + Op.PUSH1[0x20] + Op.SSTORE + Op.SWAP1 + Op.POP
        + Op.GAS + Op.DUP2 + Op.SUB + Op.PUSH1[0x3] + Op.SSTORE + Op.GAS
        + Op.PUSH1[0x2] + Op.PUSH1[0x20] + Op.SSTORE + Op.SWAP1 + Op.POP + Op.GAS
        + Op.DUP2 + Op.SUB + Op.PUSH1[0x4] + Op.SSTORE + Op.GAS + Op.PUSH1[0x0]
        + Op.PUSH1[0x20] + Op.SSTORE + Op.SWAP1 + Op.POP + Op.GAS + Op.DUP2 + Op.SUB
        + Op.PUSH1[0x5] + Op.SSTORE + Op.GAS + Op.POP + Op.PUSH1[0x1] + Op.SWAP3
        + Op.SWAP2 + Op.POP + Op.POP + Op.JUMP
    ),
    )

    tx = Transaction(
        secret_key=Hash(
            "0x185fbea9f643c40e33475353b07fa51d0695ca94789492166b67d60fdb6ef7fb"
        ),
        to=contract,
        data=bytes.fromhex("c0406226"),
        gas_limit=35000000,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
