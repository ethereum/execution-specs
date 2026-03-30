"""
Test_recursive_create.

Ported from:
state_tests/stRecursiveCreate/recursiveCreateFiller.json
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
    compute_create_address,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stRecursiveCreate/recursiveCreateFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_recursive_create(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_recursive_create."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0x095E7BAEA6A6C7C4C2DFEB977EFAC326AF552D87)
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    # Source: lll
    # {(CODECOPY 0 0 32)(CREATE 0 0 32)}
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.CODECOPY(dest_offset=0x0, offset=0x0, size=0x20)
        + Op.CREATE(value=0x0, offset=0x0, size=0x20)
        + Op.STOP,
        balance=0x1312D00,
        nonce=0,
        address=Address(0x095E7BAEA6A6C7C4C2DFEB977EFAC326AF552D87),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=Bytes(""),
        gas_limit=465224,
        value=0x186A0,
    )

    post = {
        compute_create_address(address=contract_0, nonce=0): Account(nonce=2),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
