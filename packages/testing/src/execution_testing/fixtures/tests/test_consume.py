"""Tests for the consume index file models."""

import json

from execution_testing.base_types import Hash
from execution_testing.fixtures.consume import IndexFile

# A fixture hash as an older framework version wrote it: serialized from a
# number, so its two leading zero bytes are missing.
LEGACY_FIXTURE_HASH = (
    "0x511ecc977c8f0ea5e940b47f4faac9ff6f7b77b2bb82f4d94a369f4475d1463"
)


def _index_json(root_hash: str, fixture_hash: str) -> str:
    """Return an index file holding a single test case."""
    return json.dumps(
        {
            "root_hash": root_hash,
            "created_at": "2025-10-09T22:01:49.594302",
            "test_count": 1,
            "forks": ["Prague"],
            "fixture_formats": ["state_test"],
            "test_cases": [
                {
                    "id": "tests/a.py::test_a",
                    "json_path": "state_tests/a.json",
                    "fixture_hash": fixture_hash,
                    "fork": "Prague",
                    "format": "state_test",
                    "pre_hash": None,
                }
            ],
        }
    )


def test_index_file_reads_legacy_hashes() -> None:
    """
    Load an index file written before its hashes were typed.

    Those hashes were serialized from numbers, which drops leading zero
    bytes and writes an unavailable root hash as ``0x0``, so reading one
    back must pad rather than reject it.
    """
    index = IndexFile.model_validate_json(
        _index_json(root_hash="0x0", fixture_hash=LEGACY_FIXTURE_HASH)
    )

    assert index.root_hash == Hash(0)

    fixture_hash = index.test_cases[0].fixture_hash
    assert len(fixture_hash) == 32
    assert int(str(fixture_hash), 16) == int(LEGACY_FIXTURE_HASH, 16)


def test_index_file_reads_full_width_hashes() -> None:
    """Load an index file whose hashes already carry their zero bytes."""
    full_width = str(Hash(int(LEGACY_FIXTURE_HASH, 16)))

    index = IndexFile.model_validate_json(
        _index_json(root_hash=full_width, fixture_hash=full_width)
    )

    assert index.root_hash == Hash(full_width)
    assert index.test_cases[0].fixture_hash == Hash(full_width)
