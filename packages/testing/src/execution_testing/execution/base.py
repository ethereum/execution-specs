"""Ethereum test execution base types."""

from abc import abstractmethod
from typing import Annotated, Any, ClassVar, Dict, List, Type

import pytest
from pydantic import PlainSerializer, PlainValidator
from pytest import FixtureRequest

from execution_testing.base_types import Address, CamelModel
from execution_testing.forks import Fork
from execution_testing.rpc import EngineRPC, EthRPC
from execution_testing.test_types import Environment


class ExecuteResult(CamelModel):
    """
    Result of the execute operation.
    """

    benchmark_gas_used: int | None = None


class BaseExecute(CamelModel):
    """Represents a base execution format."""

    benchmark_mode: bool = False

    # Base Execute class properties
    formats: ClassVar[Dict[str, Type["BaseExecute"]]] = {}

    # Execute format properties
    format_name: ClassVar[str] = ""
    description: ClassVar[str] = "Unknown execute format; it has not been set."
    requires_engine_rpc: ClassVar[bool] = False

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: Any) -> None:
        """
        Register all subclasses of BaseExecute with a execute format
        name set as possible execute formats.
        """
        if cls.format_name:
            # Register the new execute format
            BaseExecute.formats[cls.format_name] = cls

    @classmethod
    def format_class(cls) -> "Type[BaseExecute]":
        """Get the execute format."""
        return cls

    @classmethod
    def format_id(cls) -> str:
        """Get string used as identifier for this format."""
        return cls.format_name.lower()

    @classmethod
    def marks(cls) -> List[pytest.MarkDecorator | pytest.Mark]:
        """
        Get list of pytest marks that need to be added to a test produced
        with this execute format.
        """
        return [
            getattr(
                pytest.mark,
                cls.format_name.lower(),
            ),
        ]

    def prepare_transactions(
        self,
        *,
        env: Environment,
        gas_price: int,
        max_fee_per_gas: int,
        max_priority_fee_per_gas: int,
        max_fee_per_blob_gas: int,
        fork: Fork,
    ) -> None:
        """Prepare transactions by setting their final gas properties."""
        del env
        del gas_price, max_fee_per_gas, max_priority_fee_per_gas
        del max_fee_per_blob_gas, fork
        raise Exception(
            "Method `prepare_transactions` not implemented for "
            f"{self.format_name}"
        )

    def get_required_sender_balances(
        self,
        *,
        fork: Fork,
    ) -> Dict[Address, int]:
        """Get the required sender balances."""
        del fork
        raise Exception(
            "Method `get_required_sender_balances` not implemented for "
            f"{self.format_name}"
        )

    @abstractmethod
    def execute(
        self,
        fork: Fork,
        eth_rpc: EthRPC,
        engine_rpc: EngineRPC | None,
        request: FixtureRequest,
    ) -> ExecuteResult:
        """Execute the format."""
        pass


class LabeledExecuteFormat:
    """
    Represents an execution format with a custom label.

    This label will be used in the test id and also will be added as a marker
    to the generated test case when executing the test.
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
        self.format = execute_format.format_class()
        self.label = label
        self.description = description
        if label not in LabeledExecuteFormat.registered_labels:
            LabeledExecuteFormat.registered_labels[label] = self

    @property
    def format_name(self) -> str:
        """Get the execute format name."""
        return self.format.format_name

    def format_class(self) -> Type[BaseExecute]:
        """Get the format without label."""
        return self.format

    @property
    def requires_engine_rpc(self) -> bool:
        """Get the requires-engine-RPC flag."""
        return self.format.requires_engine_rpc

    def format_id(self) -> str:
        """Get string used as identifier for this format."""
        return self.label

    def marks(self) -> List[pytest.MarkDecorator | pytest.Mark]:
        """
        Get list of pytest marks that need to be added to a test produced
        with this execute format.
        """
        marks: List[pytest.MarkDecorator | pytest.Mark] = self.format.marks()
        if self.label.lower() != self.format.format_name.lower():
            marks.append(
                getattr(
                    pytest.mark,
                    self.label.lower(),
                )
            )
        return marks

    def __eq__(self, other: Any) -> bool:
        """
        Check if two labeled execute formats are equal.

        If the other object is a ExecuteFormat type, the format of the labeled
        execute format will be compared with the format of the other object.
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
    PlainValidator(
        lambda f: BaseExecute.formats[f] if f in BaseExecute.formats else f
    ),
]
