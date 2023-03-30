"""
Ethereum test fork definitions.
"""

from typing import List, Type


class BaseFork:
    """
    An abstract class representing an Ethereum fork
    """

    @classmethod
    def header_base_fee_required(
        cls, block_number: int, timestamp: int
    ) -> bool:
        """
        Returns true if the header must contain withdrawals
        """
        return False

    @classmethod
    def header_prev_randao_required(
        cls, block_number: int, timestamp: int
    ) -> bool:
        """
        Returns true if the header must contain Prev Randao value
        """
        return False

    @classmethod
    def header_zero_difficulty_required(
        cls, block_number: int, timestamp: int
    ) -> bool:
        """
        Returns true if the header must have difficulty zero
        """
        return False

    @classmethod
    def header_withdrawals_required(
        cls, block_number: int, timestamp: int
    ) -> bool:
        """
        Returns true if the header must contain withdrawals
        """
        return False

    @classmethod
    def get_reward(cls, block_number: int, timestamp: int) -> int:
        """
        Returns the expected reward amount in wei of a given fork
        """
        return 2_000_000_000_000_000_000


# All forks must be listed here
class Frontier(BaseFork):
    """
    Frontier fork
    """

    pass


class Homestead(Frontier):
    """
    Homestead fork
    """

    pass


class Byzantium(Homestead):
    """
    Byzantium fork
    """

    pass


class Constantinople(Byzantium):
    """
    Constantinople fork
    """

    pass


class ConstantinopleFix(Constantinople):
    """
    Constantinople Fix fork
    """

    pass


class Istanbul(ConstantinopleFix):
    """
    Istanbul fork
    """

    pass


# Glacier forks skipped, unless explicitly specified
class MuirGlacier(Istanbul):
    """
    Muir Glacier fork
    """

    pass


class Berlin(Istanbul):
    """
    Berlin fork
    """

    pass


class London(Berlin):
    """
    London fork
    """

    @classmethod
    def header_base_fee_required(
        cls, block_number: int, timestamp: int
    ) -> bool:
        """
        Base Fee is required starting from London.
        """
        return True


# Glacier forks skipped, unless explicitly specified
class ArrowGlacier(London):
    """
    Arrow Glacier fork
    """

    pass


class GrayGlacier(ArrowGlacier):
    """
    Gray Glacier fork
    """

    pass


class Merge(London):
    """
    Merge fork
    """

    @classmethod
    def header_prev_randao_required(
        cls, block_number: int, timestamp: int
    ) -> bool:
        """
        Prev Randao is required starting from Merge.
        """
        return True

    @classmethod
    def header_zero_difficulty_required(
        cls, block_number: int, timestamp: int
    ) -> bool:
        """
        Zero difficulty is required starting from Merge.
        """
        return True

    @classmethod
    def get_reward(cls, block_number: int, timestamp: int) -> int:
        """
        Merge updates the reward to 0.
        """
        return 0


class Shanghai(Merge):
    """
    Shanghai fork
    """

    @classmethod
    def header_withdrawals_required(
        cls, block_number: int, timestamp: int
    ) -> bool:
        """
        Withdrawals are required starting from Shanghai.
        """
        return True


LatestFork = Shanghai

# Upcoming forks


# Transition Forks
class BerlinToLondonAt5(Berlin):
    """
    Berlin to London transition at Block 5 fork
    """

    @classmethod
    def header_base_fee_required(cls, block_number: int, _: int) -> bool:
        """
        Base Fee is required starting from London.
        """
        return block_number >= 5


class MergeToShanghaiAtTime15k(Merge):
    """
    Merge to Shanghai transition at Timestamp 15k fork
    """

    @classmethod
    def header_withdrawals_required(cls, _: int, timestamp: int) -> bool:
        """
        Withdrawals are required starting from Shanghai.
        """
        return timestamp >= 15_000


# Fork Type
Fork = Type[BaseFork]


# Fork helper methods
def forks_from_until(fork_from: Fork, fork_until: Fork) -> List[Fork]:
    """
    Returns the specified fork and all forks after it until and including the
    second specified fork
    """
    prev_fork = fork_until

    forks: List[Fork] = []

    while prev_fork != BaseFork and prev_fork != fork_from:
        forks.insert(0, prev_fork)

        prev_fork = prev_fork.__base__

    if prev_fork == BaseFork:
        raise Exception("Fork not found")

    forks.insert(0, fork_from)

    return forks


def forks_from(fork: Fork) -> List[Fork]:
    """
    Returns the specified fork and all forks after it
    """
    return forks_from_until(fork, LatestFork)


def is_fork(fork: Fork, which: Fork) -> bool:
    """
    Returns `True` if `fork` is `which` or beyond, `False otherwise.
    """
    prev_fork = fork

    while prev_fork != BaseFork:
        if prev_fork == which:
            return True

        prev_fork = prev_fork.__base__

    return False
