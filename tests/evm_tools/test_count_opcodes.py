import json
from io import StringIO
from pathlib import Path
from typing import Callable

import pytest

from ethereum_spec_tools.evm_tools import create_parser
from ethereum_spec_tools.evm_tools.t8n import T8N

parser = create_parser()


@pytest.mark.evm_tools
def test_count_opcodes(root_relative: Callable[[str | Path], Path]) -> None:
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

    t8n_tool = T8N(options, out_file=out_file, in_file=in_file)
    exit_code = t8n_tool.run()
    assert 0 == exit_code

    results = json.loads(out_file.getvalue())

    assert results["opcodeCount"] == {
        "PUSH1": 5,
        "MSTORE8": 1,
        "CREATE": 1,
        "ADD": 1,
        "SELFDESTRUCT": 1,
    }
