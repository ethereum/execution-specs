"""
Test_revert_prefound_oog.

Ported from:
state_tests/stRevertTest/RevertPrefoundOOGFiller.json
"""

import pytest
from execution_testing import (
    EOA,
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
    addr = Address(0x85FDDE91FD0CE22A2968E1F1B2EBB9F9E5A180BA)
    sender = EOA(
        key=0x4F31B3206FBF0E0E598B9B1A7D8AC86302A0FF1D8930738F1BEBAE9B67173E52
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[sender] = Account(balance=0xE8D4A51000)
    pre[addr] = Account(balance=1)
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
        address=Address(0x35B3F8CA79C46F2CBC3DB596A2162ADE570B0ADD),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=930000,
    )

    post = {addr: Account(storage={}, code=b"", balance=1, nonce=0)}

    state_test(env=env, pre=pre, post=post, tx=tx)
