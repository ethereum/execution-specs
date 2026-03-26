"""
Malicious bytecode found by fuzztest tool: returndatacopy(0,-1)

Ported from:
state_tests/stRandom2/randomStatetest647Filler.json
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
    ["state_tests/stRandom2/randomStatetest647Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_random_statetest647(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Malicious bytecode found by fuzztest tool: returndatacopy(0,-1)"""
    coinbase = Address("0xd94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    sender = EOA(
        key=0x5b7b8efb6d003cd481e408d8759a25adc79955092f1a380d8f8b57346c1d1342
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=18857228215205537,
    )

    pre[sender] = Account(balance=0x174876e800)
    # Source: raw
    # 0x6001600160000360003e00
    target = pre.deploy_contract(
        code=Op.RETURNDATACOPY(dest_offset=0x0, offset=Op.SUB(0x0, 0x1), size=0x1)
        + Op.STOP,
        nonce=7,
        address=Address("0x782b7c65205e1c08192df7357e2fe778c81256a9"),  # noqa: E501
    )


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=5786929,
        nonce=0,
        gas_price=10,
    )

    post = {sender: Account(nonce=1)}

    state_test(env=env, pre=pre, post=post, tx=tx)
