"""
Unit tests for the parallel spec-doc shard planner.
"""

from ethereum_spec_tools.docc_shards import compute_shards
from ethereum_spec_tools.forks import Hardfork


def test_shards_cover_every_fork() -> None:
    """Every fork lands in at least one shard."""
    forks = [f"f{i}" for i in range(24)]
    shards = compute_shards(forks, 4)
    covered = {fork for shard in shards for fork in shard}
    assert covered == set(forks)


def test_shards_are_contiguous_with_one_fork_overlap() -> None:
    """Shards tile the range in order, overlapping one fork per seam."""
    forks = [f"f{i}" for i in range(24)]
    assert compute_shards(forks, 4) == [
        forks[0:6],
        forks[5:12],
        forks[11:18],
        forks[17:24],
    ]


def test_each_fork_shares_a_shard_with_its_predecessor() -> None:
    """The overlap keeps every fork beside its immediate predecessor."""
    forks = [f"f{i}" for i in range(24)]
    shards = compute_shards(forks, 4)
    for i in range(1, len(forks)):
        assert any(
            forks[i] in shard and forks[i - 1] in shard for shard in shards
        )


def test_more_shards_than_forks_still_covers_all() -> None:
    """Requesting more shards than forks leaves no fork uncovered."""
    shards = compute_shards(["a", "b", "c"], 4)
    covered = {fork for shard in shards for fork in shard}
    assert covered == {"a", "b", "c"}


def test_real_fork_set_is_fully_covered() -> None:
    """The discovered fork set shards without dropping any fork."""
    forks = [fork.short_name for fork in Hardfork.discover()]
    shards = compute_shards(forks, 4)
    covered = {fork for shard in shards for fork in shard}
    assert covered == set(forks)
