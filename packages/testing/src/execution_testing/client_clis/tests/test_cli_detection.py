"""Test which client CLI claims a given version line."""

from typing import Any, List, Type

import pytest

from execution_testing.client_clis import (
    BesuFixtureConsumer,
    BesuTransitionTool,
    EvmOneBlockchainFixtureConsumer,
    EvmOneStateFixtureConsumer,
    EvmOneTransitionTool,
    FixtureConsumerTool,
    GethFixtureConsumer,
    GethTransitionTool,
    NethtestFixtureConsumer,
    NimbusTransitionTool,
    TransitionTool,
)


def claimants(
    registered_tools: List[Type[Any]], version_output: str
) -> List[Type[Any]]:
    """Return the registered tools whose detection accepts the output."""
    # The spec's own t8n has no pattern; it is never detected from a binary.
    # Without a binary to probe, Erigon declines and leaves `evm` to geth.
    return [
        tool
        for tool in registered_tools
        if hasattr(tool, "detect_binary_pattern")
        and tool.detect_binary(version_output, None)
    ]


@pytest.mark.parametrize(
    "version_output,transition_tool,fixture_consumer",
    [
        pytest.param(
            "evm version 1.17.0-unstable-0b26b7c7-20261016",
            GethTransitionTool,
            GethFixtureConsumer,
            id="geth",
        ),
        pytest.param(
            "evm 1.17.0",
            GethTransitionTool,
            GethFixtureConsumer,
            id="geth-new",
        ),
        pytest.param(
            "Besu evm 25.10.0-dev-45455813",
            BesuTransitionTool,
            BesuFixtureConsumer,
            id="besu",
        ),
        pytest.param(
            "evmtool 25.10.0",
            BesuTransitionTool,
            BesuFixtureConsumer,
            id="besu-new",
        ),
        pytest.param("1.2.3", None, NethtestFixtureConsumer, id="nethtest"),
        pytest.param(
            "1.32.0-unstable+" + "a" * 40,
            None,
            NethtestFixtureConsumer,
            id="nethtest-commit",
        ),
        pytest.param(
            "Nethermind nethtest 2.2.0-preview+441af213",
            None,
            NethtestFixtureConsumer,
            id="nethtest-runner",
        ),
        pytest.param("evmone 0.22.0", EvmOneTransitionTool, None, id="evmone"),
        pytest.param(
            "evmone-statetest 0.22.0",
            None,
            EvmOneStateFixtureConsumer,
            id="evmone-statetest",
        ),
        pytest.param(
            "evmone-blockchaintest 0.22.0",
            None,
            EvmOneBlockchainFixtureConsumer,
            id="evmone-blockchaintest",
        ),
        pytest.param(
            "Nimbus-t8n 0.1.2", NimbusTransitionTool, None, id="nimbus"
        ),
        pytest.param("Geth 1.2.3", None, None, id="unknown"),
    ],
)
def test_one_tool_claims_each_version_line(
    version_output: str,
    transition_tool: Type[Any] | None,
    fixture_consumer: Type[Any] | None,
) -> None:
    """Detect each tool by its name, and no other tool by the same line."""
    expected_tools = [transition_tool] if transition_tool else []
    expected_consumers = [fixture_consumer] if fixture_consumer else []
    assert (
        claimants(TransitionTool.registered_tools, version_output)
        == expected_tools
    )
    assert (
        claimants(FixtureConsumerTool.registered_tools, version_output)
        == expected_consumers
    )
