"""
Test_revert_prefound_oog.

Ported from:
state_tests/stRevertTest/RevertPrefoundOOGFiller.json
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
    ["state_tests/stRevertTest/RevertPrefoundOOGFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_revert_prefound_oog(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_revert_prefound_oog."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0xE8D4A51000)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    addr = pre.fund_eoa(amount=1)  # noqa: F841
    # Source: lll
    # { [[0]] (CREATE 0 0 32) (KECCAK256 0x00 0x2fffff) }
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0, value=Op.CREATE(value=0x0, offset=0x0, size=0x20)
        )
        + Op.SHA3(offset=0x0, size=0x2FFFFF)
        + Op.STOP,
        balance=1,
        nonce=0,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=930000,
    )

    post = {addr: Account(storage={}, code=b"", balance=1, nonce=0)}

    state_test(env=env, pre=pre, post=post, tx=tx)
