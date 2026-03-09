"""
BLOB003, BLOB004.

Ported from:
tests/static/state_tests/Cancun/stEIP4844_blobtransactions
opcodeBlobhashOutOfRangeFiller.yml
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
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/Cancun/stEIP4844_blobtransactions/opcodeBlobhashOutOfRangeFiller.yml",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_opcode_blobhash_out_of_range(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """BLOB003, BLOB004."""
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

    # Source: LLL
    # {
    #    ; Can also add lll style comments here
    #    [[0]] (BLOBHASH 0)
    #    [[1]] (BLOBHASH 10)
    # }
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=Op.BLOBHASH(index=0x0))
            + Op.SSTORE(key=0x1, value=Op.BLOBHASH(index=0xA))
            + Op.STOP
        ),
        storage={0x0: 0x1, 0x1: 0x1},
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x0c4d6f62d3c85069cea2411284bd520ac87fb7eb"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex("00"),
        gas_limit=4000000,
        max_fee_per_gas=5000000000,
        max_priority_fee_per_gas=2,
        max_fee_per_blob_gas=10,
        blob_versioned_hashes=[
            Hash(
                "0x01a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"  # noqa: E501
            ),
            Hash(
                "0x01a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"  # noqa: E501
            ),
        ],
        value=100000,
        access_list=[
            AccessList(
                address=Address("0x0c4d6f62d3c85069cea2411284bd520ac87fb7eb"),
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
    )

    post = {
        contract: Account(
            storage={
                0: 0x1A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8,  # noqa: E501
            },
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
