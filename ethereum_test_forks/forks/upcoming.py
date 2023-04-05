"""
List of upcoming, planned or tentative Ethereum forks that are not yet
supported by most clients.
"""

from .forks import Shanghai


class ShardingFork(Shanghai):
    """
    Sharding fork
    """

    @classmethod
    def header_excess_data_gas_required(
        cls, block_number: int, timestamp: int
    ) -> bool:
        """
        Excess data gas is required starting from Sharding.
        """
        return True


# Test-only forks


class TestOnlyUpcomingFork(Shanghai):
    """
    Test-only fork
    """

    pass
