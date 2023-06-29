"""
Abstract base class for Ethereum forks
"""
from abc import ABC, ABCMeta, abstractmethod
from typing import Optional, Type


class BaseForkMeta(ABCMeta):
    """
    Metaclass for BaseFork
    """

    def name(cls) -> str:
        """
        To be implemented by the fork base class.
        """
        return ""

    def __repr__(cls) -> str:
        """
        Used to properly print the name of the fork, instead of the class.
        """
        return cls.name()


class BaseFork(ABC, metaclass=BaseForkMeta):
    """
    An abstract class representing an Ethereum fork.

    Must contain all the methods used by every fork.
    """

    # Header information abstract methods
    @classmethod
    @abstractmethod
    def header_base_fee_required(cls, block_number: int, timestamp: int) -> bool:
        """
        Returns true if the header must contain base fee
        """
        pass

    @classmethod
    @abstractmethod
    def header_prev_randao_required(cls, block_number: int, timestamp: int) -> bool:
        """
        Returns true if the header must contain Prev Randao value
        """
        pass

    @classmethod
    @abstractmethod
    def header_zero_difficulty_required(cls, block_number: int, timestamp: int) -> bool:
        """
        Returns true if the header must have difficulty zero
        """
        pass

    @classmethod
    @abstractmethod
    def header_withdrawals_required(cls, block_number: int, timestamp: int) -> bool:
        """
        Returns true if the header must contain withdrawals
        """
        pass

    @classmethod
    @abstractmethod
    def header_excess_data_gas_required(cls, block_number: int, timestamp: int) -> bool:
        """
        Returns true if the header must contain excess data gas
        """
        pass

    @classmethod
    @abstractmethod
    def header_data_gas_used_required(cls, block_number: int, timestamp: int) -> bool:
        """
        Returns true if the header must contain data gas used
        """
        pass

    @classmethod
    @abstractmethod
    def get_reward(cls, block_number: int, timestamp: int) -> int:
        """
        Returns the expected reward amount in wei of a given fork
        """
        pass

    # Engine API information abstract methods
    @classmethod
    @abstractmethod
    def engine_new_payload_version(cls, block_number: int, timestamp: int) -> Optional[int]:
        """
        Returns `None` if this fork's payloads cannot be sent over the engine API,
        or the payload version if it can.
        """
        pass

    @classmethod
    @abstractmethod
    def engine_new_payload_blob_hashes(cls, block_number: int, timestamp: int) -> bool:
        """
        Returns true if the engine api version requires new payload calls to include blob hashes.
        """
        pass

    # Meta information about the fork
    @classmethod
    def name(cls) -> str:
        """
        Returns the name of the fork.
        """
        return cls.__name__

    @classmethod
    def is_deployed(cls) -> bool:
        """
        Returns whether the fork has been deployed to mainnet, or not.

        Must be overridden and return False for forks that are still under
        development.
        """
        return True


# Fork Type
Fork = Type[BaseFork]
