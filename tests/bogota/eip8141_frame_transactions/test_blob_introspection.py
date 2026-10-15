"""
Blob introspection in frame transactions, for
[EIP-8141: Frame Transaction](https://eips.ethereum.org/EIPS/eip-8141).

`BLOBHASH` returns `tx.blob_versioned_hashes[index]` in every frame, and
`TXPARAM` reports the blob count, the blob fee cap and the maximum cost,
which includes the blob gas at the blob base fee.
"""

from typing import Dict, List

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    Conditional,
    Fork,
    Frame,
    Hash,
    Op,
    StateTestFiller,
    Transaction,
    add_kzg_version,
)

from .helpers import verify_frame
from .spec import Spec, ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = pytest.mark.valid_from("Bogota")

BLOB_COUNT = 2
"""Blobs the probed transaction carries, so an index past the first."""

BLOB_COMMITMENT_VERSION_KZG = 1

MAX_FEE_PER_BLOB_GAS = 11
"""A blob fee cap above the blob base fee, distinct from other fields."""

MAX_FEE = 1_000_000_000
"""A fee cap above the base fee, so a max cost computed at the effective
gas price instead of the cap is caught."""

PROBE_FRAME_STATE_GAS = 1_000_000
"""State budget of the probe frame, above the framework default, which
the storage slot the probe creates per read would exhaust."""

SLOT_BLOB_COUNT = 0x01
SLOT_MAX_FEE_PER_BLOB_GAS = 0x02
SLOT_MAX_COST = 0x03
SLOT_FIRST_BLOBHASH = 0x10
"""`BLOBHASH(i)` is stored at `SLOT_FIRST_BLOBHASH + i`, one index past
the last blob included."""


def blob_versioned_hashes() -> List[Hash]:
    """Return the versioned hashes of the probed transaction."""
    return add_kzg_version(
        list(range(1, BLOB_COUNT + 1)), BLOB_COMMITMENT_VERSION_KZG
    )


def max_cost(fork: Fork, tx: Transaction) -> int:
    """
    Return the maximum cost of a signed frame transaction: its maximum
    gas at the maximum fee per gas, plus its blob gas at the blob base
    fee of an empty excess.
    """
    tx.sign()
    assert tx.frames is not None and tx.signatures is not None
    assert tx.max_fee_per_gas is not None
    max_gas = fork.frame_transaction_intrinsic_cost_calculator()(
        frames=tx.frames, signatures=tx.signatures
    )
    floor = fork.frame_transaction_data_floor_cost_calculator()(
        frames=tx.frames, signatures=tx.signatures
    ) + sum(int(frame.state_gas_limit) for frame in tx.frames)
    blob_gas = fork.blob_gas_per_blob() * BLOB_COUNT
    blob_base_fee = fork.blob_gas_price_calculator()(excess_blob_gas=0)
    return max(max_gas, floor) * tx.max_fee_per_gas + blob_gas * blob_base_fee


@pytest.mark.parametrize(
    "mode",
    [Spec.MODE_DEFAULT, Spec.MODE_SENDER],
    ids=["default_frame", "sender_frame"],
)
def test_blob_introspection(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    mode: int,
) -> None:
    """
    Read the transaction's blobs from a `DEFAULT` or `SENDER` frame:
    `BLOBHASH` returns each versioned hash and zero past the last one,
    and `TXPARAM` reports the blob count, the blob fee cap and a maximum
    cost that includes the blob gas.
    """
    hashes = blob_versioned_hashes()
    probe_code = Bytecode()
    for index in range(BLOB_COUNT + 1):
        probe_code += Op.SSTORE(
            SLOT_FIRST_BLOBHASH + index, Op.BLOBHASH(index)
        )
    probe_code += (
        Op.SSTORE(SLOT_BLOB_COUNT, Op.TXPARAM(Spec.TXPARAM_BLOB_COUNT))
        + Op.SSTORE(
            SLOT_MAX_FEE_PER_BLOB_GAS,
            Op.TXPARAM(Spec.TXPARAM_MAX_FEE_PER_BLOB_GAS),
        )
        + Op.SSTORE(SLOT_MAX_COST, Op.TXPARAM(Spec.TXPARAM_MAX_COST))
        + Op.STOP
    )
    probe = pre.deploy_contract(code=probe_code)
    tx = Transaction(
        sender=pre.fund_eoa(),
        max_fee_per_gas=MAX_FEE,
        max_fee_per_blob_gas=MAX_FEE_PER_BLOB_GAS,
        blob_versioned_hashes=hashes,
        frames=[
            verify_frame(),
            Frame(
                mode=mode,
                target=probe,
                state_gas_limit=PROBE_FRAME_STATE_GAS,
            ),
        ],
    )

    storage: Dict[int, int | Hash] = {
        SLOT_FIRST_BLOBHASH + index: blob_hash
        for index, blob_hash in enumerate(hashes)
    }
    storage[SLOT_FIRST_BLOBHASH + BLOB_COUNT] = 0
    storage[SLOT_BLOB_COUNT] = BLOB_COUNT
    storage[SLOT_MAX_FEE_PER_BLOB_GAS] = MAX_FEE_PER_BLOB_GAS
    storage[SLOT_MAX_COST] = max_cost(fork, tx)
    state_test(pre=pre, tx=tx, post={probe: Account(storage=storage)})


def test_blob_introspection_in_verify_frame(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Read the transaction's blobs from a `VERIFY` frame, which cannot
    store what it reads: the sender approves only when `BLOBHASH`
    returns each versioned hash and zero past the last one, and
    `TXPARAM` reports the blob count and the blob fee cap. The
    transaction is valid only if every read matches.
    """
    hashes = blob_versioned_hashes()
    reads_match = Op.ISZERO(Op.BLOBHASH(BLOB_COUNT))
    for index, blob_hash in enumerate(hashes):
        reads_match = Op.AND(reads_match, Op.EQ(Op.BLOBHASH(index), blob_hash))
    reads_match = Op.AND(
        Op.AND(
            reads_match,
            Op.EQ(Op.TXPARAM(Spec.TXPARAM_BLOB_COUNT), BLOB_COUNT),
        ),
        Op.EQ(
            Op.TXPARAM(Spec.TXPARAM_MAX_FEE_PER_BLOB_GAS),
            MAX_FEE_PER_BLOB_GAS,
        ),
    )
    sender = pre.deploy_contract(
        code=Conditional(
            condition=reads_match,
            if_true=Op.APPROVE(0, 0, Spec.APPROVE_EXECUTION_AND_PAYMENT),
            if_false=Op.REVERT(0, 0),
        ),
        balance=10**18,
    )
    tx = Transaction(
        sender=sender,
        nonce=1,
        max_fee_per_gas=MAX_FEE,
        max_fee_per_blob_gas=MAX_FEE_PER_BLOB_GAS,
        blob_versioned_hashes=hashes,
        frames=[verify_frame()],
    )

    state_test(pre=pre, tx=tx, post={sender: Account(nonce=2)})
