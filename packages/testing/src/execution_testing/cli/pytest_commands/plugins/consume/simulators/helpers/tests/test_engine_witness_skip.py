"""Tests for engine-witness simulator skip handling."""

from types import SimpleNamespace
from typing import Any, cast

import pytest

from execution_testing.cli.pytest_commands.plugins.consume.simulators.simulator_logic.test_via_engine_witness import (  # noqa: E501
    test_blockchain_via_engine_witness as run_engine_witness,
)


def test_mutated_execution_witness_fixture_is_skipped() -> None:
    """Fixtures with deliberately mutated witnesses are not consumable."""
    fixture = cast(
        Any,
        SimpleNamespace(
            payloads=[
                SimpleNamespace(
                    execution_witness=object(),
                    execution_witness_mutated=True,
                )
            ]
        ),
    )
    unused_dependency = cast(Any, None)

    with pytest.raises(
        pytest.skip.Exception,
        match="fixture contains a deliberately mutated executionWitness",
    ):
        run_engine_witness(
            timing_data=unused_dependency,
            eth_rpc=unused_dependency,
            engine_rpc=unused_dependency,
            engine_ssz_rpc=unused_dependency,
            fixture=fixture,
            genesis_header=unused_dependency,
            use_ssz_transport=False,
        )
