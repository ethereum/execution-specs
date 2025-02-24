"""Ethereum test execution base types."""

from abc import abstractmethod
from typing import Annotated, Any, ClassVar, Dict, Type

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
        Register all subclasses of BaseExecute with a execute format name set
        as possible execute formats.
        """
        if cls.format_name:
            # Register the new execute format
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
    description: str

    registered_labels: ClassVar[Dict[str, "LabeledExecuteFormat"]] = {}

    def __init__(
        self,
        execute_format: "Type[BaseExecute] | LabeledExecuteFormat",
        label: str,
        description: str,
    ):
        """Initialize the execute format with a custom label."""
        self.format = (
            execute_format.format
            if isinstance(execute_format, LabeledExecuteFormat)
            else execute_format
        )
        self.label = label
        self.description = description
        if label not in LabeledExecuteFormat.registered_labels:
            LabeledExecuteFormat.registered_labels[label] = self

    @property
    def format_name(self) -> str:
        """Get the execute format name."""
        return self.format.format_name

    def __eq__(self, other: Any) -> bool:
        """
        Check if two labeled execute formats are equal.

        If the other object is a ExecuteFormat type, the format of the labeled execute
        format will be compared with the format of the other object.
        """
        if isinstance(other, LabeledExecuteFormat):
            return self.format == other.format
        if isinstance(other, type) and issubclass(other, BaseExecute):
            return self.format == other
        return False


# Type alias for a base execute class
ExecuteFormat = Annotated[
    Type[BaseExecute],
    PlainSerializer(lambda f: f.format_name),
    PlainValidator(lambda f: BaseExecute.formats[f] if f in BaseExecute.formats else f),
]
