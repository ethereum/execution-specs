"""
Abstract base class for Ethereum forks
"""
from abc import ABC, ABCMeta, abstractmethod
from typing import Mapping, Optional, Type

from .base_decorators import prefer_transition_to_method


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

    @classmethod
    @abstractmethod
    def fork(cls, block_number: int = 0, timestamp: int = 0) -> str:
        """
        Returns fork name as it's meant to be passed to the transition tool for execution.
        """
        pass

    # Header information abstract methods
    @classmethod
    @abstractmethod
    def header_base_fee_required(cls, block_number: int = 0, timestamp: int = 0) -> bool:
        """
        Returns true if the header must contain base fee
        """
        pass

    @classmethod
    @abstractmethod
    def header_prev_randao_required(cls, block_number: int = 0, timestamp: int = 0) -> bool:
        """
        Returns true if the header must contain Prev Randao value
        """
        pass

    @classmethod
    @abstractmethod
    def header_zero_difficulty_required(cls, block_number: int = 0, timestamp: int = 0) -> bool:
        """
        Returns true if the header must have difficulty zero
        """
        pass

    @classmethod
    @abstractmethod
    def header_withdrawals_required(cls, block_number: int = 0, timestamp: int = 0) -> bool:
        """
        Returns true if the header must contain withdrawals
        """
        pass

    @classmethod
    @abstractmethod
    def header_excess_blob_gas_required(cls, block_number: int = 0, timestamp: int = 0) -> bool:
        """
        Returns true if the header must contain excess blob gas
        """
        pass

    @classmethod
    @abstractmethod
    def header_blob_gas_used_required(cls, block_number: int = 0, timestamp: int = 0) -> bool:
        """
        Returns true if the header must contain blob gas used
        """
        pass

    @classmethod
    @abstractmethod
    def header_beacon_root_required(cls, block_number: int, timestamp: int) -> bool:
        """
        Returns true if the header must contain parent beacon block root
        """
        pass

    @classmethod
    @abstractmethod
    def get_reward(cls, block_number: int = 0, timestamp: int = 0) -> int:
        """
        Returns the expected reward amount in wei of a given fork
        """
        pass

    @classmethod
    @prefer_transition_to_method
    @abstractmethod
    def pre_allocation(cls, block_number: int = 0, timestamp: int = 0) -> Mapping:
        """
        Returns required pre-allocation of accounts.

        This method must always call the `fork_to` method when transitioning, because the
        allocation can only be set at genesis, and thus cannot be changed at transition time.
        """
        pass

    # Engine API information abstract methods
    @classmethod
    @abstractmethod
    def engine_new_payload_version(
        cls, block_number: int = 0, timestamp: int = 0
    ) -> Optional[int]:
        """
        Returns `None` if this fork's payloads cannot be sent over the engine API,
        or the payload version if it can.
        """
        pass

    @classmethod
    @abstractmethod
    def engine_new_payload_blob_hashes(cls, block_number: int = 0, timestamp: int = 0) -> bool:
        """
        Returns true if the engine api version requires new payload calls to include blob hashes.
        """
        pass

    @classmethod
    @abstractmethod
    def engine_new_payload_beacon_root(cls, block_number: int = 0, timestamp: int = 0) -> bool:
        """
        Returns true if the engine api version requires new payload calls to include a parent
        beacon block root.
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
