"""Verify transition-tool transport retains complete inclusion context."""

import json
from pathlib import Path

from execution_testing.base_types import Bytes
from execution_testing.client_clis import TransitionTool
from execution_testing.forks import Bogota
from execution_testing.test_types import (
    Alloc,
    Environment,
    InclusionListClaim,
    InclusionListReplayLimits,
    Transaction,
)


def test_inclusion_list_input_serialization(tmp_path: Path) -> None:
    """Keep ordering, duplicate claims and explicit limits in every path."""
    tx = Transaction(gas_limit=21_000).with_signature_and_sender()
    claim = InclusionListClaim(transaction_hash=tx.hash, transaction_index=1)
    data = TransitionTool.TransitionToolData(
        alloc=Alloc(),
        txs=[],
        env=Environment(),
        fork=Bogota,
        chain_id=1,
        reward=0,
        blob_schedule=Bogota.blob_schedule(),
        inclusion_list_txs=[tx],
        inclusion_list_membership=[Bytes("0x0102")],
        inclusion_list_claims=[claim, claim],
        inclusion_list_replay_limits=InclusionListReplayLimits(
            max_code_bodies=3, max_code_bytes=1234
        ),
    )
    inputs = data.to_input()
    encoded = inputs.model_dump(mode="json", by_alias=True, exclude_none=True)
    assert (
        json.loads(inputs.model_dump_json(by_alias=True, exclude_none=True))
        == encoded
    )
    assert encoded["inclusionListMembership"] == ["0x0102"]
    assert encoded["inclusionListClaims"] == [
        {"transactionHash": tx.hash.hex(), "transactionIndex": "0x1"},
        {"transactionHash": tx.hash.hex(), "transactionIndex": "0x1"},
    ]
    assert encoded["inclusionListReplayLimits"] == {
        "maxCodeBodies": "0x3",
        "maxCodeBytes": "0x4d2",
    }
    paths = inputs.to_files(tmp_path, by_alias=True, exclude_none=True)
    for field in (
        "inclusionListTransactions",
        "inclusionListMembership",
        "inclusionListClaims",
        "inclusionListReplayLimits",
    ):
        assert json.loads(Path(paths[field]).read_text()) == encoded[field]


def test_legacy_input_does_not_invent_membership_or_limits() -> None:
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
    assert data.inclusion_list_membership is None
    assert data.inclusion_list_replay_limits is None
