"""
Ethereum test fork definitions.
"""

from typing import List, Type


class Fork:
    """
    An abstract class representing an Ethereum fork
    """

    @classmethod
    def header_base_fee_required(
        self, block_number: int, timestamp: int
    ) -> bool:
        """
        Returns true if the header must contain withdrawals
        """
        return False

    @classmethod
    def header_prev_randao_required(
        self, block_number: int, timestamp: int
    ) -> bool:
        """
        Returns true if the header must contain PrevRandao value
        """
        return False

    @classmethod
    def header_zero_difficulty_required(
        self, block_number: int, timestamp: int
    ) -> bool:
        """
        Returns true if the header must have difficulty zero
        """
        return False

    @classmethod
    def header_withdrawals_required(
        self, block_number: int, timestamp: int
    ) -> bool:
        """
        Returns true if the header must contain withdrawals
        """
        return False

    @classmethod
    def get_reward(self, block_number: int, timestamp: int) -> int:
        """
        Returns the expected reward amount in wei of a given fork
        """
        return 2_000_000_000_000_000_000


# All forks must be listed here
class Frontier(Fork):
    pass


class Homestead(Frontier):
    pass


class Byzantium(Homestead):
    pass


class Constantinople(Byzantium):
    pass


class ConstantinopleFix(Constantinople):
    pass


class Istanbul(ConstantinopleFix):
    pass


# Glacier forks skipped, unless explicitly specified
class MuirGlacier(Istanbul):
    pass


class Berlin(Istanbul):
    pass


class London(Berlin):
    @classmethod
    def header_base_fee_required(
        self, block_number: int, timestamp: int
    ) -> bool:
        """
        Base Fee is required starting from London.
        """
        return True


# Glacier forks skipped, unless explicitly specified
class ArrowGlacier(London):
    pass


class GrayGlacier(ArrowGlacier):
    pass


class Merge(London):
    @classmethod
    def header_prev_randao_required(
        self, block_number: int, timestamp: int
    ) -> bool:
        """
        PrevRandao is required starting from Merge.
        """
        return True

    @classmethod
    def header_zero_difficulty_required(
        self, block_number: int, timestamp: int
    ) -> bool:
        """
        Zero difficulty is required starting from Merge.
        """
        return True

    @classmethod
    def get_reward(self, block_number: int, timestamp: int) -> int:
        """
        Merge updates the reward to 0.
        """
        return 0


class Shanghai(Merge):
    @classmethod
    def header_withdrawals_required(
        self, block_number: int, timestamp: int
    ) -> bool:
        """
        Withdrawals are required starting from Shanghai.
        """
        return True


LatestFork = Shanghai

# Upcoming forks


# Transition Forks
class BerlinToLondonAt5(Berlin):
    @classmethod
    def header_base_fee_required(self, block_number: int, _: int) -> bool:
        """
        Base Fee is required starting from London.
        """
        return block_number >= 5


class MergeToShanghaiAtTime15k(Merge):
    @classmethod
    def header_withdrawals_required(self, _: int, timestamp: int) -> bool:
        """
        Withdrawals are required starting from Shanghai.
        """
        return timestamp >= 15_000


# Fork helper methods
def forks_from_until(
    fork_from: Type[Fork], fork_until: Type[Fork]
) -> List[Type[Fork]]:
    """
    Returns the specified fork and all forks after it until and including the
    second specified fork
    """
    prev_fork = fork_until

    forks: List[Type[Fork]] = []

    while prev_fork != Fork and prev_fork != fork_from:
        forks.insert(0, prev_fork)

        prev_fork = prev_fork.__base__

    if prev_fork == Fork:
        raise Exception("Fork not found")

    forks.insert(0, fork_from)

    return forks


def forks_from(fork: Type[Fork]) -> List[Type[Fork]]:
    """
    Returns the specified fork and all forks after it
    """
    return forks_from_until(fork, LatestFork)


def is_fork(fork: Type[Fork], which: Type[Fork]) -> bool:
    """
    Returns `True` if `fork` is `which` or beyond, `False otherwise.
    """
    prev_fork = fork

    while prev_fork != Fork:
        if prev_fork == which:
            return True

        prev_fork = prev_fork.__base__

    return False
