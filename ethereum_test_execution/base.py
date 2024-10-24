"""
Ethereum test execution base types.
"""
from abc import abstractmethod
from typing import ClassVar, Type

from ethereum_test_base_types import CamelModel
from ethereum_test_rpc import EthRPC


class BaseExecute(CamelModel):
    """
    Represents a base execution format.
    """

    # Execute format properties
    execute_format_name: ClassVar[str] = "unset"
    description: ClassVar[str] = "Unknown execute format; it has not been set."

    @abstractmethod
    def execute(self, eth_rpc: EthRPC):
        """
        Execute the format.
        """
        pass


# Type alias for a base execute class
ExecuteFormat = Type[BaseExecute]
