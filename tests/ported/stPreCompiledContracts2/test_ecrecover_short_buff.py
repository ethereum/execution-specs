"""
Ported from:
tests/static/state_tests/stPreCompiledContracts2/ecrecoverShortBuffFiller.yml

contract code:
    push1 0xa0
    push1 0x00
    jumpdest
    dup2
    dup2
    lt
    push1 0x8a
    jumpi
    pop
    push1 0x00
    dup1
    mstore
    push1 0x1b
    push1 0x20
    mstore
    push32 0x184870a8e4faa6065ddf65c873935d3e48e3d1c7b7853f25cd79b8247f771910
    push1 0x40
    mstore
    push32 0x226140b6b66554c7fcfa38589e433cc148ebe5c8482eb3093ab1d9a932c96f58
    push1 0x60
    ... (47 more instructions)
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
    ["tests/static/state_tests/stPreCompiledContracts2/ecrecoverShortBuffFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_ecrecover_short_buff(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0xcccccccccccccccccccccccccccccccccccccccc")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=71794957647893862,
    )

    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=1)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0xa0] + Op.PUSH1[0x0] + Op.JUMPDEST + Op.DUP2 + Op.DUP2 + Op.LT
        + Op.PUSH1[0x8a] + Op.JUMPI + Op.POP + Op.PUSH1[0x0] + Op.DUP1 + Op.MSTORE
        + Op.PUSH1[0x1b] + Op.PUSH1[0x20] + Op.MSTORE
        + Op.PUSH32[0x184870a8e4faa6065ddf65c873935d3e48e3d1c7b7853f25cd79b8247f771910]
        + Op.PUSH1[0x40] + Op.MSTORE
        + Op.PUSH32[0x226140b6b66554c7fcfa38589e433cc148ebe5c8482eb3093ab1d9a932c96f58]
        + Op.PUSH1[0x60] + Op.MSTORE + Op.PUSH1[0x0] + Op.JUMPDEST + Op.DUP2 + Op.DUP2
        + Op.LT + Op.PUSH1[0x67] + Op.JUMPI + Op.STOP + Op.JUMPDEST + Op.DUP1
        + Op.PUSH1[0x20] + Op.PUSH2[0x100] + Op.PUSH1[0x1] + Op.SWAP4 + Op.PUSH1[0x0]
        + Op.DUP1 + Op.DUP7 + Op.GAS + Op.CALL + Op.DUP3 + Op.SWAP1 + Op.SUB + Op.DUP2
        + Op.SSTORE + Op.PUSH2[0x100] + Op.MLOAD + Op.PUSH2[0x1000] + Op.DUP3 + Op.ADD
        + Op.SSTORE + Op.ADD + Op.PUSH1[0x5f] + Op.JUMP + Op.JUMPDEST
        + Op.PUSH4[0xdead60a7] + Op.DUP1 + Op.DUP3 + Op.SSTORE + Op.PUSH2[0x1000]
        + Op.DUP3 + Op.ADD + Op.SSTORE + Op.PUSH1[0x1] + Op.ADD + Op.PUSH1[0x4]
        + Op.JUMP
    ),
        storage={0x0: 0x60a7, 0x11: 0x60a7, 0x22: 0x60a7, 0x33: 0x60a7, 0x44: 0x60a7, 0x55: 0x60a7, 0x66: 0x60a7, 0x77: 0x60a7, 0x80: 0x60a7, 0x99: 0x60a7, 0x1000: 0x60a7, 0x1011: 0x60a7, 0x1022: 0x60a7, 0x1033: 0x60a7, 0x1044: 0x60a7, 0x1055: 0x60a7, 0x1066: 0x60a7, 0x1077: 0x60a7, 0x1080: 0x60a7, 0x1099: 0x60a7},
    )

    tx = Transaction(
        secret_key=Hash(
            "0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
        ),
        to=contract,
        data=bytes.fromhex("00"),
        gas_limit=7400000,
        gas_price=10,
        nonce=1,
        value=100000,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
