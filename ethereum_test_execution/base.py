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
    format_name: ClassVar[str] = ""
    description: ClassVar[str] = "Unknown execute format; it has not been set."

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs):
        """
        Register all subclasses of BaseFixture with a fixture format name set
        as possible fixture formats.
        """
        if cls.format_name:
            # Register the new fixture format
            BaseExecute.formats[cls.format_name] = cls

    @abstractmethod
    def execute(self, eth_rpc: EthRPC):
        """Execute the format."""
        pass


class LabeledExecuteFormat:
    """
    Represents an execution format with a custom label.

    This label will be used in the test id and also will be added as a marker to the
    generated test case when executing the test.
    """

    format: Type[BaseExecute]
    label: str

    def __init__(self, execute_format: "Type[BaseExecute] | LabeledExecuteFormat", label: str):
        """Initialize the execute format with a custom label."""
        self.format = (
            execute_format.format
            if isinstance(execute_format, LabeledExecuteFormat)
            else execute_format
        )
        self.label = label

    @property
    def format_name(self) -> str:
        """Get the execute format name."""
        return self.format.format_name


# Type alias for a base execute class
ExecuteFormat = Annotated[
    Type[BaseExecute],
    PlainSerializer(lambda f: f.format_name),
    PlainValidator(lambda f: BaseExecute.formats[f] if f in BaseExecute.formats else f),
]
