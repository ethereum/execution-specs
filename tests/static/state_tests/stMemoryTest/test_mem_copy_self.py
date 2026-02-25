"""
Ori Pomerantz qbzzt1@gmail.com

Ported from:
tests/static/state_tests/stMemoryTest/memCopySelfFiller.yml

contract code:
    push1 0x04
    push1 0x00
    jumpdest
    push1 0x0f
    dup2
    lt
    push1 0x30
    jumpi
    push1 0x0a
    push1 0x02
    dup2
    push1 0x00
    dup1
    dup7
    dup2
    mload
    dup3
    sstore
    gas
    call
    ... (27 more instructions)
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
    ["tests/static/state_tests/stMemoryTest/memCopySelfFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_mem_copy_self(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Ori Pomerantz qbzzt1@gmail.com."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0x485fd0fd5c1d0409d2b772a66e98a6ac867b9d8b")
    contract = Address("0xb595300ac049b84c5277c7ca68a96d74ae377b85")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[sender] = Account(balance=0xba1a9ce0ba1a9ce, nonce=1)
    pre[contract] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=1,
        code=(
        Op.PUSH1[0x4] + Op.PUSH1[0x0] + Op.JUMPDEST + Op.PUSH1[0xf] + Op.DUP2
        + Op.LT + Op.PUSH1[0x30] + Op.JUMPI + Op.PUSH1[0xa] + Op.PUSH1[0x2] + Op.DUP2
        + Op.PUSH1[0x0] + Op.DUP1 + Op.DUP7 + Op.DUP2 + Op.MLOAD + Op.DUP3 + Op.SSTORE
        + Op.GAS + Op.CALL + Op.POP + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x1]
        + Op.SSTORE + Op.PUSH1[0xa] + Op.PUSH1[0x0] + Op.PUSH1[0x20]
        + Op.RETURNDATACOPY + Op.PUSH1[0x20] + Op.MLOAD + Op.PUSH1[0x2] + Op.SSTORE
        + Op.STOP + Op.JUMPDEST + Op.DUP1 + Op.PUSH1[0x11] + Op.PUSH1[0x1] + Op.DUP1
        + Op.SWAP4 + Op.ADD + Op.MUL + Op.DUP2 + Op.MSTORE8 + Op.ADD + Op.PUSH1[0x4]
        + Op.JUMP
    ),
        storage={0x0: 0x60a7},
    )

    tx = Transaction(
        secret_key=Hash(
            "0x48dc5a9f099caaaa557742ca3a990a94be45b9969126a1bc74e5e8be5a2b5b47"
        ),
        to=contract,
        data=b"",
        gas_limit=16777216,
        gas_price=10,
        nonce=1,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
