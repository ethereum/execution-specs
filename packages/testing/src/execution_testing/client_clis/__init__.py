"""
Library of Python wrappers for the different implementations of transition
tools.
"""

from .cli_types import (
    BlockExceptionWithMessage,
    LazyAlloc,
    Result,
    TraceFieldDiff,
    Traces,
    TransactionExceptionWithMessage,
    TransitionToolOutput,
)
from .clis.besu import BesuFixtureConsumer, BesuTransitionTool
from .clis.ethereumjs import EthereumJSTransitionTool
from .clis.evmone import (
    EvmOneBlockchainFixtureConsumer,
    EvmoneExceptionMapper,
    EvmOneStateFixtureConsumer,
    EvmOneTransitionTool,
)
from .clis.execution_specs import ExecutionSpecsTransitionTool
from .clis.geth import GethFixtureConsumer, GethTransitionTool
from .clis.nethermind import Nethtest, NethtestFixtureConsumer
from .clis.nimbus import NimbusTransitionTool
from .ethereum_cli import CLINotFoundInPathError, UnknownCLIError
from .fixture_consumer_tool import FixtureConsumerTool
from .trace_comparators import (
    FieldExclusionTraceComparator,
    GasExhaustionTraceComparator,
    TraceComparator,
    TraceComparatorType,
    TraceComparisonResult,
    TraceDifference,
    TransactionCountMismatch,
    create_comparator,
)
from .transition_tool import TransitionTool

TransitionTool.set_default_tool(ExecutionSpecsTransitionTool)
FixtureConsumerTool.set_default_tool(GethFixtureConsumer)

__all__ = (
    "BesuFixtureConsumer",
    "BesuTransitionTool",
    "BlockExceptionWithMessage",
    "CLINotFoundInPathError",
    "EthereumJSTransitionTool",
    "EvmoneExceptionMapper",
    "EvmOneTransitionTool",
    "EvmOneStateFixtureConsumer",
    "EvmOneBlockchainFixtureConsumer",
    "ExecutionSpecsTransitionTool",
    "FieldExclusionTraceComparator",
    "FixtureConsumerTool",
    "GasExhaustionTraceComparator",
    "GethFixtureConsumer",
    "GethTransitionTool",
    "LazyAlloc",
    "Nethtest",
    "NethtestFixtureConsumer",
    "NimbusTransitionTool",
    "Result",
    "TraceComparator",
    "TraceComparatorType",
    "TraceComparisonResult",
    "TraceDifference",
    "TraceFieldDiff",
    "Traces",
    "TransactionCountMismatch",
    "TransactionExceptionWithMessage",
    "TransitionTool",
    "TransitionToolOutput",
    "UnknownCLIError",
    "create_comparator",
)
