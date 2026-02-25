"""
Ported from:
tests/static/state_tests/stRefundTest/refund_CallToSuicideNoStorageFiller.json

callee code:
    push20 0x5be4b33890f720eff72be0019b122e0ff75cb937
    selfdestruct
    stop

contract code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0x4ff65047ce9c85f968689e4369c10003026a41a9
    push1 0x00
    calldataload
    call
    push1 0x00
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
    ["tests/static/state_tests/stRefundTest/refund_CallToSuicideNoStorageFiller.json"],
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
def test_refund_call_to_suicide_no_storage(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xd96ed4431b417993ab4f4d4a656959d13c66e1dc")
    contract = Address("0x5be4b33890f720eff72be0019b122e0ff75cb937")
    callee = Address("0x4ff65047ce9c85f968689e4369c10003026a41a9")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH20[0x5be4b33890f720eff72be0019b122e0ff75cb937] + Op.SELFDESTRUCT
        + Op.STOP
    ),
    )
    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0x4ff65047ce9c85f968689e4369c10003026a41a9]
        + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.CALL + Op.PUSH1[0x0] + Op.SSTORE
        + Op.STOP
    ),
        storage={0x1: 0x1},
    )
    pre[sender] = Account(balance=0x2540be400, nonce=0)

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0x6f0117d3e9c684c7d6e1e6b79dc3880da2bebe77c765b171c062fdffd38a673f"
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
