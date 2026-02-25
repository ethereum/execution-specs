"""
Ori Pomerantz qbzzt1@gmail.com

Ported from:
tests/static/state_tests/stEIP150singleCodeGasPrices/gasCostExpFiller.yml

contract code:
    push1 0x04
    calldataload
    push1 0x00
    mstore
    push1 0x24
    calldataload
    push1 0x20
    mstore
    gas
    push1 0x40
    mstore
    push1 0x00
    mload
    push1 0x02
    exp
    pop
    gas
    push1 0x60
    mstore
    push1 0x20
    ... (10 more instructions)
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
    ["tests/static/state_tests/stEIP150singleCodeGasPrices/gasCostExpFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "c5b5a1ae00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000020",
        "c5b5a1ae00000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000052",
        "c5b5a1ae00000000000000000000000000000000000000000000000000000000000000ff0000000000000000000000000000000000000000000000000000000000000052",
        "c5b5a1ae00000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000084",
        "c5b5a1ae000000000000000000000000000000000000000000000000000000000000ffff0000000000000000000000000000000000000000000000000000000000000084",
        "c5b5a1ae000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000000b6",
        "c5b5a1ae0000000000000000000000000000000000000000000000000000000000ffffff00000000000000000000000000000000000000000000000000000000000000b6",
        "c5b5a1ae000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000000000e8",
        "c5b5a1ae00000000000000000000000000000000000000000000000000000000ffffffff00000000000000000000000000000000000000000000000000000000000000e8",
    ],
    ids=['case0', 'case1', 'case2', 'case3', 'case4', 'case5', 'case6', 'case7', 'case8'],
)
@pytest.mark.pre_alloc_mutable
def test_gas_cost_exp(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Ori Pomerantz qbzzt1@gmail.com."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0x56724d001b4f2a2888a81971a64aad37cd43f881")
    contract = Address("0x087aab8070088fbbe4f60141cf79032d28528b89")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[contract] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x24]
        + Op.CALLDATALOAD + Op.PUSH1[0x20] + Op.MSTORE + Op.GAS + Op.PUSH1[0x40]
        + Op.MSTORE + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x2] + Op.EXP + Op.POP
        + Op.GAS + Op.PUSH1[0x60] + Op.MSTORE + Op.PUSH1[0x20] + Op.MLOAD
        + Op.PUSH1[0x60] + Op.MLOAD + Op.PUSH1[0x40] + Op.MLOAD + Op.SUB + Op.SUB
        + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP
    ),
        storage={0x0: 0x60a7},
    )
    pre[sender] = Account(balance=0xba1a9ce0ba1a9ce, nonce=0)

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0x40ac0fc28c27e961ee46ec43355a094de205856edbd4654cf2577c2608d4ec1e"
        ),
        to=contract,
        data=tx_data,
        gas_limit=16777216,
        gas_price=10,
        nonce=0,
        value=1,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
