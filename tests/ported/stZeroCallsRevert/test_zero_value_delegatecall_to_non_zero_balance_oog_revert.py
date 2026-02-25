"""
Ported from:
tests/static/state_tests/stZeroCallsRevert/ZeroValue_DELEGATECALL_ToNonZeroBalance_OOGRevertFiller.json

contract code:
    gas
    push1 0x00
    sstore
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0x9089da66e8bbc08846842a301905501bc8525dc4
    push2 0xea60
    delegatecall
    push1 0x01
    sstore
    push1 0x0c
    push1 0x02
    sstore
    push1 0x0c
    push1 0x03
    sstore
    push1 0x0c
    push1 0x04
    ... (5 more instructions)
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
    ["tests/static/state_tests/stZeroCallsRevert/ZeroValue_DELEGATECALL_ToNonZeroBalance_OOGRevertFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_zero_value_delegatecall_to_non_zero_balance_oog_revert(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xfaa10b404ab607779993c016cd5da73ae1f29d7e")
    contract = Address("0xa58f691f4ea54dce9588fbad2b459893b055763a")
    callee = Address("0x9089da66e8bbc08846842a301905501bc8525dc4")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[callee] = Account(balance=100, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.GAS + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x9089da66e8bbc08846842a301905501bc8525dc4] + Op.PUSH2[0xea60]
        + Op.DELEGATECALL + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0xc] + Op.PUSH1[0x2]
        + Op.SSTORE + Op.PUSH1[0xc] + Op.PUSH1[0x3] + Op.SSTORE + Op.PUSH1[0xc]
        + Op.PUSH1[0x4] + Op.SSTORE + Op.GAS + Op.PUSH1[0x64] + Op.SSTORE + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xe8d4a51000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x4f31b3206fbf0e0e598b9b1a7d8ac86302a0ff1d8930738f1bebae9b67173e52"
        ),
        to=contract,
        data=b"",
        gas_limit=135000,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
