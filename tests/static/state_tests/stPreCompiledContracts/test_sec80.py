"""
Ported from:
tests/static/state_tests/stPreCompiledContracts/sec80Filler.json

contract code:
    push1 0x1b
    jump
    jumpdest
    push1 0x00
    sstore
    jumpdest
    stop
    jumpdest
    push4 0x0badf00d
    push1 0x03
    jump
    jumpdest
    push4 0xc001f00d
    push1 0x03
    jump
    jumpdest
    push20 0x19e7e376e7c213b7e7e7e46cc70a5dd086daff2a
    push32 0x22ae6da6b482f9b1b19b0b897c3fd43884180a1c5ee361e1107a1bc635649dda
    push1 0x00
    mstore
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
    ["tests/static/state_tests/stPreCompiledContracts/sec80Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_sec80(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xebaf50debf10e08302fe4280c32df010463ca297")
    contract = Address("0x39c2fbd2d4e46fa75775649472ddb79e836160b0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[contract] = Account(
        balance=0x1312d00,
        nonce=0,
        code=(
        Op.PUSH1[0x1b] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x0] + Op.SSTORE
        + Op.JUMPDEST + Op.STOP + Op.JUMPDEST + Op.PUSH4[0xbadf00d] + Op.PUSH1[0x3]
        + Op.JUMP + Op.JUMPDEST + Op.PUSH4[0xc001f00d] + Op.PUSH1[0x3] + Op.JUMP
        + Op.JUMPDEST + Op.PUSH20[0x19e7e376e7c213b7e7e7e46cc70a5dd086daff2a]
        + Op.PUSH32[0x22ae6da6b482f9b1b19b0b897c3fd43884180a1c5ee361e1107a1bc635649dda]
        + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x1b] + Op.PUSH1[0x3f] + Op.MSTORE8
        + Op.PUSH32[0x16433dce375ce6dc8151d3f0a22728bc4a1d9fd6ed39dfd18b4609331937367f]
        + Op.PUSH1[0x40] + Op.MSTORE
        + Op.PUSH32[0x306964c0cf5d74f04129fdc60b54d35b596dde1bf89ad92cb4123318f4c0e400]
        + Op.PUSH1[0x60] + Op.MSTORE + Op.PUSH1[0x20] + Op.PUSH1[0x80]
        + Op.PUSH1[0x7f] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x1]
        + Op.PUSH2[0xffff] + Op.CALLCODE + Op.ISZERO + Op.PUSH1[0x7] + Op.JUMPI
        + Op.PUSH1[0x80] + Op.MLOAD + Op.EQ + Op.PUSH1[0x12] + Op.JUMPI
        + Op.PUSH1[0x9] + Op.JUMP
    ),
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0xe04d1ac7ddda0c98397d56a0b501e960d4cd325a39286919ac23c1a07009a869"
        ),
        to=contract,
        data=b"",
        gas_limit=10000000,
        gas_price=10,
        nonce=0,
        value=100000,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
