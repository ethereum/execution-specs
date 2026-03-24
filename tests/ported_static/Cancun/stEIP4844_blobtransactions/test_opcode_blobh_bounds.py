"""
BLOB005.

Ported from:
tests/static/state_tests/Cancun/stEIP4844_blobtransactions
opcodeBlobhBoundsFiller.yml
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
        "tests/static/state_tests/Cancun/stEIP4844_blobtransactions/opcodeBlobhBoundsFiller.yml",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_opcode_blobh_bounds(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """BLOB005."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xB1F4CBC3A50042184425A6F9E996D0910F7BA879457CE5DAC5C71E498AD3C005
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=1,
        gas_limit=68719476736,
    )

    pre[sender] = Account(balance=0xDE0B6B3A7640000)
    # Source: LLL
    # {
    #    ; Can also add lll style comments here
    #    [[0]] (BLOBHASH 0)
    #    [[1]] (BLOBHASH 10)
    #    [[2]] (BLOBHASH 0xffffffff) ; 32
    #    [[3]] (BLOBHASH 0xffffffffffffffff)  ; 64
    #    [[4]] (BLOBHASH 0xffffffffffffffffffffffffffffffff) ; 128
    #    [[5]] (BLOBHASH 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff) ; 256  # noqa: E501
    # }
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=Op.BLOBHASH(index=0x0))
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
                    index=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                ),
            )
            + Op.STOP
        ),
        storage={
            0x0: 0x1,
            0x1: 0x1,
            0x2: 0x1,
            0x3: 0x1,
            0x4: 0x1,
            0x5: 0x1,
        },
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0xc8126e943c569c35df09619f8e1e67460acff695"),  # noqa: E501
    )

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
                address=Address("0xc8126e943c569c35df09619f8e1e67460acff695"),
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
