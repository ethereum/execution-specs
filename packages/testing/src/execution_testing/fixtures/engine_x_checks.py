"""
Fill-time execution-consistency check for Engine X fixtures.

An Engine X fixture is filled against its packed pre-allocation group's
merged genesis, while the test's `blockchain_test_engine` sibling is
filled against the test's own pre-allocation. Their per-payload
execution outputs must be identical; `verify_engine_x_execution`
compares the two fixture trees after a fill and raises a classified,
per-cause report when they are not.

The check runs post-fill on the fixture files because the two formats of
a test are separate pytest items that may fill on different xdist
workers; the output directory is the only place both reliably exist. It
only needs that directory, so it can also be re-run standalone against a
failed fill's artifacts without re-filling.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple, Type, TypeVar

from pydantic import ValidationError

from execution_testing.base_types import Address, Bytes, Hash
from execution_testing.forks.forks.eips.prague.eip_2935 import (
    HISTORY_STORAGE_ADDRESS,
)
from execution_testing.test_types import AllocGroupHash
from execution_testing.test_types.block_access_list import BlockAccessList

from .blockchain import (
    BlockchainEngineFixture,
    BlockchainEngineXFixture,
    FixtureEngineNewPayload,
    FixtureExecutionPayload,
)
from .pre_alloc_groups import PreAllocGroup, PreAllocGroups

ENGINE_X_FIXTURES_DIR = BlockchainEngineXFixture.output_base_dir_name()
SIBLING_FIXTURES_DIR = BlockchainEngineFixture.output_base_dir_name()

# Path parts under a fixture format tree that do not contain fixture
# files (mirrors INDEX_EXCLUDED_PATH_PARTS in `cli/gen_index.py`).
_NON_FIXTURE_PATH_PARTS = frozenset({".meta", "pre_alloc"})

# Execution payload fields whose value is a function of the genesis
# state root and so legitimately differs between a test's own genesis
# and its packed group's genesis. Python field names of
# `FixtureExecutionPayload`; a unit test asserts they stay valid when
# the model changes.
STATE_ROOT_DERIVED_FIELDS = frozenset(
    {"state_root", "block_hash", "parent_hash"}
)

# Placeholder for the masked EIP-2935 parent-hash write in a BAL.
_PARENT_HASH_PLACEHOLDER = "<parent-hash>"

_VALUE_DISPLAY_LIMIT = 96

_FixtureT = TypeVar(
    "_FixtureT", BlockchainEngineFixture, BlockchainEngineXFixture
)


class EngineXCheckError(Exception):
    """The Engine X execution check failed to run on the fixture output."""


@dataclass(frozen=True)
class ExecutionDrift:
    """A fixture whose packed execution differs from its sibling's."""

    test_id: str
    signature: str
    """One-line cause classification; identical causes share it."""
    detail: str
    """Multi-line explanation rendered for the first example only."""


class EngineXExecutionDriftError(EngineXCheckError):
    """
    A packed pre-allocation group changed a test's execution.

    Either an account introduced by pre-alloc group packing leaked into
    the test's execution (see `pack_pre_alloc_groups`), or the test
    observes a block hash (e.g. via `BLOCKHASH`), which depends on every
    account in the genesis and so cannot survive any grouping. Drifts
    are grouped by cause signature so a single systemic cause reads as
    one diagnosis, not one failure per fixture.
    """

    MAX_SIGNATURES = 10
    MAX_EXAMPLE_IDS = 3

    def __init__(self, drifts: List[ExecutionDrift], compared: int):
        """Initialize with per-fixture drifts, grouped by signature."""
        self.drifts = drifts
        self.compared = compared
        grouped: Dict[str, List[ExecutionDrift]] = {}
        for drift in drifts:
            grouped.setdefault(drift.signature, []).append(drift)
        sections = []
        for signature, group in list(grouped.items())[: self.MAX_SIGNATURES]:
            ids = ", ".join(
                drift.test_id for drift in group[: self.MAX_EXAMPLE_IDS]
            )
            if len(group) > self.MAX_EXAMPLE_IDS:
                ids += f", ... and {len(group) - self.MAX_EXAMPLE_IDS} more"
            section = f"[{len(group)}x] {signature}\n  tests: {ids}"
            if group[0].detail:
                section += "\n" + "\n".join(
                    f"  {line}" for line in group[0].detail.splitlines()
                )
            sections.append(section)
        if len(grouped) > self.MAX_SIGNATURES:
            sections.append(
                f"... and {len(grouped) - self.MAX_SIGNATURES} more "
                "distinct causes"
            )
        super().__init__(
            f"{len(drifts)} of {compared} Engine X fixtures execute "
            "differently against their packed pre-allocation group's "
            "genesis than against their own pre-allocation "
            f"({len(grouped)} distinct cause(s)):\n\n" + "\n\n".join(sections)
        )


@dataclass(frozen=True)
class EngineXCheckResult:
    """Outcome of a completed Engine X execution check."""

    compared: int = 0
    skipped: int = 0
    skip_reason: str | None = None
    """Set when Engine X fixtures exist but nothing could be compared."""

    @property
    def summary(self) -> str:
        """Return a one-line summary of the check for the fill log."""
        summary = (
            f"{self.compared} Engine X fixtures execute identically "
            "against their packed group's genesis"
        )
        if self.skipped:
            summary += f" ({self.skipped} skipped: no sibling fixture)"
        return summary


def _sibling_test_id(engine_x_test_id: str) -> str:
    """Return the sibling-format id of an Engine X test id."""
    return engine_x_test_id.replace(
        BlockchainEngineXFixture.format_name,
        BlockchainEngineFixture.format_name,
    )


def _sibling_file(
    engine_x_file: Path, engine_x_dir: Path, sibling_dir: Path
) -> Path:
    """
    Return the sibling fixture file for an Engine X fixture file.

    A `--single-fixture-per-file` fill embeds the fixture format name in
    every file name, so the sibling's basename can differ.
    """
    sibling = sibling_dir / engine_x_file.relative_to(engine_x_dir)
    if not sibling.exists():
        sibling = sibling.with_name(
            sibling.name.replace(
                BlockchainEngineXFixture.format_name,
                BlockchainEngineFixture.format_name,
            )
        )
    return sibling


def _load_fixture_file(
    file: Path, fixture_cls: Type[_FixtureT]
) -> Dict[str, _FixtureT]:
    """Parse every fixture in a fixture file with its typed model."""
    try:
        raw = json.loads(file.read_text())
    except json.JSONDecodeError as e:
        raise EngineXCheckError(f"unreadable fixture file {file}: {e}") from e
    fixtures: Dict[str, _FixtureT] = {}
    for test_id, data in raw.items():
        try:
            fixtures[test_id] = fixture_cls.model_validate(data)
        except ValidationError as e:
            raise EngineXCheckError(
                f"cannot parse {fixture_cls.format_name!r} fixture "
                f"{test_id!r} in {file}: {e}"
            ) from e
    return fixtures


def _comparable_payload(payload: FixtureEngineNewPayload) -> Dict[str, Any]:
    """
    Return the payload as a dict without state-root-derived values.

    The block access list is replaced by its decoded, parent-hash-masked
    form, see `_comparable_bal`.
    """
    entry = payload.model_dump(
        mode="json",
        by_alias=True,
        exclude={
            "params": {
                0: set(STATE_ROOT_DERIVED_FIELDS) | {"block_access_list"}
            }
        },
    )
    execution_payload = payload.params[0]
    if execution_payload.block_access_list is not None:
        entry["params"][0]["blockAccessList"] = _comparable_bal(
            execution_payload.block_access_list,
            execution_payload.parent_hash,
        )
    return entry


def _comparable_bal(bal: Bytes, parent_hash: Hash) -> Any:
    """
    Return the decoded BAL with the EIP-2935 history write masked.

    The EIP-2935 system call writes the block's parent hash into the
    history contract on every block; at payload 0 that value is the
    genesis hash itself, so it is the one BAL entry that legitimately
    differs between a test's own genesis and its packed group's genesis.
    Only that write is masked: a storage change of the history contract
    whose written value equals the payload's own parent hash. A
    parent-hash-valued write to any other account is genuine drift (the
    test observes block hashes and cannot survive grouping). An
    undecodable BAL (an intentionally malformed one from a negative
    test) is compared verbatim.

    Known limitation: a header parent hash injected with
    `Block.rlp_modifier=Header(parent_hash=...)` defeats the mask. The
    override is applied after t8n has executed the block, so the BAL
    keeps the real parent hash while the payload field holds the
    injected value; the mask matches neither, and the check fails
    loudly on a difference that packing did not cause. No test does
    this today. If one appears, isolate it with
    `@pytest.mark.pre_alloc_group("separate")`, or make the mask derive
    the expected value from the chain itself (the genesis hash at
    payload 0, the previous payload's block hash after that) instead of
    the payload's own `parent_hash` field.
    """
    try:
        accounts = BlockAccessList.from_rlp(bal)
    except Exception:
        return str(bal)
    parent_hash_value = int.from_bytes(parent_hash, "big")
    dumped = accounts.model_dump(mode="json")
    for account in dumped:
        if int(account["address"], 16) != HISTORY_STORAGE_ADDRESS:
            continue
        for slot in account["storage_changes"]:
            for change in slot["slot_changes"]:
                if int(change["post_value"], 16) == parent_hash_value:
                    change["post_value"] = _PARENT_HASH_PLACEHOLDER
    return dumped


class _GroupLookup:
    """Lazily load packed pre-allocation groups for drift attribution."""

    def __init__(self, engine_x_dir: Path):
        """Initialize with the Engine X fixture tree to look under."""
        self._folder = engine_x_dir / "pre_alloc"
        self._groups: PreAllocGroups | None = None

    def get(self, pre_hash: AllocGroupHash) -> PreAllocGroup | None:
        """Return the group for a hash, or None if unavailable."""
        if self._groups is None:
            if not self._folder.is_dir():
                return None
            try:
                self._groups = PreAllocGroups.from_folder(
                    self._folder, lazy_load=True
                )
            except Exception:
                return None
        try:
            return self._groups[pre_hash]
        except Exception:
            return None


def _short(value: Any) -> str:
    """Render a value for an error message, truncated if long."""
    text = value if isinstance(value, str) else json.dumps(value)
    if len(text) > _VALUE_DISPLAY_LIMIT:
        text = f"{text[:_VALUE_DISPLAY_LIMIT]}... ({len(text)} chars)"
    return text


def _hex_int(value: Any) -> int | None:
    """Parse a hex string to an int, or return None."""
    try:
        return int(value, 16)
    except (TypeError, ValueError):
        return None


def _diff_fields(
    base_entry: Dict[str, Any], packed_entry: Dict[str, Any]
) -> List[Tuple[str, Any, Any]]:
    """Return the (field, own, packed) diffs of two comparable payloads."""
    diffs: List[Tuple[str, Any, Any]] = []
    for key in sorted(set(base_entry) | set(packed_entry)):
        base_value = base_entry.get(key)
        packed_value = packed_entry.get(key)
        if base_value == packed_value:
            continue
        if (
            key != "params"
            or not isinstance(base_value, list)
            or not isinstance(packed_value, list)
            or len(base_value) != len(packed_value)
        ):
            diffs.append((key, base_value, packed_value))
            continue
        for i, (base_param, packed_param) in enumerate(
            zip(base_value, packed_value, strict=True)
        ):
            if base_param == packed_param:
                continue
            if (
                i == 0
                and isinstance(base_param, dict)
                and isinstance(packed_param, dict)
            ):
                for field in sorted(set(base_param) | set(packed_param)):
                    if base_param.get(field) != packed_param.get(field):
                        diffs.append(
                            (
                                field,
                                base_param.get(field),
                                packed_param.get(field),
                            )
                        )
            else:
                diffs.append((f"params[{i}]", base_param, packed_param))
    return diffs


def _parent_hash_write_slot(
    base_account: Dict[str, Any],
    packed_account: Dict[str, Any],
    base_parent_hash: int,
    packed_parent_hash: int,
) -> str | None:
    """Return the slot where each side stored its own parent hash."""
    packed_slots = {
        slot["slot"]: slot for slot in packed_account["storage_changes"]
    }
    for base_slot in base_account["storage_changes"]:
        packed_slot = packed_slots.get(base_slot["slot"])
        if packed_slot is None:
            continue
        packed_changes = {
            change["block_access_index"]: change
            for change in packed_slot["slot_changes"]
        }
        for base_change in base_slot["slot_changes"]:
            packed_change = packed_changes.get(
                base_change["block_access_index"]
            )
            if packed_change is None or base_change == packed_change:
                continue
            if (
                _hex_int(base_change["post_value"]) == base_parent_hash
                and _hex_int(packed_change["post_value"]) == packed_parent_hash
            ):
                return str(base_slot["slot"])
    return None


def _diff_bal(
    payload_index: int,
    base_bal: Any,
    packed_bal: Any,
    base_payload: FixtureExecutionPayload,
    packed_payload: FixtureExecutionPayload,
    sibling: BlockchainEngineFixture,
    engine_x: BlockchainEngineXFixture,
    groups: _GroupLookup,
) -> Tuple[str, str]:
    """Return (signature, detail) for a block-access-list difference."""
    prefix = f"payload {payload_index}"
    if isinstance(base_bal, str) or isinstance(packed_bal, str):
        return (
            f"{prefix}: blockAccessList differs (undecodable BAL "
            "compared verbatim)",
            f"own:    {_short(base_bal)}\npacked: {_short(packed_bal)}",
        )
    base_accounts = {account["address"]: account for account in base_bal}
    packed_accounts = {account["address"]: account for account in packed_bal}
    extra = sorted(set(packed_accounts) - set(base_accounts))
    missing = sorted(set(base_accounts) - set(packed_accounts))
    if extra:
        address = extra[0]
        signature = (
            f"{prefix}: account {address} appears in the packed "
            "fixture's BAL only"
        )
        if Address(address) in sibling.pre.root:
            return signature, (
                "the account is declared in the test's own "
                "pre-allocation but only touched under the packed "
                "genesis: packing changed the execution path"
            )
        group = groups.get(engine_x.pre_hash)
        if group is not None and Address(address) in group.pre:
            others = ", ".join(group.test_ids[:3])
            return signature, (
                "the account is absent from the test's own "
                "pre-allocation but present in pre-alloc group "
                f"{engine_x.pre_hash} ({group.test_count} tests, e.g. "
                f"{others}): an account introduced by packing leaked "
                "into this test's execution. Isolate the test with "
                '@pytest.mark.pre_alloc_group("separate") or declare '
                "the account in its pre-allocation"
            )
        return signature, (
            "the account is absent from the test's own pre-allocation "
            "and from its packed pre-alloc group: packing changed the "
            "execution path"
        )
    if missing:
        return (
            f"{prefix}: account {missing[0]} is missing from the "
            "packed fixture's BAL",
            "the test touches the account only under its own genesis: "
            "packing changed the execution path",
        )
    base_parent_hash = int.from_bytes(base_payload.parent_hash, "big")
    packed_parent_hash = int.from_bytes(packed_payload.parent_hash, "big")
    for address, base_account in base_accounts.items():
        packed_account = packed_accounts[address]
        if base_account == packed_account:
            continue
        slot = _parent_hash_write_slot(
            base_account,
            packed_account,
            base_parent_hash,
            packed_parent_hash,
        )
        if slot is not None:
            return (
                f"{prefix}: account {address} writes its block's "
                f"parent hash to storage (slot {slot})",
                "each fixture's BAL stores its own parent hash: the "
                "test observes block hashes (e.g. via BLOCKHASH), "
                "which cannot survive pre-alloc grouping. Isolate the "
                'test with @pytest.mark.pre_alloc_group("separate")',
            )
        return (
            f"{prefix}: BAL differs for account {address}",
            f"own:    {_short(base_account)}\n"
            f"packed: {_short(packed_account)}",
        )
    return f"{prefix}: blockAccessList differs", ""


def _diagnose(
    test_id: str,
    engine_x: BlockchainEngineXFixture,
    sibling: BlockchainEngineFixture,
    base_payloads: List[Dict[str, Any]],
    packed_payloads: List[Dict[str, Any]],
    groups: _GroupLookup,
) -> ExecutionDrift:
    """Classify the first difference between two payload sequences."""
    if len(base_payloads) != len(packed_payloads):
        return ExecutionDrift(
            test_id,
            signature="payload count differs",
            detail=(
                f"sibling has {len(base_payloads)} payloads, packed "
                f"fixture has {len(packed_payloads)}: packing changed "
                "block-level outcomes"
            ),
        )
    for index, (base_entry, packed_entry) in enumerate(
        zip(base_payloads, packed_payloads, strict=True)
    ):
        if base_entry == packed_entry:
            continue
        diffs = _diff_fields(base_entry, packed_entry)
        fields = sorted({field for field, _, _ in diffs})
        if "blockAccessList" in fields:
            base_bal, packed_bal = next(
                (base_value, packed_value)
                for field, base_value, packed_value in diffs
                if field == "blockAccessList"
            )
            signature, detail = _diff_bal(
                index,
                base_bal,
                packed_bal,
                sibling.payloads[index].params[0],
                engine_x.payloads[index].params[0],
                sibling,
                engine_x,
                groups,
            )
            other_fields = [f for f in fields if f != "blockAccessList"]
            if other_fields:
                detail += (
                    f"\nthe payload also differs in: {', '.join(other_fields)}"
                )
            return ExecutionDrift(test_id, signature, detail)
        detail_lines = []
        for field, base_value, packed_value in diffs[:5]:
            detail_lines.append(f"{field}:")
            detail_lines.append(f"  own:    {_short(base_value)}")
            detail_lines.append(f"  packed: {_short(packed_value)}")
        return ExecutionDrift(
            test_id,
            signature=f"payload {index} differs in: {', '.join(fields)}",
            detail="\n".join(detail_lines),
        )
    return ExecutionDrift(test_id, "payloads differ", "")


def verify_engine_x_execution(output_dir: Path) -> EngineXCheckResult:
    """
    Verify that pre-alloc group packing did not change any test's
    execution.

    For every Engine X fixture (filled against its packed group's merged
    genesis), compare its payloads against the test's
    `blockchain_test_engine` sibling fixture (filled against the test's
    own pre-allocation in the same session, with an independent `t8n`
    execution: Engine X fixtures never share the transition tool output
    cache). All payload fields except the state-root-derived ones must
    match exactly; each payload's block access list is compared with the
    EIP-2935 history write of its own parent hash masked out, see
    `_comparable_bal`.

    Return the comparison counts; `skip_reason` is set when Engine X
    fixtures exist but nothing could be compared (e.g. when filling with
    `-m blockchain_test_engine_x`, which produces no siblings).

    Raise `EngineXExecutionDriftError` if any test executed differently,
    or `EngineXCheckError` if a fixture file cannot be parsed.
    """
    engine_x_dir = output_dir / ENGINE_X_FIXTURES_DIR
    sibling_dir = output_dir / SIBLING_FIXTURES_DIR
    if not engine_x_dir.is_dir():
        return EngineXCheckResult()
    if not sibling_dir.is_dir():
        return EngineXCheckResult(
            skip_reason=(
                "Engine X execution consistency check skipped: this "
                f"fill generated no {SIBLING_FIXTURES_DIR} fixtures to "
                "compare against (e.g. filling with `-m "
                f"{BlockchainEngineXFixture.format_name}`). Leaks from "
                "pre-alloc group packing are not verified for this "
                "output."
            )
        )

    groups = _GroupLookup(engine_x_dir)
    compared = 0
    skipped = 0
    drifts: List[ExecutionDrift] = []
    for engine_x_file in sorted(engine_x_dir.rglob("*.json")):
        relative_parts = engine_x_file.relative_to(engine_x_dir).parts
        if _NON_FIXTURE_PATH_PARTS.intersection(relative_parts):
            continue
        sibling_file = _sibling_file(engine_x_file, engine_x_dir, sibling_dir)
        siblings = (
            _load_fixture_file(sibling_file, BlockchainEngineFixture)
            if sibling_file.exists()
            else {}
        )
        for test_id, fixture in _load_fixture_file(
            engine_x_file, BlockchainEngineXFixture
        ).items():
            sibling = siblings.get(_sibling_test_id(test_id))
            if sibling is None:
                skipped += 1
                continue
            compared += 1
            base = [_comparable_payload(p) for p in sibling.payloads]
            packed = [_comparable_payload(p) for p in fixture.payloads]
            if base != packed:
                drifts.append(
                    _diagnose(test_id, fixture, sibling, base, packed, groups)
                )

    if drifts:
        raise EngineXExecutionDriftError(drifts, compared)
    skip_reason = None
    if compared == 0 and skipped > 0:
        skip_reason = (
            "Engine X execution consistency check skipped: none of the "
            f"{skipped} Engine X fixtures have a {SIBLING_FIXTURES_DIR} "
            "sibling fixture to compare against. Leaks from pre-alloc "
            "group packing are not verified for this output."
        )
    return EngineXCheckResult(
        compared=compared, skipped=skipped, skip_reason=skip_reason
    )
