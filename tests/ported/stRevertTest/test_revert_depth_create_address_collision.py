"""
Ported from:
tests/static/state_tests/stRevertTest/RevertDepthCreateAddressCollisionFiller.json

contract code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0xb1b49241a4ecf7860872e686090781c906b1b437
    push1 0x00
    calldataload
    call
    push1 0x01
    sstore
    push1 0x0c
    push1 0x04
    sstore
    stop

callee code:
    push1 0x08
    push1 0x02
    sstore
    push1 0x00
    push1 0x00
    push1 0x00
    create
    pop
    push1 0x0c
    push1 0x03
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
    ["tests/static/state_tests/stRevertTest/RevertDepthCreateAddressCollisionFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, tx_gas_limit, tx_value",
    [
        ("000000000000000000000000000000000000000000000000000000000000ea60", 110000, 1),
        ("000000000000000000000000000000000000000000000000000000000000ea60", 110000, 0),
        ("000000000000000000000000000000000000000000000000000000000000ea60", 160000, 1),
        ("000000000000000000000000000000000000000000000000000000000000ea60", 160000, 0),
        ("000000000000000000000000000000000000000000000000000000000001ea60", 110000, 1),
        ("000000000000000000000000000000000000000000000000000000000001ea60", 110000, 0),
        ("000000000000000000000000000000000000000000000000000000000001ea60", 160000, 1),
        ("000000000000000000000000000000000000000000000000000000000001ea60", 160000, 0),
    ],
    ids=['case0', 'case1', 'case2', 'case3', 'case4', 'case5', 'case6', 'case7'],
)
@pytest.mark.pre_alloc_mutable
def test_revert_depth_create_address_collision(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    tx_gas_limit: int,
    tx_value: int,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xfaa10b404ab607779993c016cd5da73ae1f29d7e")
    contract = Address("0x97e33a176b7c8d61b356d1c170ac2119d28867df")
    callee = Address("0xb1b49241a4ecf7860872e686090781c906b1b437")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[contract] = Account(
        balance=5,
        nonce=54,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xb1b49241a4ecf7860872e686090781c906b1b437] + Op.PUSH1[0x0]
        + Op.CALLDATALOAD + Op.CALL + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0xc]
        + Op.PUSH1[0x4] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x8] + Op.PUSH1[0x2] + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.CREATE + Op.POP + Op.PUSH1[0xc] + Op.PUSH1[0x3]
        + Op.SSTORE + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xe8d4a51000, nonce=0)

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0x4f31b3206fbf0e0e598b9b1a7d8ac86302a0ff1d8930738f1bebae9b67173e52"
        ),
        to=contract,
        data=tx_data,
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=0,
        value=tx_value,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
