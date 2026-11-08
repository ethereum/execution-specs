"""
BLOB005.

Ported from:
state_tests/Cancun/stEIP4844_blobtransactions/opcodeBlobhBoundsFiller.yml
"""

import pytest
from execution_testing import (
    AccessList,
    Account,
    Alloc,
    Bytes,
    Hash,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/Cancun/stEIP4844_blobtransactions/opcodeBlobhBoundsFiller.yml"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
def test_opcode_blobh_bounds(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """BLOB005."""
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    # Source: lll
    # {
    #    ; Can also add lll style comments here
    #    [[0]] (BLOBHASH 0)
    #    [[1]] (BLOBHASH 10)
    #    [[2]] (BLOBHASH 0xffffffff) ; 32
    #    [[3]] (BLOBHASH 0xffffffffffffffff)  ; 64
    #    [[4]] (BLOBHASH 0xffffffffffffffffffffffffffffffff) ; 128
    #    [[5]] (BLOBHASH 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff) ; 256  # noqa: E501
    # }
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.BLOBHASH(index=0x0))
        + Op.SSTORE(key=0x1, value=Op.BLOBHASH(index=0xA))
        + Op.SSTORE(key=0x2, value=Op.BLOBHASH(index=0xFFFFFFFF))
        + Op.SSTORE(key=0x3, value=Op.BLOBHASH(index=0xFFFFFFFFFFFFFFFF))
        + Op.SSTORE(
            key=0x4,
            value=Op.BLOBHASH(index=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF),
        )
        + Op.SSTORE(
            key=0x5,
            value=Op.BLOBHASH(
                index=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF  # noqa: E501
            ),
        )
        + Op.STOP,
        storage={0: 1, 1: 1, 2: 1, 3: 1, 4: 1, 5: 1},
        balance=0xDE0B6B3A7640000,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes("00"),
        gas_limit=4000000,
        value=0x186A0,
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
        access_list=[
            AccessList(
                address=target,
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
        target: Account(
            storage={
                0: 0x1A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8,  # noqa: E501
            },
        ),
    }

    state_test(pre=pre, post=post, tx=tx)
