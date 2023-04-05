"""
Abstract base class for Ethereum forks
"""
from typing import Type


class BaseFork:
    """
    An abstract class representing an Ethereum fork.

    Must contain all the methods used by every fork.
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
    def header_excess_data_gas_required(
        cls, block_number: int, timestamp: int
    ) -> bool:
        """
        Returns true if the header must contain excess data gas
        """
        return False

    @classmethod
    def get_reward(cls, block_number: int, timestamp: int) -> int:
        """
        Returns the expected reward amount in wei of a given fork
        """
        return 2_000_000_000_000_000_000


# Fork Type
Fork = Type[BaseFork]
