"""Ethereum test execution base types."""

from abc import abstractmethod
from typing import Annotated, ClassVar, Dict, Type

from pydantic import PlainSerializer, PlainValidator

from ethereum_test_base_types import CamelModel
from ethereum_test_rpc import EthRPC


class BaseExecute(CamelModel):
    """Represents a base execution format."""

    # Base Execute class properties
    formats: ClassVar[Dict[str, Type["BaseExecute"]]] = {}

    # Execute format properties
    execute_format_name: ClassVar[str] = "unset"
    description: ClassVar[str] = "Unknown execute format; it has not been set."

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs):
        """
        Register all subclasses of BaseFixture with a fixture format name set
        as possible fixture formats.
        """
        if cls.execute_format_name != "unset":
            # Register the new fixture format
            BaseExecute.formats[cls.execute_format_name] = cls

    @abstractmethod
    def execute(self, eth_rpc: EthRPC):
        """Execute the format."""
        pass


# Type alias for a base execute class
ExecuteFormat = Annotated[
    Type[BaseExecute],
    PlainSerializer(lambda f: f.execute_format_name),
    PlainValidator(lambda f: BaseExecute.formats[f] if f in BaseExecute.formats else f),
]
