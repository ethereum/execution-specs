"""
test_store_gas_on_create

Ported from:
state_tests/stTransactionTest/StoreGasOnCreateFiller.json
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
    ["state_tests/stTransactionTest/StoreGasOnCreateFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_store_gas_on_create(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_store_gas_on_create"""
    coinbase = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    sender = EOA(
        key=0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre[sender] = Account(balance=0x17d78400)
    # Source: lll
    # { (MSTORE 0 0x5a60fd55) (CREATE 0 28 4)}
    coinbase = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=0x5a60fd55)
        + Op.CREATE(value=0x0, offset=0x1c, size=0x4) + Op.STOP,
        nonce=0,
        address=Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b"),  # noqa: E501
    )


    tx = Transaction(
        sender=sender,
        to=coinbase,
        data=b'',
        gas_limit=131882,
        value=100,
        nonce=0,
        gas_price=10,
    )

    post = {
        Address("0xf1ecf98489fa9ed60a664fc4998db699cfa39d40"): Account(storage={253: 0x12f39}),  # noqa: E501
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
