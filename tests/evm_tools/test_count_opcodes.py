"""
Test counting opcodes in a transaction execution
using the T8N tool.
"""

import json
from io import StringIO
from pathlib import Path

import pytest

from ethereum_spec_tools.evm_tools import create_parser
from ethereum_spec_tools.evm_tools.t8n import ForkCache
from ethereum_spec_tools.evm_tools.t8n.cli import run_t8n_cli

parser = create_parser()

# Fixture 3 is the only client_clis alloc with code, so the only one
# that runs opcodes.
FIXTURE = Path(__file__).parents[2] / (
    "packages/testing/src/execution_testing/client_clis/tests/fixtures/3"
)


@pytest.mark.evm_tools
def test_count_opcodes() -> None:
    """Test counting opcodes in a transaction execution using the T8N tool."""
    options = parser.parse_args(
        [
            "t8n",
            f"--input.env={FIXTURE / 'env.json'}",
            f"--input.alloc={FIXTURE / 'alloc.json'}",
            f"--input.txs={FIXTURE / 'txs.json'}",
            "--output.result=stdout",
            "--output.body=stdout",
            "--output.alloc=stdout",
            "--opcode.count=stdout",
            "--state.fork=Frontier",
        ]
    )

    in_file = StringIO()
    out_file = StringIO()

    with ForkCache() as fork_cache:
        exit_code = run_t8n_cli(options, out_file, in_file, fork_cache)
    assert 0 == exit_code

    results = json.loads(out_file.getvalue())

    # 0x600140 is PUSH1 then BLOCKHASH.
    assert results["opcodeCount"] == {"PUSH1": 1, "BLOCKHASH": 1}
