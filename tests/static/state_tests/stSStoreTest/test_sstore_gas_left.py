"""
Checks EIP-1706/EIP-2200 out of gas requirement for non-mutating SSTOREs.

Ported from:
tests/static/state_tests/stSStoreTest/sstore_gasLeftFiller.json

contract code:
    push1 0x01
    push1 0x01
    sstore
    stop

callee_1 code:
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
    ["tests/static/state_tests/stSStoreTest/sstore_gasLeftFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "6000600060006000600073b0409d84ab61455cb8bec14b94f635146ab55613610901f115604b5760006000600060006000734092b3905cfea2485ea53222f41eb26e67587802617530f1505b00",
        "6000600060006000600073b0409d84ab61455cb8bec14b94f635146ab55613610902f115604b5760006000600060006000734092b3905cfea2485ea53222f41eb26e67587802617530f1505b00",
        "6000600060006000600073b0409d84ab61455cb8bec14b94f635146ab55613610903f115604b5760006000600060006000734092b3905cfea2485ea53222f41eb26e67587802617530f1505b00",
        "60016001556000600060006000600073b0409d84ab61455cb8bec14b94f635146ab55613610901f21560505760006000600060006000734092b3905cfea2485ea53222f41eb26e67587802617530f1505b00",
        "60016001556000600060006000600073b0409d84ab61455cb8bec14b94f635146ab55613610902f21560505760006000600060006000734092b3905cfea2485ea53222f41eb26e67587802617530f1505b00",
        "60016001556000600060006000600073b0409d84ab61455cb8bec14b94f635146ab55613610903f21560505760006000600060006000734092b3905cfea2485ea53222f41eb26e67587802617530f1505b00",
        "6001600155600060006000600073b0409d84ab61455cb8bec14b94f635146ab55613610901f415604e5760006000600060006000734092b3905cfea2485ea53222f41eb26e67587802617530f1505b00",
        "6001600155600060006000600073b0409d84ab61455cb8bec14b94f635146ab55613610902f415604e5760006000600060006000734092b3905cfea2485ea53222f41eb26e67587802617530f1505b00",
        "6001600155600060006000600073b0409d84ab61455cb8bec14b94f635146ab55613610903f415604e5760006000600060006000734092b3905cfea2485ea53222f41eb26e67587802617530f1505b00",
    ],
    ids=['case0', 'case1', 'case2', 'case3', 'case4', 'case5', 'case6', 'case7', 'case8'],
)
@pytest.mark.pre_alloc_mutable
def test_sstore_gas_left(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Checks EIP-1706/EIP-2200 out of gas requirement for non-mutating SSTOREs.."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xfaa10b404ab607779993c016cd5da73ae1f29d7e")
    contract = Address("0x4092b3905cfea2485ea53222f41eb26e67587802")
    callee_1 = Address("0xb0409d84ab61455cb8bec14b94f635146ab55613")

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
        code=Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP,
    )
    pre[callee_1] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP,
        storage={0x1: 0x1},
    )
    pre[sender] = Account(balance=0xe8d4a51000, nonce=0)

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0x4f31b3206fbf0e0e598b9b1a7d8ac86302a0ff1d8930738f1bebae9b67173e52"
        ),
        to=None,
        data=tx_data,
        gas_limit=200000,
        gas_price=10,
        nonce=0,
        value=1,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
