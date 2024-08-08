"""
Abstract base class for Ethereum forks
"""

from abc import ABC, ABCMeta, abstractmethod
from typing import Any, ClassVar, List, Mapping, Optional, Protocol, Tuple, Type

from semver import Version

from ethereum_test_vm import EVMCodeType, Opcodes

from .base_decorators import prefer_transition_to_method


class ForkAttribute(Protocol):
    """
    A protocol to get the attribute of a fork at a given block number and timestamp.
    """

    def __call__(self, block_number: int = 0, timestamp: int = 0) -> Any:
        """
        Returns the value of the attribute at the given block number and timestamp.
        """
        pass


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

    def __gt__(cls, other: "BaseForkMeta") -> bool:
        """
        Compare if a fork is newer than some other fork.
        """
        return cls != other and other.__subclasscheck__(cls)

    def __ge__(cls, other: "BaseForkMeta") -> bool:
        """
        Compare if a fork is newer than or equal to some other fork.
        """
        return other.__subclasscheck__(cls)

    def __lt__(cls, other: "BaseForkMeta") -> bool:
        """
        Compare if a fork is older than some other fork.
        """
        return cls != other and cls.__subclasscheck__(other)

    def __le__(cls, other: "BaseForkMeta") -> bool:
        """
        Compare if a fork is older than or equal to some other fork.
        """
        return cls.__subclasscheck__(other)


class BaseFork(ABC, metaclass=BaseForkMeta):
    """
    An abstract class representing an Ethereum fork.

    Must contain all the methods used by every fork.
    """

    _transition_tool_name: ClassVar[Optional[str]] = None
    _blockchain_test_network_name: ClassVar[Optional[str]] = None
    _solc_name: ClassVar[Optional[str]] = None
    _ignore: ClassVar[bool] = False

    def __init_subclass__(
        cls,
        *,
        transition_tool_name: Optional[str] = None,
        blockchain_test_network_name: Optional[str] = None,
        solc_name: Optional[str] = None,
        ignore: bool = False,
    ) -> None:
        """
        Initializes the new fork with values that don't carry over to subclass forks.
        """
        cls._transition_tool_name = transition_tool_name
        cls._blockchain_test_network_name = blockchain_test_network_name
        cls._solc_name = solc_name
        cls._ignore = ignore

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
    def header_requests_required(cls, block_number: int, timestamp: int) -> bool:
        """
        Returns true if the header must contain beacon chain requests
        """
        pass

    @classmethod
    @abstractmethod
    def blob_gas_per_blob(cls, block_number: int, timestamp: int) -> int:
        """
        Returns the amount of blob gas used per blob for a given fork.
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
    @abstractmethod
    def tx_types(cls, block_number: int = 0, timestamp: int = 0) -> List[int]:
        """
        Returns a list of the transaction types supported by the fork
        """
        pass

    @classmethod
    @abstractmethod
    def contract_creating_tx_types(cls, block_number: int = 0, timestamp: int = 0) -> List[int]:
        """
        Returns a list of the transaction types supported by the fork that can create contracts
        """
        pass

    @classmethod
    @abstractmethod
    def precompiles(cls, block_number: int = 0, timestamp: int = 0) -> List[int]:
        """
        Returns a list pre-compiles supported by the fork
        """
        pass

    @classmethod
    @prefer_transition_to_method
    @abstractmethod
    def pre_allocation(cls) -> Mapping:
        """
        Returns required pre-allocation of accounts for any kind of test.

        This method must always call the `fork_to` method when transitioning, because the
        allocation can only be set at genesis, and thus cannot be changed at transition time.
        """
        pass

    @classmethod
    @prefer_transition_to_method
    @abstractmethod
    def pre_allocation_blockchain(cls) -> Mapping:
        """
        Returns required pre-allocation of accounts for any blockchain tests.

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

    @classmethod
    @abstractmethod
    def engine_forkchoice_updated_version(
        cls, block_number: int = 0, timestamp: int = 0
    ) -> Optional[int]:
        """
        Returns `None` if the forks canonical chain cannot be set using the forkchoice method.
        """
        pass

    @classmethod
    @abstractmethod
    def evm_code_types(cls, block_number: int = 0, timestamp: int = 0) -> List[EVMCodeType]:
        """
        Returns the list of EVM code types supported by the fork.
        """
        pass

    @classmethod
    @abstractmethod
    def call_opcodes(
        cls, block_number: int = 0, timestamp: int = 0
    ) -> List[Tuple[Opcodes, EVMCodeType]]:
        """
        Returns the list of tuples with the call opcodes and its corresponding EVM code type.
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
    def fork_at(cls, block_number: int = 0, timestamp: int = 0) -> Type["BaseFork"]:
        """
        Returns the fork at the given block number and timestamp.
        Useful only for transition forks, and it's a no-op for normal forks.
        """
        return cls

    @classmethod
    @abstractmethod
    def transition_tool_name(cls, block_number: int = 0, timestamp: int = 0) -> str:
        """
        Returns fork name as it's meant to be passed to the transition tool for execution.
        """
        pass

    @classmethod
    @abstractmethod
    def solc_name(cls) -> str:
        """
        Returns fork name as it's meant to be passed to the solc compiler.
        """
        pass

    @classmethod
    @abstractmethod
    def solc_min_version(cls) -> Version:
        """
        Returns the minimum version of solc that supports this fork.
        """
        pass

    @classmethod
    def blockchain_test_network_name(cls) -> str:
        """
        Returns the network configuration name to be used in BlockchainTests for this fork.
        """
        if cls._blockchain_test_network_name is not None:
            return cls._blockchain_test_network_name
        return cls.name()

    @classmethod
    def is_deployed(cls) -> bool:
        """
        Returns whether the fork has been deployed to mainnet, or not.

        Must be overridden and return False for forks that are still under
        development.
        """
        return True

    @classmethod
    def ignore(cls) -> bool:
        """
        Returns whether the fork should be ignored during test generation.
        """
        return cls._ignore


# Fork Type
Fork = Type[BaseFork]
