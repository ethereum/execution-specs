"""Fill-time execution-consistency check for Engine X fixtures."""

import json
from pathlib import Path
from typing import Any, Dict, List, NamedTuple, Optional, Tuple

from ethereum_rlp import rlp

ENGINE_X_FIXTURES_DIR = "blockchain_tests_engine_x"
SIBLING_FIXTURES_DIR = "blockchain_tests_engine"

# Every state-root-derived field of an execution payload. These are the only
# fields a packed (merged) genesis is allowed to change; everything else in a
# payload is a pure function of the test's execution.
_STATE_ROOT_DERIVED_FIELDS = ("stateRoot", "blockHash", "parentHash")

# Placeholder for the parent-hash value embedded in a block access list.
_PARENT_HASH_PLACEHOLDER = "<parent-hash>"


def _masked(node: Any, parent_hash: bytes) -> Any:
    """Mask every ``parent_hash`` leaf in a decoded BAL, hex the rest."""
    if isinstance(node, bytes):
        if parent_hash and node == parent_hash:
            return _PARENT_HASH_PLACEHOLDER
        return node.hex()
    return [_masked(child, parent_hash) for child in node]


def _scrubbed_bal(bal_hex: str, parent_hash_hex: str) -> Any:
    """
    Return a comparable form of a BAL with its parent hash masked out.

    The EIP-2935 system call writes the parent hash into the history
    contract on every block, so each payload's BAL embeds one
    state-root-derived value (at payload 0, the genesis hash itself). The
    BAL is decoded and that value masked rather than the whole field
    dropped, so the rest of the BAL still participates in the comparison:
    a leaked account shows up in the BAL before anywhere else. Storage
    values are RLP-encoded with leading zeros trimmed, so the trimmed
    parent hash is masked. An undecodable BAL (an intentionally malformed
    one from a negative test) is compared verbatim.
    """
    parent_hash = bytes.fromhex(parent_hash_hex.removeprefix("0x"))
    try:
        decoded = rlp.decode(bytes.fromhex(bal_hex.removeprefix("0x")))
    except Exception:
        return bal_hex
    return _masked(decoded, parent_hash.lstrip(b"\x00"))


class EngineXExecutionDriftError(Exception):
    """
    A packed pre-allocation group changed a test's execution.

    An Engine X fixture is filled against its group's merged genesis, while
    the test's `blockchain_test_engine` sibling is filled against the test's
    own pre-allocation. Their per-payload execution outputs (gas used,
    receipts root, logs bloom, ...) must be identical; a difference means
    either an account introduced by pre-alloc group packing leaked into the
    test's execution (see `pack_pre_alloc_groups`), or the test observes the
    genesis hash itself (e.g. via `BLOCKHASH(0)`), which depends on every
    account in the genesis and so cannot survive any grouping.
    """

    def __init__(self, mismatches: List[Tuple[str, str]], compared: int):
        """Initialize with the mismatched test ids and the compared count."""
        self.mismatches = mismatches
        self.compared = compared
        details = "\n".join(
            f"  {test_id}: {what}" for test_id, what in mismatches[:10]
        )
        if len(mismatches) > 10:
            details += f"\n  ... and {len(mismatches) - 10} more"
        super().__init__(
            f"{len(mismatches)} of {compared} Engine X fixtures execute "
            "differently against their packed pre-allocation group's genesis "
            "than against their own pre-allocation:\n"
            f"{details}\n"
            "Sharing a genesis changed these tests' execution: either an "
            "account introduced by pre-alloc group packing leaked into "
            "their execution, or they observe the genesis hash itself "
            "(e.g. via BLOCKHASH(0)). Isolate the affected tests with "
            '@pytest.mark.pre_alloc_group("separate") and re-fill.'
        )


class EngineXCheckResult(NamedTuple):
    """Comparison counts from a completed Engine X execution check."""

    compared: int
    skipped: int

    @property
    def summary(self) -> str:
        """Return a one-line summary of the check for the fill log."""
        summary = (
            f"{self.compared} Engine X fixtures execute identically "
            "against their packed group's genesis"
        )
        if self.skipped:
            summary += f" ({self.skipped} skipped: no sibling engine fixture)"
        return summary


def _scrubbed_payloads(fixture: Dict[str, Any]) -> List[Any]:
    """Return the fixture's payload entries minus state-root-derived fields."""
    payloads = []
    for entry in fixture.get("engineNewPayloads", []):
        entry = json.loads(json.dumps(entry))
        params = entry.get("params")
        if params and isinstance(params[0], dict):
            payload = params[0]
            bal = payload.get("blockAccessList")
            parent_hash = payload.get("parentHash")
            if isinstance(bal, str) and isinstance(parent_hash, str):
                payload["blockAccessList"] = _scrubbed_bal(bal, parent_hash)
            for field in _STATE_ROOT_DERIVED_FIELDS:
                payload.pop(field, None)
        payloads.append(entry)
    return payloads


def _describe_mismatch(base: List[Any], packed: List[Any]) -> str:
    """Return a short description of the first difference between payloads."""
    if len(base) != len(packed):
        return f"payload count: {len(base)} != {len(packed)}"
    for i, (base_entry, packed_entry) in enumerate(
        zip(base, packed, strict=False)
    ):
        if base_entry == packed_entry:
            continue
        base_payload = base_entry.get("params", [{}])[0]
        packed_payload = packed_entry.get("params", [{}])[0]
        if isinstance(base_payload, dict) and isinstance(packed_payload, dict):
            fields = sorted(
                field
                for field in set(base_payload) | set(packed_payload)
                if base_payload.get(field) != packed_payload.get(field)
            )
            if fields:
                return f"payload {i} differs in: {', '.join(fields)}"
        return f"payload {i} differs"
    return "payloads differ"


def verify_engine_x_execution(
    output_dir: Path,
) -> Optional[EngineXCheckResult]:
    """
    Verify that pre-alloc group packing did not change any test's execution.

    For every Engine X fixture (filled against its packed group's merged
    genesis), compare its `engineNewPayloads` against the test's
    `blockchain_test_engine` sibling fixture (filled against the test's own
    pre-allocation in the same session, with an independent `t8n` execution:
    Engine X fixtures never share the transition tool output cache). All
    payload fields except the state-root-derived ones must match exactly;
    each payload's block access list is compared with its own parent-hash
    bytes normalized out, since the EIP-2935 system write embeds that
    state-root-derived value in every BAL.

    Return the comparison counts, or ``None`` when one of the two fixture
    format trees was not generated at all (e.g. when filling with
    ``-m blockchain_test_engine_x``, which produces no siblings).

    Raise `EngineXExecutionDriftError` if any test executed differently.
    """
    engine_x_dir = output_dir / ENGINE_X_FIXTURES_DIR
    sibling_dir = output_dir / SIBLING_FIXTURES_DIR
    if not engine_x_dir.is_dir() or not sibling_dir.is_dir():
        return None

    compared = 0
    skipped = 0
    mismatches: List[Tuple[str, str]] = []
    for engine_x_file in engine_x_dir.rglob("*.json"):
        if "pre_alloc" in engine_x_file.parts:
            continue
        sibling_file = sibling_dir / engine_x_file.relative_to(engine_x_dir)
        if not sibling_file.exists():
            # A --single-fixture-per-file fill embeds the fixture format
            # name in every file name, so the sibling's basename differs.
            sibling_file = sibling_file.with_name(
                sibling_file.name.replace(
                    "blockchain_test_engine_x", "blockchain_test_engine"
                )
            )
        sibling_fixtures = (
            json.loads(sibling_file.read_text())
            if sibling_file.exists()
            else {}
        )
        for test_id, fixture in json.loads(engine_x_file.read_text()).items():
            sibling_id = test_id.replace(
                "blockchain_test_engine_x", "blockchain_test_engine"
            )
            sibling = sibling_fixtures.get(sibling_id)
            if sibling is None:
                skipped += 1
                continue
            compared += 1
            base = _scrubbed_payloads(sibling)
            packed = _scrubbed_payloads(fixture)
            if base != packed:
                mismatches.append((test_id, _describe_mismatch(base, packed)))

    if mismatches:
        raise EngineXExecutionDriftError(mismatches, compared)
    return EngineXCheckResult(compared=compared, skipped=skipped)
