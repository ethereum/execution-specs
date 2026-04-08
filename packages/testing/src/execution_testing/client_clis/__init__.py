"""
Library of Python wrappers for the different implementations of transition
tools.
"""

from .cli_types import (
    BlockExceptionWithMessage,
    LazyAlloc,
    Result,
    Traces,
    TransactionExceptionWithMessage,
    TransitionToolOutput,
)
from .clis.besu import BesuFixtureConsumer, BesuTransitionTool
# Erigon must be imported before geth: both use the `evm` binary,
# and erigon's more-specific detect pattern (version >= 2.x) must
# be checked before geth's broader pattern.
from .clis.erigon import ErigonFixtureConsumer
from .clis.ethereumjs import EthereumJSTransitionTool
from .clis.ethrex import EthrexFixtureConsumer
from .clis.evmone import (
    EvmOneBlockchainFixtureConsumer,
    EvmoneExceptionMapper,
    EvmOneStateFixtureConsumer,
    EvmOneTransitionTool,
)
from .clis.execution_specs import ExecutionSpecsTransitionTool
from .clis.geth import GethFixtureConsumer, GethTransitionTool
from .clis.nethermind import Nethtest, NethtestFixtureConsumer
from .clis.nimbus import NimbusFixtureConsumer, NimbusTransitionTool
from .clis.reth import RethFixtureConsumer
from .ethereum_cli import CLINotFoundInPathError, UnknownCLIError
from .fixture_consumer_tool import FixtureConsumerTool
from .transition_tool import TransitionTool

TransitionTool.set_default_tool(ExecutionSpecsTransitionTool)
FixtureConsumerTool.set_default_tool(GethFixtureConsumer)

__all__ = (
    "BesuFixtureConsumer",
    "BesuTransitionTool",
    "BlockExceptionWithMessage",
    "CLINotFoundInPathError",
    "ErigonFixtureConsumer",
    "EthereumJSTransitionTool",
    "EthrexFixtureConsumer",
    "EvmoneExceptionMapper",
    "EvmOneTransitionTool",
    "EvmOneStateFixtureConsumer",
    "EvmOneBlockchainFixtureConsumer",
    "ExecutionSpecsTransitionTool",
    "FixtureConsumerTool",
    "GethFixtureConsumer",
    "GethTransitionTool",
    "LazyAlloc",
    "Nethtest",
    "NethtestFixtureConsumer",
    "NimbusFixtureConsumer",
    "NimbusTransitionTool",
    "RethFixtureConsumer",
    "Result",
    "Traces",
    "TransactionExceptionWithMessage",
    "TransitionTool",
    "TransitionToolOutput",
    "UnknownCLIError",
)
