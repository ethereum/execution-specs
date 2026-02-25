"""
Ported from:
tests/static/state_tests/stStaticCall/static_CheckOpcodes4Filler.json

contract code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0xb4b91c40f3e3a6e5576b0413572b88d535cee7b0
    push3 0x0186a0
    staticcall
    push1 0x01
    sstore
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0x8fd6268252f0d331531601b40524719c7f681fe9
    push3 0x0186a0
    staticcall
    push1 0x02
    sstore
    caller
    push1 0x03
    ... (11 more instructions)

callee code:
    origin
    push20 0xfaa10b404ab607779993c016cd5da73ae1f29d7e
    eq
    push1 0x22
    jumpi
    push1 0x02
    push1 0x01
    sstore
    push1 0x28
    jump
    jumpdest
    push1 0x01
    push1 0x01
    mstore
    jumpdest
    caller
    push20 0x3350a62ddddd0ff0e39cd82e2d185fe06b5fcf49
    eq
    push1 0x4b
    jumpi
    ... (41 more instructions)

callee_1 code:
    origin
    push20 0xfaa10b404ab607779993c016cd5da73ae1f29d7e
    eq
    push1 0x22
    jumpi
    push1 0x02
    push1 0x01
    sstore
    push1 0x28
    jump
    jumpdest
    push1 0x01
    push1 0x01
    mstore
    jumpdest
    caller
    push20 0x3350a62ddddd0ff0e39cd82e2d185fe06b5fcf49
    eq
    push1 0x4b
    jumpi
    ... (41 more instructions)
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
    ["tests/static/state_tests/stStaticCall/static_CheckOpcodes4Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit, tx_value",
    [
        (50000, 0),
        (50000, 100),
        (335000, 0),
        (335000, 100),
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_static_check_opcodes4(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
    tx_value: int,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xfaa10b404ab607779993c016cd5da73ae1f29d7e")
    contract = Address("0x3350a62ddddd0ff0e39cd82e2d185fe06b5fcf49")
    callee = Address("0x8fd6268252f0d331531601b40524719c7f681fe9")
    callee_1 = Address("0xb4b91c40f3e3a6e5576b0413572b88d535cee7b0")

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
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xb4b91c40f3e3a6e5576b0413572b88d535cee7b0] + Op.PUSH3[0x186a0]
        + Op.STATICCALL + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x8fd6268252f0d331531601b40524719c7f681fe9] + Op.PUSH3[0x186a0]
        + Op.STATICCALL + Op.PUSH1[0x2] + Op.SSTORE + Op.CALLER + Op.PUSH1[0x3]
        + Op.SSTORE + Op.CALLVALUE + Op.PUSH1[0x4] + Op.SSTORE + Op.ORIGIN
        + Op.PUSH1[0x5] + Op.SSTORE + Op.ADDRESS + Op.PUSH1[0x6] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.ORIGIN + Op.PUSH20[0xfaa10b404ab607779993c016cd5da73ae1f29d7e] + Op.EQ
        + Op.PUSH1[0x22] + Op.JUMPI + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH1[0x28] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.JUMPDEST + Op.CALLER
        + Op.PUSH20[0x3350a62ddddd0ff0e39cd82e2d185fe06b5fcf49] + Op.EQ
        + Op.PUSH1[0x4b] + Op.JUMPI + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH1[0x51] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.JUMPDEST + Op.ADDRESS
        + Op.PUSH20[0x8fd6268252f0d331531601b40524719c7f681fe9] + Op.EQ
        + Op.PUSH1[0x74] + Op.JUMPI + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH1[0x7a] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.JUMPDEST + Op.CALLVALUE + Op.PUSH1[0x0] + Op.EQ
        + Op.PUSH1[0x8a] + Op.JUMPI + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH1[0x90] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.JUMPDEST + Op.STOP
    ),
    )
    pre[callee_1] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.ORIGIN + Op.PUSH20[0xfaa10b404ab607779993c016cd5da73ae1f29d7e] + Op.EQ
        + Op.PUSH1[0x22] + Op.JUMPI + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH1[0x28] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.JUMPDEST + Op.CALLER
        + Op.PUSH20[0x3350a62ddddd0ff0e39cd82e2d185fe06b5fcf49] + Op.EQ
        + Op.PUSH1[0x4b] + Op.JUMPI + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH1[0x51] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.JUMPDEST + Op.ADDRESS
        + Op.PUSH20[0xb4b91c40f3e3a6e5576b0413572b88d535cee7b0] + Op.EQ
        + Op.PUSH1[0x74] + Op.JUMPI + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH1[0x7a] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.JUMPDEST + Op.CALLVALUE + Op.PUSH1[0x0] + Op.EQ
        + Op.PUSH1[0x8a] + Op.JUMPI + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH1[0x90] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.JUMPDEST + Op.STOP
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
        value=tx_value,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
