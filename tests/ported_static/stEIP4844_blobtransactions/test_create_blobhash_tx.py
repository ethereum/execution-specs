"""
BLOB002.

Ported from:
state_tests/Cancun/stEIP4844_blobtransactions/createBlobhashTxFiller.yml
"""

import pytest
from execution_testing import (
    AccessList,
    Account,
    Address,
    Alloc,
    Environment,
    Hash,
    StateTestFiller,
    Transaction,
    TransactionException,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/Cancun/stEIP4844_blobtransactions/createBlobhashTxFiller.yml"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.exception_test
@pytest.mark.pre_alloc_mutable
def test_create_blobhash_tx(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """BLOB002."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=7,
        excess_blob_gas=0,
        gas_limit=68719476736,
    )

    # Source: lll
    # {
    #    ; Can also add lll style comments here
    #    [[0]] (BLOBHASH 0)
    # }
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=Op.BLOBHASH(index=0x0)) + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
    )

    tx = Transaction(
        sender=sender,
        to=None,
        data=Op.STOP,
        gas_limit=4000000,
        value=0x186A0,
        max_fee_per_gas=5000000000,
        max_priority_fee_per_gas=2,
        max_fee_per_blob_gas=10,
        blob_versioned_hashes=[
            Hash(
                "0x01a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"  # noqa: E501
            ),
        ],
        access_list=[
            AccessList(
                address=addr,
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000001"  # noqa: E501
                    ),
                ],
            ),
        ],
        error=TransactionException.TYPE_3_TX_CONTRACT_CREATION,
    )

    post = {addr: Account(storage={0: 0})}

    state_test(env=env, pre=pre, post=post, tx=tx)
