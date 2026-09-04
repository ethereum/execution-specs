"""Tests for the transaction body emitted by the t8n tool."""

import json
from io import StringIO
from pathlib import Path

import pytest
from ethereum_rlp import rlp

from execution_testing.evm_tools import create_parser
from execution_testing.evm_tools.t8n import ForkCache
from execution_testing.evm_tools.t8n.cli import run_t8n_cli
from execution_testing.test_types import Transaction

FIXTURES = Path(__file__).parent / "fixtures" / "t8n_body"


@pytest.mark.evm_tools
def test_body_encodes_only_accepted_transactions() -> None:
    """Encode legacy txs inline, preserve typed envelopes, and omit rejects."""
    options = create_parser().parse_args(
        [
            "t8n",
            f"--input.alloc={FIXTURES / 'alloc.json'}",
            f"--input.env={FIXTURES / 'env.json'}",
            f"--input.txs={FIXTURES / 'txs.json'}",
            "--output.result=stdout",
            "--output.body=stdout",
            "--output.alloc=stdout",
            "--state.fork=Prague",
            "--state.chainid=1",
            "--state.reward=-1",
        ]
    )

    out_file = StringIO()
    with ForkCache() as fork_cache:
        exit_code = run_t8n_cli(options, out_file, StringIO(), fork_cache)

    assert exit_code == 0
    output = json.loads(out_file.getvalue())
    assert [item["index"] for item in output["result"]["rejected"]] == ["0x1"]

    raw_txs = json.loads((FIXTURES / "txs.json").read_text())
    txs = [Transaction.model_validate(raw) for raw in raw_txs]
    expected = rlp.encode([rlp.decode(txs[0].rlp()), txs[2].rlp()])
    body = bytes.fromhex(output["body"][2:])

    assert body == expected
    decoded = rlp.decode(body)
    assert isinstance(decoded[0], list)
    assert isinstance(decoded[1], bytes)
    assert decoded[1].startswith(b"\x02")
