"""
Calling a runtime code that contains only a single `REVERT` should consume...

Ported from:
tests/static/state_tests/stRevertTest/RevertOnEmptyStackFiller.json
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
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["tests/static/state_tests/stRevertTest/RevertOnEmptyStackFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_revert_on_empty_stack(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Calling a runtime code that contains only a single `REVERT`..."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x3327048BBC0B8C348A6352BE62994144E64B8FF2CEC68D9FF4CA4E911ECD5D22
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    # Source: raw bytecode
    contract = pre.deploy_contract(
        code=Op.REVERT,
        nonce=0,
        address=Address("0x3141bb954e8294e47a14ebd08229f30e6294ba83"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x5AF3107A4000)

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {contract: Account(code=bytes.fromhex("fd"))},
        },
    ]

    post, _exc = resolve_expect_post(EXPECT_ENTRIES, 0, 0, 0, fork)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=2000000,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
