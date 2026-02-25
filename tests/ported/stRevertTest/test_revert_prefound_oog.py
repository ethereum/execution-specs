"""
Ported from:
tests/static/state_tests/stRevertTest/RevertPrefoundOOGFiller.json

contract code:
    push1 0x20
    push1 0x00
    push1 0x00
    create
    push1 0x00
    sstore
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
    ["tests/static/state_tests/stRevertTest/RevertPrefoundOOGFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_revert_prefound_oog(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xfaa10b404ab607779993c016cd5da73ae1f29d7e")
    contract = Address("0x35b3f8ca79c46f2cbc3db596a2162ade570b0add")
    callee = Address("0x85fdde91fd0ce22a2968e1f1b2ebb9f9e5a180ba")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[contract] = Account(
        balance=1,
        nonce=0,
        code=(
        Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.CREATE + Op.PUSH1[0x0]
        + Op.SSTORE + Op.PUSH3[0x2fffff] + Op.PUSH1[0x0] + Op.SHA3 + Op.STOP
    ),
    )
    pre[callee] = Account(balance=1, nonce=0)
    pre[sender] = Account(balance=0xe8d4a51000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x4f31b3206fbf0e0e598b9b1a7d8ac86302a0ff1d8930738f1bebae9b67173e52"
        ),
        to=contract,
        data=b"",
        gas_limit=930000,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
