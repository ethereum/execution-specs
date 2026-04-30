"""
Malicious bytecode found by fuzztest tool: returndatacopy(0,-1).

Ported from:
state_tests/stRandom2/randomStatetest647Filler.json
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stRandom2/randomStatetest647Filler.json"],
)
@pytest.mark.valid_from("Cancun")
def test_random_statetest647(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Malicious bytecode found by fuzztest tool: returndatacopy(0,-1)."""
    coinbase = Address(0xD94F5374FCE5EDBC8E2A8697C15331677E6EBF0B)
    sender = pre.fund_eoa(amount=0x174876E800)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=18857228215205537,
    )

    # Source: raw
    # 0x6001600160000360003e00
    target = pre.deploy_contract(  # noqa: F841
        code=Op.RETURNDATACOPY(
            dest_offset=0x0, offset=Op.SUB(0x0, 0x1), size=0x1
        )
        + Op.STOP,
        nonce=7,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=5786929,
    )

    post = {sender: Account(nonce=1)}

    state_test(env=env, pre=pre, post=post, tx=tx)
