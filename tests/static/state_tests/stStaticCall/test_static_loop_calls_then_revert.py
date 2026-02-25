"""
Requires a separate pre-alloc group due to time required to fill when grouped with other tests.

Ported from:
tests/static/state_tests/stStaticCall/static_LoopCallsThenRevertFiller.json

callee code:
    push1 0x00
    mload
    push1 0x01
    add
    push1 0x00
    mstore
    stop

callee_1 code:
    jumpdest
    push1 0x01
    push1 0x00
    calldataload
    sub
    push1 0x00
    mstore
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0x59c89b27361fd637262b13489f28923c835e17b2
    push2 0xc350
    staticcall
    pop
    push1 0x00
    mload
    push1 0x00
    jumpi

contract code:
    push2 0x0352
    push1 0x00
    mstore
    push1 0x00
    push1 0x00
    push1 0x20
    push1 0x00
    push1 0x00
    push20 0x7a2af5cc0310371cce006e472ed3b5d68e62f839
    push2 0x2710
    gas
    sub
    call
    push1 0x00
    sstore
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
    ["tests/static/state_tests/stStaticCall/static_LoopCallsThenRevertFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        10000000,
        9000000,
    ],
    ids=['case0', 'case1'],
)
@pytest.mark.pre_alloc_mutable
def test_static_loop_calls_then_revert(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Requires a separate pre-alloc group due to time required to fill when grouped with other tests.."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xfaa10b404ab607779993c016cd5da73ae1f29d7e")
    contract = Address("0xd64495cbba16d27a88b96f2a72417b957ed4cae6")
    callee = Address("0x59c89b27361fd637262b13489f28923c835e17b2")
    callee_1 = Address("0x7a2af5cc0310371cce006e472ed3b5d68e62f839")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x1] + Op.ADD + Op.PUSH1[0x0]
        + Op.MSTORE + Op.STOP
    ),
    )
    pre[callee_1] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.SUB
        + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0x59c89b27361fd637262b13489f28923c835e17b2]
        + Op.PUSH2[0xc350] + Op.STATICCALL + Op.POP + Op.PUSH1[0x0] + Op.MLOAD
        + Op.PUSH1[0x0] + Op.JUMPI
    ),
        storage={0x0: 0x352},
    )
    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH2[0x352] + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x7a2af5cc0310371cce006e472ed3b5d68e62f839] + Op.PUSH2[0x2710]
        + Op.GAS + Op.SUB + Op.CALL + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x1]
        + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xe8d4a51000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x4f31b3206fbf0e0e598b9b1a7d8ac86302a0ff1d8930738f1bebae9b67173e52"
        ),
        to=contract,
        data=b"",
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
