"""Test suite for blobs."""

import copy

import pytest

from ethereum_test_forks import (
    Cancun,
    Osaka,
    Prague,
)
from ethereum_test_forks.forks.transition import (
    CancunToPragueAtTime15k,
    PragueToOsakaAtTime15k,
    ShanghaiToCancunAtTime15k,
)

from ..blob_types import CACHED_BLOBS_DIRECTORY, Blob, clear_blob_cache


@pytest.mark.parametrize("seed", [0, 10, 100])
@pytest.mark.parametrize("fork", [Cancun, Prague, Osaka])
def test_blob_creation_and_writing_and_reading(
    seed,
    fork,
):  # noqa: F811
    """
    Generates blobs for different forks and ensures writing to file
    and reading from file works as expected.
    """
    timestamp = 100
    b = Blob.from_fork(fork=fork, seed=seed, timestamp=timestamp)
    b.write_to_file()

    # read from file
    #       determine what filename would be
    cell_proof_amount = str(fork.get_blob_constant("AMOUNT_CELL_PROOFS"))
    file_name = "blob_" + str(seed) + "_cell_proofs_" + cell_proof_amount + ".json"
    #       read
    restored = Blob.from_file(file_name)

    # ensure file you read equals file you wrote
    assert b.model_dump() == restored.model_dump()


@pytest.mark.parametrize(
    "corruption_mode",
    [
        Blob.ProofCorruptionMode.CORRUPT_ALL_BYTES,
        Blob.ProofCorruptionMode.CORRUPT_FIRST_BYTE,
        Blob.ProofCorruptionMode.CORRUPT_LAST_BYTE,
        Blob.ProofCorruptionMode.CORRUPT_TO_ALL_ZEROES,
    ],
)
@pytest.mark.parametrize("fork", [Cancun, Prague, Osaka])
def test_blob_proof_corruption(
    corruption_mode,
    fork,
):
    """
    Generates blobs for different forks, corrupts their proofs and ensures that
    the corrupted proof is not equal to the correct proof.
    """
    timestamp = 100
    b = Blob.from_fork(fork=fork, timestamp=timestamp)
    old_valid_proof = copy.deepcopy(b.proof)  # important to deepcopy

    b.corrupt_proof(corruption_mode)
    assert b.proof != old_valid_proof, (
        f"Proof corruption mode {corruption_mode} for fork {fork.name()} failed, "
        "proof is unchanged!"
    )


@pytest.mark.parametrize("timestamp", [14999, 15000])
@pytest.mark.parametrize(
    "fork", [ShanghaiToCancunAtTime15k, CancunToPragueAtTime15k, PragueToOsakaAtTime15k]
)
def test_transition_fork_blobs(
    fork,
    timestamp,
):
    """Generates blobs for transition forks (time 14999 is old fork, time 15000 is new fork)."""
    clear_blob_cache(CACHED_BLOBS_DIRECTORY)

    print(f"Original fork: {fork}, Timestamp: {timestamp}")
    pre_transition_fork = fork.transitions_from()
    post_transition_fork_at_15k = fork.transitions_to()  # only reached if timestamp >= 15000

    if not pre_transition_fork.supports_blobs() and timestamp < 15000:
        print(
            f"Skipping blob creation because pre-transition fork is {pre_transition_fork} "
            f"and timestamp is {timestamp}"
        )
        return

    # b has already applied transition if requirements were met
    b = Blob.from_fork(fork=fork, timestamp=timestamp)
    print(f"Fork of created blob: {b.fork.name()}")

    if timestamp == 14999:  # case: no transition yet
        assert b.fork.name() == pre_transition_fork.name(), (
            f"Transition fork failure! Fork {fork.name()} at timestamp: {timestamp} should have "
            f"stayed at fork {pre_transition_fork.name()} but has unexpectedly transitioned "
            f"to {b.fork.name()}"
        )
    elif timestamp == 15000:  # case: transition to next fork has happened
        assert b.fork.name() == post_transition_fork_at_15k.name(), (
            f"Transition fork failure! Fork {fork.name()} at timestamp: {timestamp} should have "
            f"transitioned to {post_transition_fork_at_15k.name()} but is still at {b.fork.name()}"
        )
