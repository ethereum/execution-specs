"""Verify transition-tool transport retains complete inclusion context."""

import json
from pathlib import Path

from execution_testing.client_clis import TransitionTool
from execution_testing.forks import Bogota
from execution_testing.test_types import (
    Alloc,
    Environment,
    OmissionClaim,
    Transaction,
)


def test_inclusion_list_input_serialization(tmp_path: Path) -> None:
    """Keep ordering and duplicate claims in every path."""
    tx = Transaction(gas_limit=21_000).with_signature_and_sender()
    claim = OmissionClaim(transaction_hash=tx.hash, evaluation_index=1)
    data = TransitionTool.TransitionToolData(
        alloc=Alloc(),
        txs=[],
        env=Environment(),
        fork=Bogota,
        chain_id=1,
        reward=0,
        blob_schedule=Bogota.blob_schedule(),
        inclusion_lists=[[tx] if i in (0, 9) else [] for i in range(16)],
        omission_claims=[claim, claim],
    )
    inputs = data.to_input()
    encoded = inputs.model_dump(mode="json", by_alias=True, exclude_none=True)
    assert (
        json.loads(inputs.model_dump_json(by_alias=True, exclude_none=True))
        == encoded
    )
    assert len(encoded["inclusionLists"]) == 16
    assert encoded["inclusionLists"][0] == encoded["inclusionLists"][9]
    assert all(
        not il
        for i, il in enumerate(encoded["inclusionLists"])
        if i not in (0, 9)
    )
    assert encoded["omissionClaims"] == [
        {"transactionHash": tx.hash.hex(), "evaluationIndex": "0x1"},
        {"transactionHash": tx.hash.hex(), "evaluationIndex": "0x1"},
    ]
    paths = inputs.to_files(tmp_path, by_alias=True, exclude_none=True)
    for field in (
        "inclusionLists",
        "omissionClaims",
    ):
        assert json.loads(Path(paths[field]).read_text()) == encoded[field]


def test_legacy_input_does_not_invent_separate_lists() -> None:
    """An old Profile-1-only request remains distinct from replay input."""
    data = TransitionTool.TransitionToolData(
        alloc=Alloc(),
        txs=[],
        env=Environment(),
        fork=Bogota,
        chain_id=1,
        reward=0,
        blob_schedule=None,
        inclusion_list_txs=[],
    ).to_input()
    assert data.inclusion_list_data() == {"inclusionListTransactions": []}
    assert data.inclusion_lists is None
