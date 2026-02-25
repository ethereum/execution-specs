"""
BLOB005

Ported from:
tests/static/state_tests/Cancun/stEIP4844_blobtransactions/opcodeBlobhBoundsFiller.yml

contract code:
    push1 0x00
    blobhash
    push1 0x00
    sstore
    push1 0x0a
    blobhash
    push1 0x01
    sstore
    push4 0xffffffff
    blobhash
    push1 0x02
    sstore
    push8 0xffffffffffffffff
    blobhash
    push1 0x03
    sstore
    push16 0xffffffffffffffffffffffffffffffff
    blobhash
    push1 0x04
    sstore
    ... (5 more instructions)
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
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["tests/static/state_tests/Cancun/stEIP4844_blobtransactions/opcodeBlobhBoundsFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_opcode_blobh_bounds(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """BLOB005."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0x2e3d0156d2b99a6eacba540c55f423c8f5a33143")
    contract = Address("0xc8126e943c569c35df09619f8e1e67460acff695")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=1,
        gas_limit=68719476736,
    )

    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.BLOBHASH + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0xa]
        + Op.BLOBHASH + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH4[0xffffffff] + Op.BLOBHASH
        + Op.PUSH1[0x2] + Op.SSTORE + Op.PUSH8[0xffffffffffffffff] + Op.BLOBHASH
        + Op.PUSH1[0x3] + Op.SSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff]
        + Op.BLOBHASH + Op.PUSH1[0x4] + Op.SSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
        + Op.BLOBHASH + Op.PUSH1[0x5] + Op.SSTORE + Op.STOP
    ),
        storage={0x0: 0x1, 0x1: 0x1, 0x2: 0x1, 0x3: 0x1, 0x4: 0x1, 0x5: 0x1},
    )

    tx = Transaction(
        secret_key=Hash(
            "0xb1f4cbc3a50042184425a6f9e996d0910f7ba879457ce5dac5c71e498ad3c005"
        ),
        to=contract,
        data=bytes.fromhex("00"),
        gas_limit=4000000,
        max_fee_per_gas=5000000000,
        max_priority_fee_per_gas=2,
        max_fee_per_blob_gas=10,
        blob_versioned_hashes=[Hash("0x01a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"), Hash("0x01a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8")],
        nonce=0,
        value=100000,
        access_list=[AccessList(address=Address("0xc8126e943c569c35df09619f8e1e67460acff695"), storage_keys=[Hash("0x0000000000000000000000000000000000000000000000000000000000000000"), Hash("0x0000000000000000000000000000000000000000000000000000000000000001")])],
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
