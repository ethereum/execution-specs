"""
Abstract base class for Ethereum forks
"""
from abc import ABC, abstractmethod
from typing import Type


class BaseFork(ABC):
    """
    An abstract class representing an Ethereum fork.

    Must contain all the methods used by every fork.
    """

    @classmethod
    @abstractmethod
    def header_base_fee_required(
        cls, block_number: int, timestamp: int
    ) -> bool:
        """
        Returns true if the header must contain base fee
        """
        pass

    @classmethod
    @abstractmethod
    def header_prev_randao_required(
        cls, block_number: int, timestamp: int
    ) -> bool:
        """
        Returns true if the header must contain Prev Randao value
        """
        pass

    @classmethod
    @abstractmethod
    def header_zero_difficulty_required(
        cls, block_number: int, timestamp: int
    ) -> bool:
        """
        Returns true if the header must have difficulty zero
        """
        pass

    @classmethod
    @abstractmethod
    def header_withdrawals_required(
        cls, block_number: int, timestamp: int
    ) -> bool:
        """
        Returns true if the header must contain withdrawals
        """
        pass

    @classmethod
    @abstractmethod
    def header_excess_data_gas_required(
        cls, block_number: int, timestamp: int
    ) -> bool:
        """
        Returns true if the header must contain excess data gas
        """
        pass

    @classmethod
    @abstractmethod
    def get_reward(cls, block_number: int, timestamp: int) -> int:
        """
        Returns the expected reward amount in wei of a given fork
        """
        pass


# Fork Type
Fork = Type[BaseFork]
