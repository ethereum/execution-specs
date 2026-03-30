"""
Test_store_gas_on_create.

Ported from:
state_tests/stTransactionTest/StoreGasOnCreateFiller.json
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
    ["state_tests/stTransactionTest/StoreGasOnCreateFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_store_gas_on_create(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_store_gas_on_create."""
    coinbase = Address(0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B)
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre[sender] = Account(balance=0x17D78400)
    # Source: lll
    # { (MSTORE 0 0x5a60fd55) (CREATE 0 28 4)}
    coinbase = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=0x5A60FD55)
        + Op.CREATE(value=0x0, offset=0x1C, size=0x4)
        + Op.STOP,
        nonce=0,
        address=Address(0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=coinbase,
        data=Bytes(""),
        gas_limit=131882,
        value=100,
    )

    post = {
        compute_create_address(address=coinbase, nonce=0): Account(
            storage={253: 0x12F39}
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
