"""
BLOB002

Ported from:
state_tests/Cancun/stEIP4844_blobtransactions/createBlobhashTxFiller.yml
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
    TransactionException,
    AccessList,
    Hash,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"

REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/Cancun/stEIP4844_blobtransactions/createBlobhashTxFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.exception_test
@pytest.mark.pre_alloc_mutable
def test_create_blobhash_tx(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """BLOB002"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xb1f4cbc3a50042184425a6f9e996d0910f7ba879457ce5dac5c71e498ad3c005
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=7,
        excess_blob_gas=0,
        gas_limit=68719476736,
    )

    # Source: lll
    # {
    #    ; Can also add lll style comments here
    #    [[0]] (BLOBHASH 0) 
    # }
    addr_0x095e7baea6a6c7c4c2dfeb977efac326af552d87 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.BLOBHASH(index=0x0)) + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0xc4dcf66bd4cdefe4ce7fba4951be4e9f580122c5"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000)


    tx = Transaction(
        sender=sender,
        to=None,
        data=bytes.fromhex("00"),
        gas_limit=4000000,
        value=0x186a0,
        max_fee_per_gas=5000000000,
        max_priority_fee_per_gas=2,
        nonce=0,
        max_fee_per_blob_gas=10,
        blob_versioned_hashes=[
            Hash(
                "0x01a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"  # noqa: E501
            ),
        ],
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

    post = {
        addr_0x095e7baea6a6c7c4c2dfeb977efac326af552d87: Account(storage={0: 0}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
