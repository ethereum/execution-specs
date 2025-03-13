"""Library of Python wrappers for the different implementations of transition tools."""

from .clis.besu import BesuTransitionTool
from .clis.ethereumjs import EthereumJSTransitionTool
from .clis.evmone import EvmoneExceptionMapper, EvmOneTransitionTool
from .clis.execution_specs import ExecutionSpecsTransitionTool
from .clis.geth import GethFixtureConsumer, GethTransitionTool
from .clis.nethermind import Nethtest, NethtestFixtureConsumer
from .clis.nimbus import NimbusTransitionTool
from .ethereum_cli import CLINotFoundInPathError, UnknownCLIError
from .fixture_consumer_tool import FixtureConsumerTool
from .transition_tool import TransitionTool
from .types import Result, TransitionToolOutput

TransitionTool.set_default_tool(ExecutionSpecsTransitionTool)
FixtureConsumerTool.set_default_tool(GethFixtureConsumer)

__all__ = (
    "BesuTransitionTool",
    "CLINotFoundInPathError",
    "EthereumJSTransitionTool",
    "EvmoneExceptionMapper",
    "EvmOneTransitionTool",
    "ExecutionSpecsTransitionTool",
    "FixtureConsumerTool",
    "GethFixtureConsumer",
    "GethTransitionTool",
    "Nethtest",
    "NethtestFixtureConsumer",
    "NimbusTransitionTool",
    "Result",
    "TransitionTool",
    "TransitionToolOutput",
    "UnknownCLIError",
)
