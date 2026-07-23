"""
Test counting opcodes in a transaction execution
using the T8N tool.
"""

import json
from io import StringIO
from pathlib import Path
from typing import Callable

import pytest

from ethereum_spec_tools.evm_tools import create_parser
from ethereum_spec_tools.evm_tools.t8n import ForkCache
from ethereum_spec_tools.evm_tools.t8n.cli import run_t8n_cli

parser = create_parser()


@pytest.mark.evm_tools
def test_count_opcodes(root_relative: Callable[[str | Path], Path]) -> None:
    """Test counting opcodes in a transaction execution using the T8N tool."""
    base_path = root_relative(
        "fixtures/evm_tools_testdata/t8n/fixtures/testdata/2"
    )

    options = parser.parse_args(
        [
            "t8n",
            f"--input.env={base_path / 'env.json'}",
            f"--input.alloc={base_path / 'alloc.json'}",
            f"--input.txs={base_path / 'txs.json'}",
            "--output.result=stdout",
            "--output.body=stdout",
            "--output.alloc=stdout",
            "--opcode.count=stdout",
            "--state-test",
        ]
    )

    in_file = StringIO()
    out_file = StringIO()

    with ForkCache() as fork_cache:
        exit_code = run_t8n_cli(options, out_file, in_file, fork_cache)
    assert 0 == exit_code

    results = json.loads(out_file.getvalue())

    assert results["opcodeCount"] == {
        "PUSH1": 5,
        "MSTORE8": 1,
        "CREATE": 1,
        "ADD": 1,
        "SELFDESTRUCT": 1,
    }
