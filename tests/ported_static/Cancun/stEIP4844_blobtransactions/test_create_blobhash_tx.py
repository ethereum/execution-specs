"""
BLOB002.

Ported from:
tests/static/state_tests/Cancun/stEIP4844_blobtransactions
createBlobhashTxFiller.yml
"""

import pytest
from execution_testing import (
    EOA,
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
        "tests/static/state_tests/Cancun/stEIP4844_blobtransactions/createBlobhashTxFiller.yml",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
@pytest.mark.exception_test
def test_create_blobhash_tx(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """BLOB002."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xB1F4CBC3A50042184425A6F9E996D0910F7BA879457CE5DAC5C71E498AD3C005
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=7,
        gas_limit=68719476736,
    )

    pre[sender] = Account(balance=0xDE0B6B3A7640000)
    pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.BLOBHASH(index=0x0)) + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0xc4dcf66bd4cdefe4ce7fba4951be4e9f580122c5"),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=None,
        data=bytes.fromhex("00"),
        gas_limit=4000000,
        max_fee_per_gas=5000000000,
        max_priority_fee_per_gas=2,
        max_fee_per_blob_gas=10,
        blob_versioned_hashes=[
            Hash(
                "0x01a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"  # noqa: E501
            ),
        ],
        value=100000,
        access_list=[
            AccessList(
                address=Address("0xc4dcf66bd4cdefe4ce7fba4951be4e9f580122c5"),
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

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
