"""
Ported from:
tests/static/state_tests/stArgsZeroOneBalance/calldatacopyNonConstFiller.yml

contract code:
    push20 0x444c2681920e1105c9104fb32249ddbb41cba4a0
    balance
    push20 0x444c2681920e1105c9104fb32249ddbb41cba4a0
    balance
    push20 0x444c2681920e1105c9104fb32249ddbb41cba4a0
    balance
    calldatacopy
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
    ["tests/static/state_tests/stArgsZeroOneBalance/calldatacopyNonConstFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, tx_value",
    [
        ("", 0),
        ("", 1),
        ("11223344", 0),
        ("11223344", 1),
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_calldatacopy_non_const(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    tx_value: int,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0x2e3d0156d2b99a6eacba540c55f423c8f5a33143")
    contract = Address("0x444c2681920e1105c9104fb32249ddbb41cba4a0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH20[0x444c2681920e1105c9104fb32249ddbb41cba4a0] + Op.BALANCE
        + Op.PUSH20[0x444c2681920e1105c9104fb32249ddbb41cba4a0] + Op.BALANCE
        + Op.PUSH20[0x444c2681920e1105c9104fb32249ddbb41cba4a0] + Op.BALANCE
        + Op.CALLDATACOPY + Op.STOP
    ),
    )

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0xb1f4cbc3a50042184425a6f9e996d0910f7ba879457ce5dac5c71e498ad3c005"
        ),
        to=contract,
        data=tx_data,
        gas_limit=400000,
        gas_price=10,
        nonce=0,
        value=tx_value,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
