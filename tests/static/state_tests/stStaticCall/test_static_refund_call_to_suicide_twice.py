"""
Ported from:
tests/static/state_tests/stStaticCall/static_refund_CallToSuicideTwiceFiller.json

contract code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0x9dea1ad5123f3d8b91cfc830b1c602597883e97c
    push1 0x00
    calldataload
    staticcall
    push1 0x00
    sstore
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0x9dea1ad5123f3d8b91cfc830b1c602597883e97c
    push1 0x00
    calldataload
    call
    stop

callee code:
    push20 0x75db2708826b7d5e8cd45002f9ae23c830c31efd
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
    ["tests/static/state_tests/stStaticCall/static_refund_CallToSuicideTwiceFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "00000000000000000000000000000000000000000000000000000000000001f4",
        "0000000000000000000000000000000000000000000000000000000000010000",
    ],
    ids=['case0', 'case1'],
)
@pytest.mark.pre_alloc_mutable
def test_static_refund_call_to_suicide_twice(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xcfff6235759a3209f2cb8e3e2dd6ea4c2b96e325")
    contract = Address("0x75db2708826b7d5e8cd45002f9ae23c830c31efd")
    callee = Address("0x9dea1ad5123f3d8b91cfc830b1c602597883e97c")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x9dea1ad5123f3d8b91cfc830b1c602597883e97c] + Op.PUSH1[0x0]
        + Op.CALLDATALOAD + Op.STATICCALL + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x9dea1ad5123f3d8b91cfc830b1c602597883e97c] + Op.PUSH1[0x0]
        + Op.CALLDATALOAD + Op.CALL + Op.STOP
    ),
        storage={0x1: 0x1},
    )
    pre[callee] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH20[0x75db2708826b7d5e8cd45002f9ae23c830c31efd] + Op.SELFDESTRUCT
        + Op.STOP
    ),
        storage={0x1: 0x1},
    )
    pre[sender] = Account(balance=0x174876e800, nonce=0)

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0x5b7b8efb6d003cd481e408d8759a25adc79955092f1a380d8f8b57346c1d1342"
        ),
        to=contract,
        data=tx_data,
        gas_limit=10000000,
        gas_price=10,
        nonce=0,
        value=10,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
