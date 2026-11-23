"""
The block's dependency proof (EIP-8288).

The proof travels in the execution payload, outside the block header and
body. The header commits to it with `dependency_proof_hash` and to the
block's deduplicated, sorted claims with `block_deps_hash`; both are
`keccak256(b"")` for a block without claims.

Blocks declaring claims carry genuine proofs under the pinned recursive
guest (see `helpers.stored_proof`). Their blockchain fixtures carry the
proof next to each block, outside its RLP, and their engine fixtures carry
it in the payload's `dependencyProof`.
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
    Hash,
    Header,
    Op,
    Transaction,
    keccak256,
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
    expected_commitment,
    ordered_dependencies_hash,
    stark_claim,
    stored_proof,
)
from .spec import Spec, ref_spec_8288

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
        pytest.param([[stark_claim(1)]], id="leanstark_claim"),
        pytest.param(
            [[claim(1), stark_claim(1)]], id="mixed_schemes_one_frame"
        ),
        pytest.param(
            [[claim(index, key=index % 16) for index in range(32)]],
            id="thirty_two_claims_sixteen_keys",
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
    block's transactions and to a proof of exactly those claims, or to
    the empty proof when the block declares none.
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
        blocks=[Block(txs=txs, header_verify=expected_commitment(all_claims))],
        post={recipient: Account(balance=1)},
    )


def test_zero_data_hash_is_signature_hash(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Prove a claim declared with a zero data hash over the transaction's
    signature hash, which the frame cannot carry itself.
    """
    key = claim(0)[2]
    tx = Transaction(
        sender=pre.fund_eoa(),
        frames=[
            dependency_frame(
                fork, [(Spec.LEANSPHINCS_SCHEME, bytes(32), key)]
            ),
            verify_frame(),
            sender_frame(target=pre.deploy_contract(code=Op.STOP)),
        ],
    )
    blockchain_test(pre=pre, blocks=[Block(txs=[tx])], post={})


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


@pytest.mark.exception_test
@pytest.mark.parametrize(
    "transaction_claims,block_deps_hash",
    [
        pytest.param(
            DECLARED,
            lambda: ordered_dependencies_hash(DECLARED_IN_ORDER),
            id="digest_in_declaration_order",
        ),
        pytest.param(
            DECLARED,
            lambda: ordered_dependencies_hash(sorted(DECLARED_IN_ORDER)),
            id="digest_with_duplicates",
        ),
        pytest.param(
            DECLARED,
            lambda: Hash(Spec.EMPTY_PROOF_HASH),
            id="empty_digest_with_claims",
        ),
        pytest.param(
            DECLARED,
            lambda: keccak256(
                b"".join(
                    data_hash + key
                    for _, data_hash, key in sorted(set(DECLARED_IN_ORDER))
                )
            ),
            id="digest_without_scheme_words",
        ),
        pytest.param(
            [[]], lambda: DECLARED_DIGEST, id="digest_without_claims"
        ),
    ],
)
def test_invalid_block_deps_hash(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    transaction_claims: List[List[Dependency]],
    block_deps_hash: Callable[[], Hash],
) -> None:
    """
    Reject a block whose `block_deps_hash` is not the digest of its
    deduplicated, sorted claims, whatever proof it carries.
    """
    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=block_transactions(pre, fork, transaction_claims),
                rlp_modifier=Header(block_deps_hash=block_deps_hash()),
                # An engine payload carries no `block_deps_hash`: the client
                # derives it, so the payload's `blockHash` does not match.
                exception=[
                    BlockException.INVALID_BLOCK_DEPS_HASH,
                    BlockException.INVALID_BLOCK_HASH,
                ],
            )
        ],
        post={},
    )


def flipped(data: Bytes, index: int) -> Bytes:
    """Return `data` with one bit of the byte at `index` flipped."""
    return Bytes(data[:index] + bytes([data[index] ^ 1]) + data[index + 1 :])


ProofBuilder = Callable[[], Bytes]
"""Build a case's payload proof, reading stored proofs only when it fills."""


@pytest.mark.blockchain_test_engine_only
@pytest.mark.exception_test
@pytest.mark.parametrize(
    "transaction_claims,proof",
    [
        pytest.param(
            DECLARED,
            lambda: Bytes(stored_proof(DECLARED_IN_ORDER) + b"\x00"),
            id="trailing_byte",
        ),
        pytest.param(
            DECLARED,
            lambda: Bytes(stored_proof(DECLARED_IN_ORDER)[:-1]),
            id="truncated_proof",
        ),
        pytest.param(
            DECLARED,
            lambda: flipped(
                stored_proof(DECLARED_IN_ORDER),
                len(stored_proof(DECLARED_IN_ORDER)) // 2,
            ),
            id="corrupted_proof",
        ),
        pytest.param(
            DECLARED,
            lambda: stored_proof([claim(1)]),
            id="proof_of_other_claims",
        ),
        pytest.param(
            DECLARED,
            lambda: stored_proof([*DECLARED_IN_ORDER, claim(4)]),
            id="proof_of_superset",
        ),
        pytest.param(DECLARED, lambda: Bytes(b""), id="empty_proof"),
        pytest.param(
            DECLARED,
            lambda: Bytes(b"\x00" * (Spec.MAX_DEPENDENCY_PROOF_BYTES + 1)),
            id="oversized_proof",
        ),
        pytest.param([[]], lambda: Bytes(b"\x01"), id="proof_without_claims"),
        pytest.param(
            [[]],
            lambda: stored_proof([claim(1)]),
            id="genuine_proof_without_claims",
        ),
    ],
)
def test_invalid_dependency_proof(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    transaction_claims: List[List[Dependency]],
    proof: ProofBuilder,
) -> None:
    """
    Reject a block whose payload proof the header commits to but which
    does not verify against `block_deps_hash`, is longer than
    `MAX_DEPENDENCY_PROOF_BYTES`, or is not empty without claims.
    """
    payload_proof = proof()
    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=block_transactions(pre, fork, transaction_claims),
                rlp_modifier=Header(
                    dependency_proof_hash=keccak256(payload_proof)
                ),
                engine_new_payload_dependency_proof=payload_proof,
                exception=BlockException.INVALID_DEPENDENCY_PROOF,
            )
        ],
        post={},
    )


@pytest.mark.blockchain_test_engine_only
@pytest.mark.exception_test
@pytest.mark.parametrize(
    "transaction_claims", [pytest.param(DECLARED, id="with_claims")]
)
@pytest.mark.parametrize(
    "payload_proof",
    [
        pytest.param(None, id="missing_proof"),
        pytest.param(Bytes(b""), id="empty_proof"),
        pytest.param(Bytes(b"\x01"), id="other_proof"),
    ],
)
def test_payload_proof_not_committed(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    transaction_claims: List[List[Dependency]],
    payload_proof: Bytes | None,
) -> None:
    """
    Reject a payload whose `dependencyProof` is not the proof the header
    commits to, or is absent: the header the client derives from the
    payload does not hash to its `blockHash`.
    """
    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=block_transactions(pre, fork, transaction_claims),
                engine_new_payload_dependency_proof=payload_proof,
                engine_new_payload_without_dependency_proof=(
                    payload_proof is None
                ),
                exception=BlockException.INVALID_BLOCK_HASH,
            )
        ],
        post={},
    )


@pytest.mark.exception_test
@pytest.mark.parametrize(
    "transaction_claims",
    [
        pytest.param([[]], id="without_claims"),
        pytest.param(DECLARED, id="with_claims"),
    ],
)
def test_invalid_dependency_proof_hash(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    transaction_claims: List[List[Dependency]],
) -> None:
    """
    Reject a block whose `dependency_proof_hash` is not the hash of the
    proof it carries.
    """
    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=block_transactions(pre, fork, transaction_claims),
                rlp_modifier=Header(
                    dependency_proof_hash=keccak256(b"not the proof")
                ),
                # An engine payload carries no `dependency_proof_hash`: the
                # client derives it, so the payload's `blockHash` does not
                # match.
                exception=[
                    BlockException.INVALID_DEPENDENCY_PROOF_HASH,
                    BlockException.INVALID_BLOCK_HASH,
                ],
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
            header_verify=expected_commitment(claims),
        )
        for claims in block_claims
    ]
    blockchain_test(pre=pre, blocks=blocks, post={})
