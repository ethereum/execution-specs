"""Test complete inclusion-list input through the transition-tool CLI."""

import argparse
import json
from io import StringIO
from pathlib import Path

import pytest

from execution_testing.base_types import Bytes
from execution_testing.client_clis import TransitionTool
from execution_testing.evm_tools.t8n import ForkCache
from execution_testing.evm_tools.t8n.cli import (
    build_t8n_from_cli_options,
    t8n_arguments,
)
from execution_testing.forks import Bogota
from execution_testing.test_types import (
    Alloc,
    Environment,
    InclusionListClaim,
    Transaction,
)

pytestmark = pytest.mark.evm_tools


@pytest.mark.parametrize("use_stdin", [True, False])
def test_cli_preserves_inclusion_context(
    tmp_path: Path, use_stdin: bool
) -> None:
    """Preserve raw envelopes, duplicate claims and bitvectors."""
    transaction = Transaction(gas_limit=21_000).with_signature_and_sender()
    claim = InclusionListClaim(
        transaction_hash=transaction.hash, evaluation_index=2**64 - 1
    )
    data = TransitionTool.TransitionToolData(
        alloc=Alloc(),
        txs=[],
        env=Environment(),
        fork=Bogota,
        chain_id=1,
        reward=0,
        blob_schedule=None,
        inclusion_list_txs=[transaction],
        inclusion_list_membership=[Bytes("0x0002")],
        inclusion_list_claims=[claim, claim],
    ).to_input()
    parser = argparse.ArgumentParser()
    t8n_arguments(parser.add_subparsers())
    arguments = ["t8n", "--state.fork=Bogota"]
    if use_stdin:
        arguments.extend(
            f"--input.{field}=stdin" for field in ("alloc", "env", "txs")
        )
        in_file = StringIO(data.model_dump_json(by_alias=True))
    else:
        paths = data.to_files(tmp_path, by_alias=True, exclude_none=True)
        arguments.extend(
            f"--input.{field}={path}" for field, path in paths.items()
        )
        in_file = StringIO()

    with ForkCache() as cache:
        tool = build_t8n_from_cli_options(
            parser.parse_args(arguments), in_file, cache
        )
        inputs = tool.inclusion_list_inputs
        assert inputs.transactions == (bytes(transaction.rlp()),)
        assert inputs.membership == (b"\x00\x02",)
        assert len(inputs.claims) == 2
        assert all(
            int(value.evaluation_index) == 2**64 - 1
            and bytes(value.transaction_hash) == bytes(transaction.hash)
            for value in inputs.claims
        )


def test_cli_rejects_malformed_membership() -> None:
    """Reject metadata before executing a payload or any replay."""
    transaction = Transaction(gas_limit=21_000).with_signature_and_sender()
    parser = argparse.ArgumentParser()
    t8n_arguments(parser.add_subparsers())
    options = parser.parse_args(
        [
            "t8n",
            "--state.fork=Bogota",
            "--input.alloc=stdin",
            "--input.env=stdin",
            "--input.txs=stdin",
        ]
    )
    inputs = {
        "alloc": {},
        "env": {},
        "txs": [],
        "inclusionListTransactions": [
            transaction.model_dump(
                mode="json", by_alias=True, exclude_none=True
            )
        ],
        "inclusionListMembership": ["0x01"],
    }
    with ForkCache() as cache, pytest.raises(ValueError, match="membership"):
        build_t8n_from_cli_options(
            options, StringIO(json.dumps(inputs)), cache
        )
