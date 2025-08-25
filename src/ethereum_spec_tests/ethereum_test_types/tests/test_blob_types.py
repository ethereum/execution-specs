"""Test suite for blobs."""

import copy
import time

import pytest
from filelock import FileLock

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


def increment_counter(timeout: float = 10):
    """
    Increment counter in file, creating if doesn't exist.

    This is needed because we require the unit test 'test_transition_fork_blobs' to run
    at the end without having to include another dependency for ordering tests.
    That test has to run at the end because it assumes that no json blobs not created
    by itself are created while it is running.

    The hardcoded counter value in the test above has to be updated if any new blob_related
    unit tests that create json blobs are added in the future.

    """
    file_path = CACHED_BLOBS_DIRECTORY / "blob_unit_test_counter.txt"
    lock_file = file_path.with_suffix(".lock")

    with FileLock(lock_file, timeout=timeout):
        # Read current value or start at 0
        if file_path.exists():
            current_value = int(file_path.read_text().strip())
        else:
            current_value = 0

        # Increment and write back
        new_value = current_value + 1
        file_path.write_text(str(new_value))

        return new_value


def wait_until_counter_reached(target: int, poll_interval: float = 0.1):
    """Wait until blob unit test counter reaches target value."""
    file_path = CACHED_BLOBS_DIRECTORY / "blob_unit_test_counter.txt"
    lock_file = file_path.with_suffix(".lock")  # Add lock file path

    while True:
        # Use FileLock when reading!
        with FileLock(lock_file, timeout=10):
            if file_path.exists():
                try:
                    current_value = int(file_path.read_text().strip())
                    if current_value == target:
                        # file_path.unlink()  # get rid to effectively reset counter to 0
                        return current_value
                    elif current_value > target:
                        pytest.fail(
                            f"The blob_unit_test lock counter is too high! "
                            f"Expected {target}, but got {current_value}. "
                            f"It probably reused an existing file that was not cleared. "
                            f"Delete {file_path} manually to fix this."
                        )
                except Exception:
                    current_value = 0
            else:
                current_value = 0

        time.sleep(poll_interval)


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

    increment_counter()


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

    increment_counter()


@pytest.mark.parametrize("timestamp", [14999, 15000])
@pytest.mark.parametrize(
    "fork", [ShanghaiToCancunAtTime15k, CancunToPragueAtTime15k, PragueToOsakaAtTime15k]
)
def test_transition_fork_blobs(
    fork,
    timestamp,
):
    """Generates blobs for transition forks (time 14999 is old fork, time 15000 is new fork)."""
    # line below guarantees that this test runs only after the other blob unit tests are done
    wait_until_counter_reached(21)

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

    # delete counter at last iteration (otherwise re-running all unit tests will fail)
    if timestamp == 15_000 and pre_transition_fork == Prague:
        (CACHED_BLOBS_DIRECTORY / "blob_unit_test_counter.txt").unlink()
