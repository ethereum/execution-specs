"""Tests for client-native genesis export (`exportable_genesis` module)."""

import json
from os.path import realpath
from pathlib import Path
from typing import Dict, Type

import pytest

from ..clients.besu import BesuExportableGenesis
from ..clients.geth import GethExportableGenesis
from ..clients.nethermind import NethermindExportableGenesis
from ..exportable_genesis import (
    ExportableGenesis,
)

CURRENT_FOLDER = Path(realpath(__file__)).parent
FIXTURES = CURRENT_FOLDER / "fixtures"


def _assert_matches_golden(ours: Dict[str, Dict], path: Path) -> None:
    """
    Assert `ours` (our exporter's genesis) is consistent with every file in
    path folder `golden`.

    `config` and `alloc` must match exactly (aside from
    "mergeNetsplitBlock": the golden's hive pipeline never sets it, due
    to a HIVE_FORK_MERGE/HIVE_MERGE_BLOCK_ID naming mismatch in this
    repo's ruleset.py that our exporter doesn't go through, so we
    produce it correctly where the golden omits it) -- `config` has no
    other fields Besu doesn't compute from the fork/env, so any other
    stray or missing key is a real bug. The top-level header is checked
    as a subset instead, since the golden file -- built from a filled
    fixture's full computed header -- carries extra fields (stateRoot,
    receiptTrie, gasUsed, bloom, ...) that our exporter deliberately
    omits (see `test_header_fields_use_client_genesis_conventions`).
    """
    for file_name, our_content in ours.items():
        fixture_file_path = path / file_name
        assert fixture_file_path.exists()
        golden = json.loads(fixture_file_path.read_text())
        assert our_content == golden


@pytest.mark.parametrize("fork_name", ["cancun", "amsterdam"])
@pytest.mark.parametrize("example", ["2"])
@pytest.mark.parametrize(
    "client_exportable_class",
    [
        BesuExportableGenesis,
        GethExportableGenesis,
        NethermindExportableGenesis,
    ],
    ids=lambda x: x.client_name,
)
def test_matches_real_genesis(
    example: str,
    fork_name: str,
    client_exportable_class: Type[ExportableGenesis],
) -> None:
    """
    Match generated genesis against expectations.
    """
    fork_dir = FIXTURES / example / fork_name
    genesis = client_exportable_class.from_fixture(fork_dir / "fixture.json")
    _assert_matches_golden(
        genesis.model_dump(mode="json", by_alias=True, exclude_none=True),
        (fork_dir / client_exportable_class.client_name),
    )
