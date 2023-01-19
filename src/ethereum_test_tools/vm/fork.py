"""
Ethereum fork definitions.
"""

from copy import copy
from typing import List

from ..common import Environment

forks = [
    "frontier",
    "homestead",
    "dao",
    "tangerine whistle",
    "spurious dragon",
    "byzantium",
    "constantinople",
    "petersburg",
    "istanbul",
    "muir glacier",
    "berlin",
    "london",
    "arrow glacier",
    "merge",
    "shanghai",
]


def forks_from_until(fork_from: str, fork_until: str) -> List[str]:
    """
    Returns the specified fork and all forks after it until and including the
    second specified fork
    """
    out = forks[
        forks.index(fork_from.strip().lower()) : forks.index(
            fork_until.strip().lower()
        )
    ]
    return list(map(lambda x: x, out))


def forks_from(fork: str) -> List[str]:
    """
    Returns the specified fork and all forks after it
    """
    out = forks[forks.index(fork.strip().lower()) :]
    return list(map(lambda x: x, out))


def is_london(fork: str) -> bool:
    """
    Returns `True` if `fork` is London-compatible, `False` otherwise.
    """
    fork_lower = fork.lower()
    if fork_lower not in forks:
        return False

    i = forks.index(fork_lower)
    return i >= forks.index("london")


def is_merge(fork: str) -> bool:
    """
    Returns `True` if `fork` is Merge-compatible, `False` otherwise.
    """
    fork_lower = fork.lower()
    if fork_lower not in forks:
        return False

    i = forks.index(fork_lower)
    return i >= forks.index("merge")


def is_shanghai(fork: str) -> bool:
    """
    Returns `True` if `fork` is Shanghai-compatible, `False` otherwise.
    """
    fork_lower = fork.lower()
    if fork_lower not in forks:
        return False

    i = forks.index(fork_lower)
    return i >= forks.index("shanghai")


def is_fork(fork: str, which: str) -> bool:
    """
    Returns `True` if `fork` is `which` or beyond, `False otherwise.
    """
    fork_lower = fork.lower()
    if fork_lower not in forks:
        return False

    i = forks.index(fork_lower)
    return i >= forks.index(which.lower())


def get_reward(fork: str) -> int:
    """
    Returns the expected reward amount in wei of a given fork
    """
    return 0 if is_merge(fork) else 2000000000000000000


def must_have_zero_difficulty(fork: str) -> bool:
    """
    Returns `True` if the environment is expected to have `difficulty==0`
    """
    return is_merge(fork)


def must_contain_prev_randao(fork: str) -> bool:
    """
    Returns `True` if the environment is expected to have `currentRandom` value
    """
    return is_merge(fork)


def must_contain_base_fee(fork: str) -> bool:
    """
    Returns `True` if the environment is expected to have `currentBaseFee`
    value
    """
    return is_london(fork)


def must_contain_withdrawals(fork: str) -> bool:
    """
    Returns `True` if the environment is expected to have withdrawals
    """
    return is_shanghai(fork)


default_base_fee = 7


def set_fork_requirements(env: Environment, fork: str) -> Environment:
    """
    Fills the required fields in an environment depending on the fork.
    """
    res = copy(env)

    if must_contain_prev_randao(fork) and res.prev_randao is None:
        res.prev_randao = 0

    if must_contain_withdrawals(fork) and res.withdrawals is None:
        res.withdrawals = []

    if (
        must_contain_base_fee(fork)
        and res.base_fee is None
        and res.parent_base_fee is None
    ):
        res.base_fee = default_base_fee

    if must_have_zero_difficulty(fork):
        res.difficulty = 0

    return res
