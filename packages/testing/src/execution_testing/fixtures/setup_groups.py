"""
Setup-group models and merge helpers for stateful fixture filling.

A "setup group" bundles the setup-phase payloads of one or more stateful
tests that share an identical declared setup sequence. Tests that fund
the same EOAs, deploy the same contracts, and populate the same storage
slots end up with the same ``setup_group_hash`` (derived from the RLP of
their signed setup transactions, see
``fixtures.blockchain.derive_setup_group_hash``) and can share a single
``setup_groups/<hash>.json`` file on disk.

Consumers (e.g. benchmarkoor) read the group file once, apply it to a
warm datadir snapshot, checkpoint the post-setup state, and replay
each test's execution-only payloads from that checkpoint — avoiding
the per-test setup cost entirely.

This module mirrors the partial-write/merge pattern used for
``fixtures.pre_alloc_groups``: each worker writes
``<hash>.partial.<worker>.<test_suffix>.json`` and the session master
merges them at teardown.
"""

import os
from pathlib import Path
from typing import Dict, List

from pydantic import Field

from execution_testing.base_types import CamelModel

from .blockchain import FixtureEngineNewPayload


class StatefulSetupGroup(CamelModel):
    """
    On-disk representation of a shared setup group.

    Tests with identical declared setup sequences share one group file.
    """

    network: str
    setup_group_hash: str
    test_ids: List[str] = Field(default_factory=list)
    payloads: List[FixtureEngineNewPayload] = Field(
        ..., alias="engineNewPayloads"
    )


def _worker_suffix() -> str:
    """Return the xdist worker id, or ``main`` outside xdist."""
    return os.environ.get("PYTEST_XDIST_WORKER") or "main"


def write_partial_setup_group(
    *,
    folder: Path,
    group: StatefulSetupGroup,
    test_suffix: str,
) -> None:
    """
    Write a single test's partial setup-group file (no locking).

    Each test contributes one partial. At session teardown
    ``merge_partial_setup_group_files`` reconciles partials sharing a
    hash into a single ``<hash>.json``.

    ``test_suffix`` disambiguates concurrent writes from the same
    worker (e.g. a sha256 prefix of the test id).
    """
    folder.mkdir(parents=True, exist_ok=True)
    partial_path = folder / (
        f"{group.setup_group_hash}.partial."
        f"{_worker_suffix()}.{test_suffix}.json"
    )
    partial_path.write_text(
        group.model_dump_json(by_alias=True, exclude_none=True, indent=2)
    )


def merge_partial_setup_group_files(folder: Path) -> None:
    """
    Merge all partial setup-group files under ``folder`` into final files.

    Called once by the session master (e.g. from ``pytest_sessionfinish``)
    after every worker has flushed its partials. Partials sharing a hash
    prefix collapse into ``<hash>.json``. Payload bytes are taken from the
    first partial read — they are byte-identical across partials for the
    same hash by construction — and ``test_ids`` from all partials are
    unioned.

    No-op if ``folder`` does not exist or contains no partials.
    """
    if not folder.exists():
        return
    partial_files = sorted(folder.glob("*.partial.*.json"))
    if not partial_files:
        return

    by_hash: Dict[str, StatefulSetupGroup] = {}
    seen_test_ids: Dict[str, set[str]] = {}

    for partial in partial_files:
        parsed = StatefulSetupGroup.model_validate_json(partial.read_text())
        group_hash = parsed.setup_group_hash
        if group_hash not in by_hash:
            by_hash[group_hash] = parsed
            seen_test_ids[group_hash] = set(parsed.test_ids)
        else:
            merged = by_hash[group_hash]
            for test_id in parsed.test_ids:
                if test_id not in seen_test_ids[group_hash]:
                    merged.test_ids.append(test_id)
                    seen_test_ids[group_hash].add(test_id)
        partial.unlink()

    for group_hash, merged in by_hash.items():
        target = folder / f"{group_hash}.json"
        target.write_text(
            merged.model_dump_json(
                by_alias=True, exclude_none=True, indent=2
            )
        )


__all__ = [
    "StatefulSetupGroup",
    "merge_partial_setup_group_files",
    "write_partial_setup_group",
]
