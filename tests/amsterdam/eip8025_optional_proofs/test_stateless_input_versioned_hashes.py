"""Stateless input blob versioned-hash validation tests."""

from dataclasses import replace
from typing import Any, Callable, Tuple

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytes,
    Fork,
    Transaction,
    add_kzg_version,
)

from .gas_helpers import empty_account_value_transfer_gas_limit

pytestmark = pytest.mark.valid_from("Amsterdam")

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

StatelessInputBytesModifier = Callable[[Bytes], Bytes]
VersionedHashesBuilder = Callable[[Tuple[Any, ...]], Tuple[Any, ...]]

# Version byte prefixed to every blob versioned hash.
BLOB_COMMITMENT_VERSION_KZG = 1

# The canonical block below carries two blob transactions: the first
# declares two blobs, the second declares one. The declared versioned hash
# tuple is therefore three entries long, with the transaction boundary
# between index 1 and index 2.
FIRST_TRANSACTION_BLOB_HASHES = add_kzg_version(
    [0, 1], BLOB_COMMITMENT_VERSION_KZG
)
SECOND_TRANSACTION_BLOB_HASHES = add_kzg_version(
    [2], BLOB_COMMITMENT_VERSION_KZG
)
CANONICAL_BLOB_HASH_COUNT = len(FIRST_TRANSACTION_BLOB_HASHES) + len(
    SECOND_TRANSACTION_BLOB_HASHES
)

# A KZG-versioned hash no canonical blob transaction declares.
UNRELATED_BLOB_HASH = add_kzg_version([0xFF], BLOB_COMMITMENT_VERSION_KZG)[0]


def replace_versioned_hashes(
    build_versioned_hashes: VersionedHashesBuilder,
) -> StatelessInputBytesModifier:
    """
    Replace only the declared new payload request versioned hashes.

    Everything else the guest validates -- execution payload, block hash,
    witness, chain config, and transaction public keys -- is preserved, and
    the result is re-serialized as valid SSZ. A validation failure is
    therefore attributable to the versioned hash cross-check rather than to
    a decoding error or to some other validation step.
    """

    def modifier(input_bytes: Bytes) -> Bytes:
        from ethereum_types.bytes import Bytes as AmsterdamBytes

        from ethereum.forks.amsterdam.stateless_guest import (
            deserialize_stateless_input,
        )
        from ethereum.forks.amsterdam.stateless_host import (
            serialize_stateless_input,
        )

        stateless_input = deserialize_stateless_input(
            AmsterdamBytes(bytes(input_bytes))
        )
        new_payload_request = stateless_input.new_payload_request
        modified_input = replace(
            stateless_input,
            new_payload_request=replace(
                new_payload_request,
                versioned_hashes=build_versioned_hashes(
                    tuple(new_payload_request.versioned_hashes)
                ),
            ),
        )
        return Bytes(bytes(serialize_stateless_input(modified_input)))

    return modifier


def assert_hash_count(
    versioned_hashes: Tuple[Any, ...],
    expected_count: int,
) -> None:
    """
    Assert the canonical declared hash count before mutating it.

    Without this, a change that stops deriving the hashes from the block
    would turn every mutation below into a silent no-op.
    """
    if len(versioned_hashes) != expected_count:
        raise AssertionError(
            f"expected {expected_count} canonical versioned hashes, "
            f"got {len(versioned_hashes)}"
        )


def swapped(
    versioned_hashes: Tuple[Any, ...],
    first: int,
    second: int,
) -> Tuple[Any, ...]:
    """Return the hashes with two entries exchanged."""
    swapped_hashes = list(versioned_hashes)
    swapped_hashes[first], swapped_hashes[second] = (
        swapped_hashes[second],
        swapped_hashes[first],
    )
    return tuple(swapped_hashes)


def unchanged_hashes(
    versioned_hashes: Tuple[Any, ...],
) -> Tuple[Any, ...]:
    """Rebuild the canonical hashes unchanged."""
    assert_hash_count(versioned_hashes, CANONICAL_BLOB_HASH_COUNT)
    return versioned_hashes


def replaced_hash(
    versioned_hashes: Tuple[Any, ...],
) -> Tuple[Any, ...]:
    """Overwrite the first declared hash with an unrelated one."""
    assert_hash_count(versioned_hashes, CANONICAL_BLOB_HASH_COUNT)
    return (UNRELATED_BLOB_HASH,) + versioned_hashes[1:]


def removed_hash(
    versioned_hashes: Tuple[Any, ...],
) -> Tuple[Any, ...]:
    """Drop the first declared hash."""
    assert_hash_count(versioned_hashes, CANONICAL_BLOB_HASH_COUNT)
    return versioned_hashes[1:]


def extra_hash(
    versioned_hashes: Tuple[Any, ...],
) -> Tuple[Any, ...]:
    """Append a hash no blob transaction declares."""
    assert_hash_count(versioned_hashes, CANONICAL_BLOB_HASH_COUNT)
    return versioned_hashes + (UNRELATED_BLOB_HASH,)


def cleared_hashes(
    versioned_hashes: Tuple[Any, ...],
) -> Tuple[Any, ...]:
    """Declare no hashes at all despite the payload carrying blobs."""
    assert_hash_count(versioned_hashes, CANONICAL_BLOB_HASH_COUNT)
    return ()


def reordered_within_transaction(
    versioned_hashes: Tuple[Any, ...],
) -> Tuple[Any, ...]:
    """Exchange the two hashes belonging to the first blob transaction."""
    assert_hash_count(versioned_hashes, CANONICAL_BLOB_HASH_COUNT)
    return swapped(versioned_hashes, 0, 1)


def reordered_across_transactions(
    versioned_hashes: Tuple[Any, ...],
) -> Tuple[Any, ...]:
    """Exchange hashes across the blob transaction boundary."""
    assert_hash_count(versioned_hashes, CANONICAL_BLOB_HASH_COUNT)
    return swapped(versioned_hashes, 1, 2)


def sole_unrelated_hash(
    versioned_hashes: Tuple[Any, ...],
) -> Tuple[Any, ...]:
    """Declare one hash for a payload that carries no blob transactions."""
    assert_hash_count(versioned_hashes, 0)
    return (UNRELATED_BLOB_HASH,)


@pytest.mark.parametrize(
    "build_versioned_hashes,expected_validation_success",
    [
        pytest.param(unchanged_hashes, True, id="unchanged_hashes"),
        pytest.param(replaced_hash, False, id="replaced_hash"),
        pytest.param(removed_hash, False, id="removed_hash"),
        pytest.param(extra_hash, False, id="extra_hash"),
        pytest.param(cleared_hashes, False, id="cleared_hashes"),
        pytest.param(
            reordered_within_transaction,
            False,
            id="reordered_within_transaction",
        ),
        pytest.param(
            reordered_across_transactions,
            False,
            id="reordered_across_transactions",
        ),
    ],
)
def test_stateless_input_versioned_hashes(
    fork: Fork,
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    build_versioned_hashes: VersionedHashesBuilder,
    expected_validation_success: bool,
) -> None:
    """
    Declared versioned hashes must match the payload's blob transactions.

    The guest recomputes the hashes from the blob transactions in the
    payload and compares the ordered sequence against the hashes the
    consensus layer declared. Only the unmodified sequence validates: a
    changed, missing, extra, or reordered entry must be rejected, and the
    reordering cases fail even though the declared multiset is unchanged.
    """
    recipient = pre.fund_eoa(amount=0)
    first_sender = pre.fund_eoa()
    second_sender = pre.fund_eoa()
    first_tx = Transaction(
        ty=3,
        sender=first_sender,
        to=recipient,
        max_fee_per_blob_gas=fork.min_base_fee_per_blob_gas(),
        blob_versioned_hashes=FIRST_TRANSACTION_BLOB_HASHES,
    )
    second_tx = Transaction(
        ty=3,
        sender=second_sender,
        to=recipient,
        max_fee_per_blob_gas=fork.min_base_fee_per_blob_gas(),
        blob_versioned_hashes=SECOND_TRANSACTION_BLOB_HASHES,
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[first_tx, second_tx],
                # The rerun always goes through a modifier, including the
                # unchanged case: a bytes modifier is what forces the
                # filler to rerun the guest instead of trusting the
                # validation flag the artifact builder may hardcode.
                stateless_input_bytes_modifier=replace_versioned_hashes(
                    build_versioned_hashes
                ),
                expected_stateless_validation_success=(
                    expected_validation_success
                ),
            )
        ],
        post={
            first_sender: Account(nonce=1),
            second_sender: Account(nonce=1),
        },
    )


def test_stateless_input_versioned_hashes_without_blob_transactions(
    fork: Fork,
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    A payload carrying no blob transactions must declare no hashes.

    This catches guests that skip the cross-check when the payload has
    nothing to recompute the hashes from.
    """
    sender = pre.fund_eoa()
    recipient = pre.fund_eoa(amount=0)
    tx = Transaction(
        sender=sender,
        to=recipient,
        value=1,
        gas_limit=empty_account_value_transfer_gas_limit(fork),
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                stateless_input_bytes_modifier=replace_versioned_hashes(
                    sole_unrelated_hash
                ),
                expected_stateless_validation_success=False,
            )
        ],
        post={
            sender: Account(nonce=1),
            recipient: Account(balance=1),
        },
    )
