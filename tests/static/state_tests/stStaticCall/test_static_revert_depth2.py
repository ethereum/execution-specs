"""
Ported from:
tests/static/state_tests/stStaticCall/static_RevertDepth2Filler.json

callee code:
    push1 0x01
    push1 0x01
    mstore
    stop

contract code:
    push1 0x00
    sload
    push1 0x01
    add
    push1 0x00
    sstore
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0x5dd18f4768e54de1443f70ec11ad95d5db424293
    push3 0x0249f0
    staticcall
    push1 0x01
    sstore
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0xa61140a1c2699a13c619940208a513d42f654e98
    ... (5 more instructions)

callee_1 code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0x15b1327fe926a2172adfd10efdef1505c8e15461
    push2 0xc350
    staticcall
    pop
    push1 0x01
    push1 0x01
    mstore
    stop

callee_2 code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0x15b1327fe926a2172adfd10efdef1505c8e15461
    push2 0xc350
    staticcall
    pop
    push3 0x2fffff
    push1 0x00
    sha3
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
    ["tests/static/state_tests/stStaticCall/static_RevertDepth2Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_static_revert_depth2(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xfaa10b404ab607779993c016cd5da73ae1f29d7e")
    contract = Address("0x57c111943c5e6f1817ee85fd1212409b7d1f7f26")
    callee = Address("0x15b1327fe926a2172adfd10efdef1505c8e15461")
    callee_1 = Address("0x5dd18f4768e54de1443f70ec11ad95d5db424293")
    callee_2 = Address("0xa61140a1c2699a13c619940208a513d42f654e98")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[callee] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.MSTORE + Op.STOP,
    )
    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.SLOAD + Op.PUSH1[0x1] + Op.ADD + Op.PUSH1[0x0]
        + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x5dd18f4768e54de1443f70ec11ad95d5db424293] + Op.PUSH3[0x249f0]
        + Op.STATICCALL + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xa61140a1c2699a13c619940208a513d42f654e98] + Op.PUSH3[0x249f0]
        + Op.STATICCALL + Op.PUSH1[0x2] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_1] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x15b1327fe926a2172adfd10efdef1505c8e15461] + Op.PUSH2[0xc350]
        + Op.STATICCALL + Op.POP + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.MSTORE + Op.STOP
    ),
    )
    pre[callee_2] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x15b1327fe926a2172adfd10efdef1505c8e15461] + Op.PUSH2[0xc350]
        + Op.STATICCALL + Op.POP + Op.PUSH3[0x2fffff] + Op.PUSH1[0x0] + Op.SHA3
        + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xe8d4a51000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x4f31b3206fbf0e0e598b9b1a7d8ac86302a0ff1d8930738f1bebae9b67173e52"
        ),
        to=contract,
        data=b"",
        gas_limit=1706850,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
