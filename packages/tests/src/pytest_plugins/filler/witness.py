"""
Pytest plugin for witness functionality.

Provides --witness command-line option that checks for the witness-filler tool
in PATH and generates execution witness data for blockchain test fixtures when
enabled.
"""

import shutil
import subprocess
from typing import Callable, List

import pytest

from ethereum_test_base_types import EthereumTestRootModel
from ethereum_test_fixtures.blockchain import (
    BlockchainFixture,
    FixtureBlock,
    WitnessChunk,
)
from ethereum_test_forks import Paris


class WitnessFillerResult(EthereumTestRootModel[List[WitnessChunk]]):
    """
    Model that defines the expected result from the `witness-filler` command.
    """

    root: List[WitnessChunk]


class Merge(Paris):
    """
    Paris fork that serializes as 'Merge' for witness-filler compatibility.

    IMPORTANT: This class MUST be named 'Merge' (not 'MergeForWitness' or
    similar) because the class name is used directly in Pydantic serialization,
    and witness-filler expects exactly 'Merge' for this fork.
    """

    pass


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add witness command-line options to pytest."""
    witness_group = parser.getgroup(
        "witness", "Arguments for witness functionality"
    )
    witness_group.addoption(
        "--witness",
        "--witness-the-fitness",
        action="store_true",
        dest="witness",
        default=False,
        help=(
            "Generate execution witness data for blockchain test fixtures using the "
            "witness-filler tool (must be installed separately)."
        ),
    )


def pytest_configure(config: pytest.Config) -> None:
    """
    Pytest hook called after command line options have been parsed.

    If --witness is enabled, checks that the witness-filler tool is available
    in PATH.
    """
    if config.getoption("witness"):
        # Check if witness-filler binary is available in PATH
        if not shutil.which("witness-filler"):
            pytest.exit(
                "witness-filler tool not found in PATH. Please build and install witness-filler "
                "from https://github.com/kevaundray/reth.git before using --witness flag.\n"
                "Example: cargo install --git https://github.com/kevaundray/reth.git "
                "witness-filler",
                1,
            )


@pytest.fixture
def witness_generator(
    request: pytest.FixtureRequest,
) -> Callable[[BlockchainFixture], None] | None:
    """
    Provide a witness generator function if --witness is enabled.

    Returns: None if witness functionality is disabled. Callable that generates
    witness data for a BlockchainFixture if enabled.
    """
    if not request.config.getoption("witness"):
        return None

    def generate_witness(fixture: BlockchainFixture) -> None:
        """
        Generate witness data for a blockchain fixture using the witness-filler
        tool.
        """
        if not isinstance(fixture, BlockchainFixture):
            return None

        # Hotfix: witness-filler expects "Merge" but execution-spec-tests uses
        # "Paris"
        original_fork = None
        if fixture.fork is Paris:
            original_fork = fixture.fork
            fixture.fork = Merge

        try:
            result = subprocess.run(
                ["witness-filler"],
                input=fixture.model_dump_json(by_alias=True),
                text=True,
                capture_output=True,
            )
        finally:
            if original_fork is not None:
                fixture.fork = original_fork

        if result.returncode != 0:
            raise RuntimeError(
                f"witness-filler tool failed with exit code {result.returncode}. "
                f"stderr: {result.stderr}"
            )

        try:
            result_model = WitnessFillerResult.model_validate_json(
                result.stdout
            )
            witnesses = result_model.root

            for i, witness in enumerate(witnesses):
                if i < len(fixture.blocks):
                    block = fixture.blocks[i]
                    if isinstance(block, FixtureBlock):
                        block.execution_witness = witness
        except Exception as e:
            raise RuntimeError(
                f"Failed to parse witness data from witness-filler tool. "
                f"Output was: {result.stdout[:500]}{'...' if len(result.stdout) > 500 else ''}"
            ) from e

    return generate_witness
