"""
The block's recursive STARK (EIP-8288): the header commits to the
deduplicated, sorted claims of every transaction in the block, and
carries an empty proof when there are none.

Blocks declaring claims carry genuine proofs under the pinned recursive
guest, generated ahead of filling (see `helpers.stored_proof`).
"""

from typing import Callable, List

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    BlockException,
    Bytes,
    Fork,
    Header,
    Op,
    RecursiveStark,
    Transaction,
)

from tests.bogota.eip8141_frame_transactions.helpers import (
    sender_frame,
    verify_frame,
)

from .helpers import (
    Dependency,
    claim,
    dependencies_hash,
    dependency_frame,
    expected_recursive_stark,
    ordered_dependencies_hash,
    stored_proof,
)
from .spec import ref_spec_8288

REFERENCE_SPEC_GIT_PATH = ref_spec_8288.git_path
REFERENCE_SPEC_VERSION = ref_spec_8288.version

pytestmark = pytest.mark.valid_from("EIP8288")


def block_transactions(
    pre: Alloc, fork: Fork, transaction_claims: List[List[Dependency]]
) -> List[Transaction]:
    """
    Return one frame transaction per entry of `transaction_claims`, each
    declaring its claims in one dependency frame, or none when empty.
    """
    noop = pre.deploy_contract(code=Op.STOP)
    txs = []
    for claims in transaction_claims:
        frames = [verify_frame(), sender_frame(target=noop)]
        if claims:
            frames.insert(0, dependency_frame(fork, claims))
        txs.append(Transaction(sender=pre.fund_eoa(), frames=frames))
    return txs


@pytest.mark.parametrize(
    "transaction_claims",
    [
        pytest.param([], id="no_transactions"),
        pytest.param([[]], id="frame_transaction_without_claims"),
        pytest.param([[claim(1)]], id="one_claim"),
        pytest.param(
            [[claim(3), claim(2), claim(1)]], id="descending_declarations"
        ),
        pytest.param(
            [[claim(1), claim(1, key=1)]], id="same_message_other_keys"
        ),
        pytest.param(
            [[claim(2), claim(1)], [claim(1), claim(3)]],
            id="shared_across_transactions",
        ),
        pytest.param([[claim(1)], [claim(1)]], id="identical_transactions"),
        pytest.param(
            [[], [claim(2)], [], [claim(1)]],
            id="interleaved_with_claimless",
        ),
    ],
)
def test_block_commits_to_claims(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    transaction_claims: List[List[Dependency]],
) -> None:
    """
    Commit the header to the deduplicated, sorted claims of all the
    block's transactions, with a proof of exactly those claims,
    or an empty proof when the block declares none.
    """
    legacy_sender = pre.fund_eoa()
    recipient = pre.fund_eoa(amount=0)
    txs = [
        Transaction(sender=legacy_sender, to=recipient, value=1),
        *block_transactions(pre, fork, transaction_claims),
    ]
    all_claims = [
        dependency for claims in transaction_claims for dependency in claims
    ]
    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=txs,
                header_verify=Header(
                    recursive_stark=expected_recursive_stark(all_claims)
                ),
            )
        ],
        post={recipient: Account(balance=1)},
    )


DECLARED = [[claim(2), claim(1)], [claim(1)]]
"""
Claims of the block the rejection cases modify: declared out of order
and with a duplicate, so neither declaration order nor duplicates
survive into the digest.
"""

DECLARED_IN_ORDER = [
    dependency for claims in DECLARED for dependency in claims
]
DECLARED_DIGEST = dependencies_hash(DECLARED_IN_ORDER)


def flipped(data: Bytes, index: int) -> Bytes:
    """Return `data` with one bit of the byte at `index` flipped."""
    return Bytes(data[:index] + bytes([data[index] ^ 1]) + data[index + 1 :])


def malformed_proof(part: str) -> Bytes:
    """Alter a wire boundary or a deferred claim in a genuine block proof."""
    proof = stored_proof(DECLARED_IN_ORDER)
    if part == "trailing_byte":
        return Bytes(proof + b"\x00")
    if part == "oversized_point":
        return Bytes((2**64 - 1).to_bytes(8, "little") + proof[8:])

    # Three length-prefixed F192 vectors precede the scalar stream.
    vectors = ["bytecode_point", "blake_matrix", "keccak_matrix", "sizes"]
    offset = 0
    for vector in vectors:
        length = int.from_bytes(proof[offset : offset + 8], "little")
        offset += 8
        if part == vector:
            # Sizes must be base-field integers, with zero upper limbs.
            return flipped(proof, offset + (8 if part == "sizes" else 0))
        offset += 24 * length
    raise ValueError(f"unknown proof part: {part}")


EntryBuilder = Callable[[], RecursiveStark]
"""Build a case's header entry, reading stored proofs only when it fills."""

INVALID_ENTRIES = [
    *[
        pytest.param(
            DECLARED,
            lambda part=part: RecursiveStark(
                stark_proof=malformed_proof(part),
                block_deps_hash=DECLARED_DIGEST,
            ),
            BlockException.INVALID_RECURSIVE_STARK,
            id=part,
        )
        for part in (
            "trailing_byte",
            "oversized_point",
            "bytecode_point",
            "blake_matrix",
            "keccak_matrix",
            "sizes",
        )
    ],
    pytest.param(
        DECLARED,
        lambda: RecursiveStark(
            stark_proof=stored_proof(DECLARED_IN_ORDER),
            block_deps_hash=ordered_dependencies_hash(DECLARED_IN_ORDER),
        ),
        BlockException.INVALID_BLOCK_DEPS_HASH,
        id="digest_in_declaration_order",
    ),
    pytest.param(
        DECLARED,
        lambda: RecursiveStark(
            stark_proof=stored_proof(DECLARED_IN_ORDER),
            block_deps_hash=ordered_dependencies_hash(
                sorted(DECLARED_IN_ORDER)
            ),
        ),
        BlockException.INVALID_BLOCK_DEPS_HASH,
        id="digest_with_duplicates",
    ),
    pytest.param(
        DECLARED,
        lambda: RecursiveStark(),
        BlockException.INVALID_BLOCK_DEPS_HASH,
        id="empty_entry_with_claims",
    ),
    pytest.param(
        DECLARED,
        lambda: RecursiveStark(block_deps_hash=DECLARED_DIGEST),
        BlockException.INVALID_RECURSIVE_STARK,
        id="missing_proof",
    ),
    pytest.param(
        DECLARED,
        lambda: RecursiveStark(
            stark_proof=stored_proof(DECLARED_IN_ORDER)[:-1],
            block_deps_hash=DECLARED_DIGEST,
        ),
        BlockException.INVALID_RECURSIVE_STARK,
        id="truncated_proof",
    ),
    pytest.param(
        DECLARED,
        lambda: RecursiveStark(
            stark_proof=flipped(
                stored_proof(DECLARED_IN_ORDER),
                len(stored_proof(DECLARED_IN_ORDER)) // 2,
            ),
            block_deps_hash=DECLARED_DIGEST,
        ),
        BlockException.INVALID_RECURSIVE_STARK,
        id="corrupted_proof",
    ),
    pytest.param(
        DECLARED,
        lambda: RecursiveStark(
            stark_proof=stored_proof([claim(1)]),
            block_deps_hash=DECLARED_DIGEST,
        ),
        BlockException.INVALID_RECURSIVE_STARK,
        id="proof_of_other_claims",
    ),
    pytest.param(
        [[]],
        lambda: RecursiveStark(stark_proof=Bytes(b"\x01")),
        BlockException.INVALID_RECURSIVE_STARK,
        id="proof_without_claims",
    ),
    pytest.param(
        [[]],
        lambda: RecursiveStark(block_deps_hash=DECLARED_DIGEST),
        BlockException.INVALID_BLOCK_DEPS_HASH,
        id="digest_without_claims",
    ),
]
"""
Header entries breaking one rule each. A digest over the claims in
declaration order or with duplicates is not the block's, even with a
genuine proof of the block's claims behind it.
"""


@pytest.mark.exception_test
@pytest.mark.parametrize("transaction_claims,entry,exception", INVALID_ENTRIES)
def test_invalid_recursive_stark(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    transaction_claims: List[List[Dependency]],
    entry: EntryBuilder,
    exception: BlockException,
) -> None:
    """
    Reject a block whose header entry does not commit to its claims, or
    whose proof does not verify against the entry's digest.
    """
    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=block_transactions(pre, fork, transaction_claims),
                rlp_modifier=Header(recursive_stark=entry()),
                exception=exception,
            )
        ],
        post={},
    )


def test_dependencies_reset_between_blocks(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Require each block's proof to cover only that block's claims."""
    block_claims = [[claim(1)], [], [claim(1), claim(2)], []]
    blocks = [
        Block(
            txs=block_transactions(pre, fork, [claims]) if claims else [],
            header_verify=Header(
                recursive_stark=expected_recursive_stark(claims)
            ),
        )
        for claims in block_claims
    ]
    blockchain_test(pre=pre, blocks=blocks, post={})
