"""Build valid blocktests from fuzzer-generated transactions and pre-state."""

import json
import random
from pathlib import Path
from typing import Any, Dict, Optional

from ethereum_clis import GethTransitionTool, TransitionTool
from ethereum_test_fixtures import BlockchainFixture

from .converter import blockchain_test_from_fuzzer
from .models import FuzzerOutput


def choose_random_num_blocks(num_txs: int, max_blocks: int = 10) -> int:
    """
    Choose random number of blocks for given transaction count.

    Selects a random number between 1 and min(num_txs, max_blocks) to enable
    testing of various block configurations.

    Args:
        num_txs: Number of transactions to distribute
        max_blocks: Maximum number of blocks (default: 10)

    Returns:
        Random integer between 1 and min(num_txs, max_blocks)

    """
    if num_txs == 0:
        return 1  # Allow empty block testing
    return random.randint(1, min(num_txs, max_blocks))


class BlocktestBuilder:
    """Build valid blocktests from fuzzer-generated transactions."""

    def __init__(self, transition_tool: Optional[TransitionTool] = None):
        """Initialize the builder with optional transition tool."""
        self.t8n = transition_tool or GethTransitionTool()

    def build_blocktest(
        self,
        fuzzer_output: Dict[str, Any],
        num_blocks: int = 1,
        block_strategy: str = "distribute",
        block_time: int = 12,
    ) -> Dict[str, Any]:
        """Build a valid blocktest from fuzzer output."""
        # Parse and validate using Pydantic model
        fuzzer_data = FuzzerOutput(**fuzzer_output)

        # Get fork
        fork = fuzzer_data.fork

        # Create BlockchainTest using converter
        test = blockchain_test_from_fuzzer(
            fuzzer_data,
            fork,
            num_blocks=num_blocks,
            block_strategy=block_strategy,
            block_time=block_time,
        )

        # Generate fixture
        fixture = test.generate(
            t8n=self.t8n,
            fork=fork,
            fixture_format=BlockchainFixture,
        )

        return fixture.model_dump(
            exclude_none=True, by_alias=True, mode="json"
        )

    def build_and_save(
        self, fuzzer_output: Dict[str, Any], output_path: Path
    ) -> Path:
        """Build blocktest and save to file."""
        blocktest = self.build_blocktest(fuzzer_output)
        fixtures = {"fuzzer_generated_test": blocktest}

        with open(output_path, "w") as f:
            json.dump(fixtures, f, indent=2)

        return output_path


def build_blocktest_from_fuzzer(
    fuzzer_data: Dict[str, Any], t8n: Optional[TransitionTool] = None
) -> Dict[str, Any]:
    """Build blocktest from fuzzer output."""
    builder = BlocktestBuilder(t8n)
    return builder.build_blocktest(fuzzer_data)
