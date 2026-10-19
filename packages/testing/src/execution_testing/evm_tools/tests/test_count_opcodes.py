"""
Test counting opcodes in a transaction execution
using the T8N tool.
"""

import json
from io import StringIO
from pathlib import Path

import pytest

from execution_testing.evm_tools import create_parser
from execution_testing.evm_tools.t8n import ForkCache
from execution_testing.evm_tools.t8n.cli import run_t8n_cli

parser = create_parser()

# Vendored from https://github.com/gurukamath/evm-tools-testdata at
# commit 792422d, `t8n/fixtures/testdata/2`. The retired
# `evm_tools_testdata` download step used to supply these inputs.
FIXTURE_DIR = Path(__file__).parent / "fixtures" / "count_opcodes"


@pytest.mark.evm_tools
def test_count_opcodes(tmp_path: Path) -> None:
    """Test counting opcodes in a transaction execution using the T8N tool."""
    options = parser.parse_args(
        [
            "t8n",
            f"--input.env={FIXTURE_DIR / 'env.json'}",
            f"--input.alloc={FIXTURE_DIR / 'alloc.json'}",
            f"--input.txs={FIXTURE_DIR / 'txs.json'}",
            f"--output.basedir={tmp_path}",
            "--output.result=stdout",
            "--output.body=stdout",
            "--output.alloc=stdout",
            "--opcode.count=stdout",
            "--state.fork=Frontier",
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
