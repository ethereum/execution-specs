"""Test complete inclusion-list input through the transition-tool CLI."""

import argparse
import json
from io import StringIO
from pathlib import Path

import pytest

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
    OmissionClaim,
    Transaction,
)

pytestmark = pytest.mark.evm_tools


@pytest.mark.parametrize("use_stdin", [True, False])
def test_cli_preserves_inclusion_context(
    tmp_path: Path, use_stdin: bool
) -> None:
    """Preserve raw envelopes, duplicate claims and separate lists."""
    transaction = Transaction(gas_limit=21_000).with_signature_and_sender()
    claim = OmissionClaim(
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
        inclusion_lists=[[]] * 9 + [[transaction, transaction]] + [[]] * 6,
        omission_claims=[claim, claim],
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
        assert (
            inputs.inclusion_lists
            == ((),) * 9 + ((bytes(transaction.rlp()),) * 2,) + ((),) * 6
        )
        assert len(inputs.claims) == 2
        assert all(
            int(value.evaluation_index) == 2**64 - 1
            and bytes(value.transaction_hash) == bytes(transaction.hash)
            for value in inputs.claims
        )


def test_cli_rejects_wrong_list_count() -> None:
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
        "inclusionLists": [
            [
                transaction.model_dump(
                    mode="json", by_alias=True, exclude_none=True
                )
            ]
        ],
    }
    with (
        ForkCache() as cache,
        pytest.raises(ValueError, match="committee position"),
    ):
        build_t8n_from_cli_options(
            options, StringIO(json.dumps(inputs)), cache
        )
