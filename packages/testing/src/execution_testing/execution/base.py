"""Ethereum test execution base types."""

from abc import abstractmethod
from typing import Annotated, Any, ClassVar, Dict, List, Type

from pydantic import PlainSerializer, PlainValidator
from pytest import FixtureRequest

from execution_testing.base_types import Address, CamelModel
from execution_testing.forks import Fork
from execution_testing.rpc import EngineRPC, EthRPC
from execution_testing.test_types import Environment, Transaction


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

    @staticmethod
    def calculate_max_transaction_gas_limit(
        txs: List[Transaction], env: Environment, fork: Fork
    ) -> int:
        """
        Calculate the maximum gas limit that can be set in a transaction
        given a list of transactions with and without gas-limits set
        and a maximum available environment gas.
        """
        available_gas = int(env.gas_limit)
        unset_gas_limit_tx_count = 0
        for tx in txs:
            if tx.gas_limit is None:
                unset_gas_limit_tx_count += 1
            else:
                available_gas -= int(tx.gas_limit)

        if unset_gas_limit_tx_count == 0 or available_gas <= 0:
            return 0

        max_gas_limit = available_gas // unset_gas_limit_tx_count
        tx_gas_limit_cap = fork.transaction_gas_limit_cap()
        if fork.state_gas_reservoir_enabled():
            tx_gas_limit_cap = None
        if tx_gas_limit_cap:
            max_gas_limit = min(max_gas_limit, tx_gas_limit_cap)
        return max_gas_limit

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

    @property
    def requires_engine_rpc(self) -> bool:
        """Get the requires engine RPC flag."""
        return self.format.requires_engine_rpc

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
