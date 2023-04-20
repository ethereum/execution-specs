"""
List of all transition fork definitions.
"""
from ..transition_base_fork import transition_fork
from .forks import Berlin, London, Merge, Shanghai
from .upcoming import ShardingFork, TestOnlyUpcomingFork


# Transition Forks
@transition_fork(to_fork=London)
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


@transition_fork(to_fork=Shanghai)
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


@transition_fork(to_fork=ShardingFork)
class ShanghaiToShardingAtTime15k(Shanghai):
    """
    Shanghai to Sharding transition at Timestamp 15k
    """

    @classmethod
    def header_excess_data_gas_required(cls, _: int, timestamp: int) -> bool:
        """
        Excess data gas is required if transitioning to Sharding.
        """
        return timestamp >= 15_000


# Test-only transition forks


@transition_fork(to_fork=TestOnlyUpcomingFork)
class ShanghaiToTestOnlyUpcomingFork(Shanghai):
    """
    Test-only transition fork
    """

    pass
