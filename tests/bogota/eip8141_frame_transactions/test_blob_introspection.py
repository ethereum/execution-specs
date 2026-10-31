"""
Blob introspection in frame transactions, for
[EIP-8141: Frame Transaction](https://eips.ethereum.org/EIPS/eip-8141).

`BLOBHASH` returns `tx.blob_versioned_hashes[index]` in every frame, and
`TXPARAM` reports the blob count and the `max_fee` budget, which also pays
for the blob gas at the blob base fee.
"""

from functools import reduce
from typing import Dict, List

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    Conditional,
    Environment,
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

BASE_FEE = 7
"""Base fee of the block the probed transaction lands in."""

MAX_PRIORITY_FEE = 3
"""A tip, so the escrow includes the largest tip the budget allows."""

MAX_FEE = 1_000_000_000
"""A `max_fee` budget the worst case never reaches, distinct from other
fields."""

SENDER_FUNDS = 10**18
"""Sender balance before the transaction, which pays and escrows."""

PROBE_FRAME_STATE_GAS = 1_000_000
"""State budget of the probe frame, above the framework default, which
the storage slot the probe creates per read would exhaust."""

SLOT_BLOB_COUNT = 0x01
SLOT_MAX_FEE = 0x02
SLOT_ESCROW = 0x03
SLOT_FIRST_BLOBHASH = 0x10
"""`BLOBHASH(i)` is stored at `SLOT_FIRST_BLOBHASH + i`, one index past
the last blob included."""


def blob_versioned_hashes(count: int) -> List[Hash]:
    """Return `count` versioned hashes for the probed transaction."""
    return add_kzg_version(
        list(range(1, count + 1)), BLOB_COMMITMENT_VERSION_KZG
    )


def escrow(fork: Fork, tx: Transaction) -> int:
    """
    Return what the payer of a signed frame transaction escrows: its
    maximum gas at the base fee plus its blob gas at the blob base fee of
    an empty excess, the worst case, plus the largest tip the rest of the
    `max_fee` budget allows.
    """
    tx.sign()
    assert tx.frames is not None and tx.signatures is not None
    assert tx.blob_versioned_hashes is not None
    assert tx.max_fee is not None and tx.max_priority_fee_per_gas is not None
    max_gas = fork.frame_transaction_intrinsic_cost_calculator()(
        frames=tx.frames, signatures=tx.signatures
    )
    blob_gas = fork.blob_gas_per_blob() * len(tx.blob_versioned_hashes)
    blob_base_fee = fork.blob_gas_price_calculator()(excess_blob_gas=0)
    required_max_fee = max_gas * BASE_FEE + blob_gas * blob_base_fee
    return required_max_fee + min(
        int(tx.max_priority_fee_per_gas) * max_gas,
        int(tx.max_fee) - required_max_fee,
    )


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
    `TXPARAM` reports the blob count and the `max_fee` budget, and the
    sender's escrow includes the blob gas.
    """
    hashes = blob_versioned_hashes(BLOB_COUNT)
    probe_code = Bytecode()
    for index in range(len(hashes) + 1):
        probe_code += Op.SSTORE(
            SLOT_FIRST_BLOBHASH + index, Op.BLOBHASH(index)
        )
    probe_code += (
        Op.SSTORE(SLOT_BLOB_COUNT, Op.TXPARAM(Spec.TXPARAM_BLOB_COUNT))
        + Op.SSTORE(SLOT_MAX_FEE, Op.TXPARAM(Spec.TXPARAM_MAX_FEE))
        # The escrow stays out of the payer's balance until settlement.
        + Op.SSTORE(
            SLOT_ESCROW,
            Op.SUB(SENDER_FUNDS, Op.BALANCE(Op.TXPARAM(Spec.TXPARAM_SENDER))),
        )
        + Op.STOP
    )
    probe = pre.deploy_contract(code=probe_code)
    tx = Transaction(
        sender=pre.fund_eoa(amount=SENDER_FUNDS),
        max_fee=MAX_FEE,
        max_priority_fee_per_gas=MAX_PRIORITY_FEE,
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
    storage[SLOT_FIRST_BLOBHASH + len(hashes)] = 0
    storage[SLOT_BLOB_COUNT] = len(hashes)
    storage[SLOT_MAX_FEE] = MAX_FEE
    storage[SLOT_ESCROW] = escrow(fork, tx)
    state_test(
        env=Environment(base_fee_per_gas=BASE_FEE),
        pre=pre,
        tx=tx,
        post={probe: Account(storage=storage)},
    )


def test_blob_introspection_in_verify_frame(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Read the transaction's blobs from a `VERIFY` frame, which cannot
    store what it reads: the sender approves only when `BLOBHASH`
    returns each versioned hash and zero past the last one, and
    `TXPARAM` reports the blob count and the `max_fee` budget. The
    transaction is valid only if every read matches.
    """
    hashes = blob_versioned_hashes(BLOB_COUNT)
    checks = [
        # The index past the last blob reads zero.
        Op.ISZERO(Op.BLOBHASH(len(hashes))),
        # Each index reads its versioned hash.
        *[
            Op.EQ(Op.BLOBHASH(i), blob_hash)
            for i, blob_hash in enumerate(hashes)
        ],
        # The blob count and the budget read back as sent.
        Op.EQ(Op.TXPARAM(Spec.TXPARAM_BLOB_COUNT), len(hashes)),
        Op.EQ(Op.TXPARAM(Spec.TXPARAM_MAX_FEE), MAX_FEE),
    ]
    reads_match = reduce(Op.AND, checks)
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
        max_fee=MAX_FEE,
        blob_versioned_hashes=hashes,
        frames=[verify_frame()],
    )

    state_test(pre=pre, tx=tx, post={sender: Account(nonce=2)})
