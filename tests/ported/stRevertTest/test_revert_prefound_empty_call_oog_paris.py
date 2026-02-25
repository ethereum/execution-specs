"""
Ported from:
tests/static/state_tests/stRevertTest/RevertPrefoundEmptyCallOOG_ParisFiller.json

contract code:
    push1 0x20
    push1 0x00
    push1 0x20
    push1 0x00
    push1 0x00
    push20 0x76fae819612a29489a1a43208613d8f8557b8898
    push2 0xc350
    call
    push1 0x00
    sstore
    push1 0x0c
    push1 0x01
    sstore
    push1 0x0c
    push1 0x02
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
    ["tests/static/state_tests/stRevertTest/RevertPrefoundEmptyCallOOG_ParisFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_revert_prefound_empty_call_oog_paris(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xfaa10b404ab607779993c016cd5da73ae1f29d7e")
    contract = Address("0xf679bfe5f61e7640b9a66db191d5d86abc7b5c0a")
    callee = Address("0x76fae819612a29489a1a43208613d8f8557b8898")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[callee] = Account(balance=10, nonce=0)
    pre[contract] = Account(
        balance=1,
        nonce=0,
        code=(
        Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.PUSH1[0x20] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0x76fae819612a29489a1a43208613d8f8557b8898]
        + Op.PUSH2[0xc350] + Op.CALL + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0xc]
        + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0xc] + Op.PUSH1[0x2] + Op.SSTORE
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
        gas_limit=63000,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
