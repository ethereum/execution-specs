"""
Malicious bytecode found by fuzztest tool: returndatacopy(0,-1).

Ported from:
tests/static/state_tests/stRandom2/randomStatetest647Filler.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["tests/static/state_tests/stRandom2/randomStatetest647Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_random_statetest647(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Malicious bytecode found by fuzztest tool: returndatacopy(0,-1)."""
    coinbase = Address("0xd94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    sender = EOA(
        key=0x5B7B8EFB6D003CD481E408D8759A25ADC79955092F1A380D8F8B57346C1D1342
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=18857228215205537,
    )

    # Source: raw bytecode
    contract = pre.deploy_contract(
        code=(
            Op.RETURNDATACOPY(
                dest_offset=0x0, offset=Op.SUB(0x0, 0x1), size=0x1
            )
            + Op.STOP
        ),
        nonce=7,
        address=Address("0x782b7c65205e1c08192df7357e2fe778c81256a9"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x174876E800)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=5786929,
    )

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
