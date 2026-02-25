"""
Ported from:
tests/static/state_tests/stZeroCallsRevert/ZeroValue_SUICIDE_ToOneStorageKey_OOGRevert_ParisFiller.json

contract code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0x8d444744833c9b79fdfe630f155cf1f3bbeb92e3
    push2 0xc350
    call
    pop
    push1 0x0c
    push1 0x02
    sstore
    push1 0x0c
    push1 0x03
    sstore
    push1 0x0c
    push1 0x04
    sstore
    stop

callee_1 code:
    push20 0x4757608f18b70777ae788dd4056eeed52f7aa68f
    selfdestruct
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
    ["tests/static/state_tests/stZeroCallsRevert/ZeroValue_SUICIDE_ToOneStorageKey_OOGRevert_ParisFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_zero_value_suicide_to_one_storage_key_oog_revert_paris(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xfaa10b404ab607779993c016cd5da73ae1f29d7e")
    contract = Address("0x1d63510fcd4f3069306ebae45ec6910c0bc944c8")
    callee = Address("0x4757608f18b70777ae788dd4056eeed52f7aa68f")
    callee_1 = Address("0x8d444744833c9b79fdfe630f155cf1f3bbeb92e3")

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
        + Op.PUSH1[0x0] + Op.PUSH20[0x8d444744833c9b79fdfe630f155cf1f3bbeb92e3]
        + Op.PUSH2[0xc350] + Op.CALL + Op.POP + Op.PUSH1[0xc] + Op.PUSH1[0x2]
        + Op.SSTORE + Op.PUSH1[0xc] + Op.PUSH1[0x3] + Op.SSTORE + Op.PUSH1[0xc]
        + Op.PUSH1[0x4] + Op.SSTORE + Op.STOP
    ),
        storage={0x0: 0x1},
    )
    pre[callee] = Account(balance=10, nonce=0, storage={0x0: 0x1})
    pre[callee_1] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH20[0x4757608f18b70777ae788dd4056eeed52f7aa68f] + Op.SELFDESTRUCT
        + Op.STOP
    ),
        storage={0x0: 0x1},
    )
    pre[sender] = Account(balance=0xe8d4a51000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x4f31b3206fbf0e0e598b9b1a7d8ac86302a0ff1d8930738f1bebae9b67173e52"
        ),
        to=contract,
        data=b"",
        gas_limit=75000,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
