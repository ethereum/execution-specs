"""
CALLCODE -> CALLCODE -> (suicide) CALLCODE -> code

Ported from:
tests/static/state_tests/stCallCodes/callcodecallcodecallcode_111_SuicideMiddleFiller.json

callee code:
    push20 0xa74ca10b765dcda3b60687f73f2881e2a56eda64
    selfdestruct
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push1 0x00
    push20 0x73b954ebc05bb0ff4a0f6a13a054d50ad1584099
    push2 0xc350
    callcode
    push1 0x02
    sstore
    stop

callee_1 code:
    push1 0x01
    push1 0x03
    sstore
    stop

contract code:
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push1 0x00
    push20 0xeaf8c2ae0d01a880cea4e1aa88def5edd153d57b
    push3 0x0249f0
    callcode
    push1 0x00
    sstore
    stop

callee_2 code:
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push1 0x00
    push20 0x23a077e1e6b0740d6bfbc41de582f2930abd1762
    push3 0x0186a0
    callcode
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
    ["tests/static/state_tests/stCallCodes/callcodecallcodecallcode_111_SuicideMiddleFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_callcodecallcodecallcode_111_suicide_middle(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """CALLCODE -> CALLCODE -> (suicide) CALLCODE -> code."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xebaf50debf10e08302fe4280c32df010463ca297")
    contract = Address("0xa74ca10b765dcda3b60687f73f2881e2a56eda64")
    callee = Address("0x23a077e1e6b0740d6bfbc41de582f2930abd1762")
    callee_1 = Address("0x73b954ebc05bb0ff4a0f6a13a054d50ad1584099")
    callee_2 = Address("0xeaf8c2ae0d01a880cea4e1aa88def5edd153d57b")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=30000000,
    )

    pre[callee] = Account(
        balance=0x2540be400,
        nonce=0,
        code=(
        Op.PUSH20[0xa74ca10b765dcda3b60687f73f2881e2a56eda64] + Op.SELFDESTRUCT
        + Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0x73b954ebc05bb0ff4a0f6a13a054d50ad1584099]
        + Op.PUSH2[0xc350] + Op.CALLCODE + Op.PUSH1[0x2] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_1] = Account(
        balance=0x2540be400,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x3] + Op.SSTORE + Op.STOP,
    )
    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0xeaf8c2ae0d01a880cea4e1aa88def5edd153d57b]
        + Op.PUSH3[0x249f0] + Op.CALLCODE + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_2] = Account(
        balance=0x2540be400,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0x23a077e1e6b0740d6bfbc41de582f2930abd1762]
        + Op.PUSH3[0x186a0] + Op.CALLCODE + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0xe04d1ac7ddda0c98397d56a0b501e960d4cd325a39286919ac23c1a07009a869"
        ),
        to=contract,
        data=b"",
        gas_limit=3000000,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
