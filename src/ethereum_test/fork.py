"""
List of all Ethereum forks.
"""

from typing import List

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
]


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
    try:
        i = forks.index(fork.lower())
    except ValueError:
        return False
    return i >= forks.index("london")
