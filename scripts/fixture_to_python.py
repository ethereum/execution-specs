#!/usr/bin/env python3
"""
Convert compiled state_test fixtures to Python test files.

Reads compiled fixture JSON (from --fill-static-tests) and source filler
(for _info.comment), then generates a Python test file with:
- Module docstring from _info.comment
- Op-language bytecode (readable, self-documenting)
- Proper pytest markers and structure
- Maximum embedded context for future Amsterdam porting

Usage:
    python scripts/fixture_to_python.py \
        --fixtures /tmp/compiled_static/ \
        --fillers tests/static/state_tests/ \
        --output tests/ported_static/
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Categories that are prohibitively slow to fill — mark with @pytest.mark.slow
# ---------------------------------------------------------------------------

SLOW_CATEGORIES = {
    "stQuadraticComplexityTest",
    "stStaticCall",
    "stTimeConsuming",
}

# ---------------------------------------------------------------------------
# Fork ordering (earliest to latest)
# ---------------------------------------------------------------------------

FORK_ORDER = [
    "Frontier",
    "Homestead",
    "EIP150",
    "EIP158",
    "Byzantium",
    "Constantinople",
    "ConstantinopleFix",
    "Istanbul",
    "Berlin",
    "London",
    "Paris",
    "Shanghai",
    "Cancun",
    "Prague",
    "Osaka",
    "Amsterdam",
]
FORK_RANK = {name: i for i, name in enumerate(FORK_ORDER)}


def earliest_fork(forks: set[str]) -> str:
    """Return the earliest fork from a set, by FORK_ORDER."""
    known = [f for f in forks if f in FORK_RANK]
    if not known:
        return sorted(forks)[0]  # fallback alphabetical
    return min(known, key=lambda f: FORK_RANK[f])


def fork_before(fork_name: str) -> str | None:
    """Return the fork immediately before the given fork in FORK_ORDER."""
    if fork_name not in FORK_RANK:
        return None
    idx = FORK_RANK[fork_name]
    if idx <= 0:
        return None
    return FORK_ORDER[idx - 1]


def _next_fork(fork_name: str) -> str | None:
    """Return the fork immediately after the given fork in FORK_ORDER."""
    if fork_name not in FORK_RANK:
        return None
    idx = FORK_RANK[fork_name]
    if idx + 1 >= len(FORK_ORDER):
        return None
    return FORK_ORDER[idx + 1]


def parse_network_upper_bound(network_str: str) -> str | None:
    """
    Parse the upper fork bound from a network string.

    Examples:
        ">=Cancun"       -> None (no upper bound)
        ">=Cancun<Osaka" -> "Osaka" (exclusive upper bound)
        "Cancun"         -> None (exact fork)

    """
    match = re.search(r"<(\w+)$", network_str.strip())
    if match:
        return match.group(1)
    return None


def parse_network_lower_bound(network_str: str) -> str | None:
    """
    Parse the lower fork bound from a network string.

    Examples:
        ">=Cancun"       -> "Cancun"
        ">=Cancun<Osaka" -> "Cancun"
        "Cancun"         -> "Cancun" (exact fork)

    """
    match = re.match(r">=(\w+)", network_str.strip())
    if match:
        return match.group(1)
    # Exact fork name
    s = network_str.strip()
    if s in FORK_RANK:
        return s
    return None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def camel_to_snake(name: str) -> str:
    """Convert CamelCase to snake_case, preserving leading numbers."""
    # Insert _ before uppercase letters preceded by lowercase or digits
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)
    # Insert _ before uppercase followed by lowercase (ABCDef -> ABC_Def)
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", s)
    return s.lower()


def filler_name_to_test_name(filler_stem: str) -> str:
    """
    Convert filler stem to Python test function/file name.

    e.g. 'callcode_checkPCFiller' -> 'test_callcode_check_pc'
    e.g. 'ContractCreationSpamFiller' -> 'test_contract_creation_spam'
    e.g. 'mem32kb+1Filler' -> 'test_mem32kb_plus_1'
    e.g. 'mem32kb-1Filler' -> 'test_mem32kb_minus_1'
    """
    # Strip 'Filler' suffix
    name = re.sub(r"Filler$", "", filler_stem)
    result = "test_" + camel_to_snake(name)
    # Replace + and - with descriptive words before general cleanup
    result = result.replace("+", "_plus_")
    result = result.replace("-", "_minus_")
    # Replace remaining non-alphanumeric chars with underscores
    result = re.sub(r"[^a-z0-9_]", "_", result)
    # Collapse multiple underscores
    result = re.sub(r"_+", "_", result)
    return result.strip("_")


def hex_to_int(v: str) -> int:
    """Convert hex string to int."""
    return int(v, 16)


def format_int(v: int, *, force_hex: bool = False) -> str:
    """Format an int as Python literal. Use hex for large values."""
    if force_hex or v > 0xFFFF:
        return hex(v)
    return str(v)


def format_balance(v: int) -> str:
    """Format balance as Python literal."""
    return format_int(v, force_hex=(v > 9999))


def format_storage(
    storage: dict[str, str],
    indent: str = "                ",
) -> str:
    """Format storage dict as Python literal."""
    if not storage:
        return "{}"
    items = []
    for k, v in sorted(storage.items(), key=lambda x: int(x[0], 16)):
        items.append(f"{hex(int(k, 16))}: {hex(int(v, 16))}")
    single = "{" + ", ".join(items) + "}"
    if len(single) <= 50:
        return single
    formatted: list[str] = []
    for item in items:
        formatted.append(item + ",")
    inner = ("\n" + indent).join(formatted)
    close = indent[4:] if len(indent) >= 4 else ""
    return "{\n" + indent + inner + "\n" + close + "}"


def _format_exception(exc_str: str) -> str:
    """
    Format an expectException string as Python code.

    Single: 'TransactionException.FOO' -> 'TransactionException.FOO'
    Compound: 'TransactionException.FOO|TransactionException.BAR'
        -> '[TransactionException.FOO, TransactionException.BAR]'
    """
    parts = [p.strip() for p in exc_str.split("|")]
    if len(parts) == 1:
        return parts[0]
    single = "[" + ", ".join(parts) + "]"
    if len("        error=" + single + ",") <= 79:
        return single
    inner = ",\n            ".join(parts)
    return "[\n            " + inner + ",\n        ]"


def _format_access_list(
    al: list[dict[str, Any]],
    multiline: bool = True,
) -> str:
    """Format an access list as Python code."""
    if not al:
        return "[]"
    items = []
    for entry in al:
        addr = _pad_address(entry["address"])
        keys = entry.get("storageKeys", [])
        if keys:
            key_strs = ", ".join(f'Hash("{k}")' for k in keys)
            single = (
                f'AccessList(address=Address("{addr}"),'
                f" storage_keys=[{key_strs}])"
            )
            if multiline and len("            " + single) > 79:
                key_items = [f'Hash("{k}")' for k in keys]
                ki = ",\n                    ".join(key_items)
                items.append(
                    f"AccessList(\n"
                    f'                address=Address("{addr}"),\n'
                    f"                storage_keys=[\n"
                    f"                    {ki},\n"
                    f"                ],\n"
                    f"            )"
                )
            else:
                items.append(single)
        else:
            items.append(
                f'AccessList(address=Address("{addr}"), storage_keys=[])'
            )
    if not multiline:
        return "[" + ", ".join(items) + "]"
    if len(items) == 1:
        single = f"[{items[0]}]"
        if "\n" not in single and len("        " + single + ",") <= 79:
            return single
    inner = ",\n            ".join(items)
    return f"[\n            {inner},\n        ]"


def bytecode_to_op_string(hex_code: str) -> str | None:
    """
    Convert hex bytecode to Op expression string.

    Returns None if bytecode is empty, conversion fails, or roundtrip
    produces different bytecode (evm_bytes has edge cases with PUSH parsing).
    """
    if hex_code in ("0x", "0x00", ""):
        return None

    raw = hex_code[2:] if hex_code.startswith("0x") else hex_code

    try:
        from execution_testing import Op
        from execution_testing.cli.evm_bytes import process_evm_bytes_string

        op_str = process_evm_bytes_string(raw, assembly=False)
        # Verify roundtrip: compile Op back to hex and compare
        compiled = eval(op_str, {"Op": Op})  # noqa: S307
        if compiled.hex() != raw.lower():
            return None  # Roundtrip mismatch — fall back to bytes.fromhex
        return op_str
    except Exception:
        return None


def bytecode_to_assembly_summary(
    hex_code: str, max_lines: int = 20
) -> str | None:
    """Get a short assembly summary of bytecode for docstrings."""
    if hex_code in ("0x", "0x00", ""):
        return None

    raw = hex_code[2:] if hex_code.startswith("0x") else hex_code

    try:
        from execution_testing.cli.evm_bytes import process_evm_bytes_string

        asm = process_evm_bytes_string(raw, assembly=True)
        lines = [x for x in asm.split("\n") if x.strip()]
        if len(lines) <= max_lines:
            return "\n".join(lines)
        return (
            "\n".join(lines[:max_lines])
            + f"\n... ({len(lines) - max_lines} more instructions)"
        )
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Filler context extraction
# ---------------------------------------------------------------------------


def _load_filler_data(filler_path: Path) -> dict | None:
    """
    Load and parse a filler file (JSON or YAML).

    Return the parsed dict, or None on failure.
    """
    raw: str | None = None
    suffix = filler_path.suffix

    if filler_path.exists():
        raw = filler_path.read_text()
    else:
        # Try relative to repo root
        try:
            repo_root = Path(
                subprocess.check_output(
                    ["git", "rev-parse", "--show-toplevel"],
                    stderr=subprocess.DEVNULL,
                )
                .decode()
                .strip()
            )
            resolved = repo_root / filler_path
            if resolved.exists():
                raw = resolved.read_text()
        except (subprocess.CalledProcessError, OSError):
            pass

    if raw is None:
        return None

    try:
        if suffix == ".json":
            return json.loads(raw)
        elif suffix in (".yml", ".yaml"):
            try:
                import yaml

                return yaml.safe_load(raw)
            except ImportError:
                return None
        return None
    except Exception:
        return None


def load_filler_comment(filler_path: Path) -> str:
    """Extract _info.comment from a filler file."""
    data = _load_filler_data(filler_path)
    if not data:
        return ""
    try:
        for _test_name, test_data in data.items():
            if isinstance(test_data, dict) and "_info" in test_data:
                comment = test_data["_info"].get("comment", "")
                if comment:
                    return comment
    except Exception:
        pass
    return ""


def load_filler_network_upper_bound(filler_path: Path) -> str | None:
    """
    Extract the strictest upper fork bound from a filler's network fields.

    Parses expect[].network entries like ">=Cancun<Osaka" and returns the
    excluded fork name (e.g. "Osaka").  Returns None if no upper bound.
    """
    data = _load_filler_data(filler_path)
    if not data:
        return None
    try:
        upper_bounds: list[str] = []
        all_exact_forks: list[str] = []
        has_range = False
        for _test_name, test_data in data.items():
            if not isinstance(test_data, dict):
                continue
            expect = test_data.get("expect", [])
            if not isinstance(expect, list):
                continue
            for expect_entry in expect:
                if not isinstance(expect_entry, dict):
                    continue
                network = expect_entry.get("network", [])
                if isinstance(network, list):
                    for net_str in network:
                        s = str(net_str).strip()
                        bound = parse_network_upper_bound(s)
                        if bound:
                            upper_bounds.append(bound)
                            has_range = True
                        elif ">=" in s:
                            has_range = True
                        elif s in FORK_RANK:
                            all_exact_forks.append(s)

        # Range syntax like ">=Cancun<Osaka" — return the excluded fork
        if upper_bounds:
            known = [b for b in upper_bounds if b in FORK_RANK]
            if known:
                return min(known, key=lambda f: FORK_RANK[f])
            return upper_bounds[0]

        # Exact fork names only (e.g. ["Cancun", "Prague"]) — the fork
        # after the latest listed fork is the excluded upper bound
        if all_exact_forks and not has_range:
            latest = max(all_exact_forks, key=lambda f: FORK_RANK[f])
            latest_idx = FORK_RANK[latest]
            if latest_idx + 1 < len(FORK_ORDER):
                return FORK_ORDER[latest_idx + 1]

        return None
    except Exception:
        return None


def load_filler_network_lower_bound(filler_path: Path) -> str | None:
    """
    Extract the earliest fork from a filler's network fields.

    Parse expect[].network entries like ">=Cancun" or ">=Shanghai"
    and return the earliest lower bound (e.g. "Cancun").
    For exact fork lists like ["Cancun", "Prague"], return the earliest.
    """
    data = _load_filler_data(filler_path)
    if not data:
        return None
    try:
        lower_bounds: list[str] = []
        all_exact_forks: list[str] = []
        for _test_name, test_data in data.items():
            if not isinstance(test_data, dict):
                continue
            expect = test_data.get("expect", [])
            if not isinstance(expect, list):
                continue
            for expect_entry in expect:
                if not isinstance(expect_entry, dict):
                    continue
                network = expect_entry.get("network", [])
                if isinstance(network, list):
                    for net_str in network:
                        s = str(net_str).strip()
                        bound = parse_network_lower_bound(s)
                        if bound and bound in FORK_RANK:
                            lower_bounds.append(bound)
                        elif s in FORK_RANK:
                            all_exact_forks.append(s)

        if lower_bounds:
            return min(lower_bounds, key=lambda f: FORK_RANK[f])
        if all_exact_forks:
            return min(all_exact_forks, key=lambda f: FORK_RANK[f])
        return None
    except Exception:
        return None


_MAX_SOURCE_LINES = 30


class _FillerCodeSources:
    """Source code comments extracted from a filler file."""

    def __init__(self) -> None:
        # {normalized_address: comment} — works for plain-address fillers
        self.by_address: dict[str, str] = {}
        # {hex_bytecode_lower: comment} — for :raw and 0x... code
        self.by_hex: dict[str, str] = {}
        # Source comment for the contract with the "target" label
        self.target_source: str = ""

    def lookup(
        self,
        compiled_addr: str,
        compiled_hex: str,
        is_to_addr: bool,
    ) -> str:
        """Look up source comment for a compiled fixture address."""
        norm = _normalize_address(compiled_addr)

        # 1. Try direct address match (plain-address fillers)
        if norm in self.by_address:
            return self.by_address[norm]

        # 2. Try bytecode match (:raw and hex code)
        hex_key = compiled_hex.lower()
        if hex_key.startswith("0x"):
            hex_key = hex_key[2:]
        if hex_key and hex_key in self.by_hex:
            return self.by_hex[hex_key]

        # 3. For the to_addr, use the target label source
        if is_to_addr and self.target_source:
            return self.target_source

        return ""


def _extract_filler_code_sources(
    filler_data: dict | None,
) -> _FillerCodeSources:
    """
    Extract original source code from filler pre-state.

    Return a _FillerCodeSources object supporting lookup by address,
    bytecode hex, and label role.
    """
    result = _FillerCodeSources()
    if not filler_data:
        return result

    try:
        for _test_name, test_data in filler_data.items():
            if not isinstance(test_data, dict):
                continue
            pre = test_data.get("pre", {})
            if not isinstance(pre, dict):
                continue
            for addr_key, account in pre.items():
                if not isinstance(account, dict):
                    continue
                code = account.get("code")
                if not code or not isinstance(code, str):
                    continue
                code = code.strip()
                if not code:
                    continue

                comment = _classify_code_source(code)
                if not comment:
                    continue

                addr_str = str(addr_key)

                # Store by normalized address
                norm = _normalize_address(addr_str)
                result.by_address[norm] = comment

                # Store by hex for :raw and plain-hex code
                hex_bytes = _extract_hex_from_code(code)
                if hex_bytes:
                    result.by_hex[hex_bytes] = comment

                # Detect target/entry role from label
                if ":target:" in addr_str or ":entry:" in addr_str:
                    result.target_source = comment
    except Exception:
        pass
    return result


def _extract_hex_from_code(code: str) -> str:
    """
    Extract raw hex bytes from a code field, if applicable.

    Return lowercase hex string (no 0x prefix), or empty string.
    """
    stripped = code.strip()
    if stripped.startswith(":raw"):
        raw = stripped[4:].strip()
        if raw.startswith("0x"):
            return raw[2:].lower()
        return raw.lower()
    if stripped.startswith("0x"):
        return stripped[2:].lower()
    return ""


def _classify_code_source(code: str) -> str:
    """
    Classify a filler code field and return a source comment string.

    Return empty string if no useful comment can be generated.
    """
    stripped = code.strip()

    # :yul <dialect> { ... }
    if stripped.startswith(":yul"):
        body = stripped[4:].strip()
        # Remove optional dialect name (e.g. "berlin")
        brace = body.find("{")
        if brace >= 0:
            body = body[brace:]
        return _format_source_comment("Yul", body)

    # :abi func(args) vals
    if stripped.startswith(":abi"):
        body = stripped[4:].strip()
        return _format_source_comment("ABI", body)

    # :raw 0x...
    if stripped.startswith(":raw"):
        return "# Source: raw bytecode"

    # Plain hex: 0x...
    if stripped.startswith("0x"):
        return "# Source: raw bytecode"

    # LLL: starts with { ... }
    if stripped.startswith("{"):
        return _format_source_comment("LLL", stripped)

    # Inline assembly: (asm OP OP ...)
    if stripped.startswith("(asm"):
        return _format_source_comment("asm", stripped)

    return ""


def _format_source_comment(lang: str, body: str) -> str:
    """Format a source comment with language tag and body lines."""
    lines = body.splitlines()
    if len(lines) > _MAX_SOURCE_LINES:
        extra = len(lines) - _MAX_SOURCE_LINES
        lines = lines[:_MAX_SOURCE_LINES]
        lines.append(f"... ({extra} more lines)")
    comment_lines = [f"# Source: {lang}"]
    for line in lines:
        comment_lines.append(f"# {line}" if line.strip() else "#")
    return "\n".join(comment_lines)


COINBASE_ADDRESS = "0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba"

# Regex to strip YAML label syntax:
#   <contract:target:0xADDR> -> 0xADDR  (3-part)
#   <eoa:0xADDR> -> 0xADDR              (2-part)
_LABEL_RE = re.compile(r"<[^>]*?(0x[0-9a-fA-F]+)>")


def _strip_label(s: str) -> str:
    """Strip YAML label syntax, returning just the address."""
    m = _LABEL_RE.match(s.strip())
    if m:
        return m.group(1).lower()
    return s.strip().lower()


def _resolve_code_labels(code: str) -> str:
    """
    Resolve label syntax embedded in bytecode hex strings.

    Replace each ``<contract:0xADDR>``, ``<contract:target:0xADDR>``,
    or ``<eoa:0xADDR>`` with the raw hex address (no ``0x`` prefix,
    zero-padded to 40 chars).
    """

    def _replace(m: re.Match) -> str:
        addr = m.group(1).lower()
        raw = addr[2:] if addr.startswith("0x") else addr
        return raw.zfill(40)

    return _LABEL_RE.sub(_replace, code)


def _normalize_address(addr: str) -> str:
    """Normalize an address to lowercase with 0x prefix."""
    addr = _strip_label(addr)
    if not addr.startswith("0x"):
        addr = "0x" + addr
    return addr.lower()


def load_filler_expect_results(filler_path: Path) -> list[dict]:
    """
    Load expect entries from a filler file.

    Return list of dicts with keys:
        indexes: {"data": ..., "gas": ..., "value": ...}
        result: {address: {field: value, ...}, ...}
    """
    data = _load_filler_data(filler_path)
    if not data:
        return []
    try:
        for _test_name, test_data in data.items():
            if not isinstance(test_data, dict):
                continue
            expect = test_data.get("expect", [])
            if not isinstance(expect, list):
                continue

            entries = []
            for expect_entry in expect:
                if not isinstance(expect_entry, dict):
                    continue
                raw_indexes = expect_entry.get("indexes", {})
                raw_result = expect_entry.get("result", {})

                # Strip // prefixed keys (JSON comment hack)
                indexes = {
                    k: v
                    for k, v in raw_indexes.items()
                    if not str(k).startswith("//")
                }

                result: dict[str, dict] = {}
                for addr_key, fields in raw_result.items():
                    if str(addr_key).startswith("//"):
                        continue
                    if not isinstance(fields, dict):
                        continue
                    norm_addr = _normalize_address(str(addr_key))
                    # Strip // prefixed field keys
                    clean_fields = {
                        k: v
                        for k, v in fields.items()
                        if not str(k).startswith("//")
                    }
                    if clean_fields:
                        result[norm_addr] = clean_fields

                entry_dict: dict[str, Any] = {
                    "indexes": indexes,
                    "network": expect_entry.get("network", []),
                    "result": result,
                }
                exc = expect_entry.get("expectException")
                if exc:
                    entry_dict["expect_exception"] = exc
                entries.append(entry_dict)
            return entries
        return []
    except Exception:
        return []


def _resolve_filler_labels(
    filler_path: Path,
    expect_entries: list[dict],
) -> list[dict]:
    """
    Resolve ``:label`` selectors in expect entries to integer indices.

    Mirror the static-filler algorithm (``StateStaticTest.match_labels``):
    scan ``transaction.data`` for label matches and substitute the
    ``:label <name>`` string with a list of matching integer indices.
    """
    data = _load_filler_data(filler_path)
    if not data:
        return expect_entries

    # Build label → [indices] map from transaction.data
    label_map: dict[str, list[int]] = {}
    for _test_name, test_data in data.items():
        if not isinstance(test_data, dict):
            continue
        tx = test_data.get("transaction", {})
        if not isinstance(tx, dict):
            continue
        data_list = tx.get("data", [])
        if not isinstance(data_list, list):
            continue
        for idx, entry in enumerate(data_list):
            s = str(entry).strip()
            m = re.match(r"^:label\s+(\S+)", s)
            if m:
                label_map.setdefault(m.group(1), []).append(idx)
        break  # only first test in filler

    def _resolve_selector(sel: Any) -> Any:
        """Resolve a single index selector."""
        if isinstance(sel, str):
            s = sel.strip()
            if s.startswith(":label"):
                name = s.replace(":label ", "").strip()
                return label_map.get(name, [-2])  # -2 = never matches
            # Range like "0-2"
            range_m = re.match(r"^(\d+)-(\d+)$", s)
            if range_m:
                lo, hi = int(range_m.group(1)), int(range_m.group(2))
                return list(range(lo, hi + 1))
            try:
                return int(s)
            except ValueError:
                return sel
        if isinstance(sel, list):
            resolved: list[int] = []
            for item in sel:
                r = _resolve_selector(item)
                if isinstance(r, list):
                    resolved.extend(r)
                elif isinstance(r, int):
                    resolved.append(r)
            return list(set(resolved))
        return sel

    resolved_entries = []
    for entry in expect_entries:
        indexes = entry.get("indexes", {})
        new_indexes = {}
        for dim in ("data", "gas", "value"):
            sel = indexes.get(dim, -1)
            new_indexes[dim] = _resolve_selector(sel)
        resolved_entries.append({**entry, "indexes": new_indexes})
    return resolved_entries


def _build_filler_address_map(
    filler_data: dict | None,
) -> dict[str, str]:
    """
    Map filler original tag hex addresses to resolved addresses.

    Compute the resolved address directly from each account's model hash
    (``account.hash()`` + ``contract_address_from_hash``), avoiding the
    full ``PreInFiller.setup()`` which requires solc for Yul contracts.

    Return ``{original_hex_lower: resolved_hex_lower}`` or ``{}`` on
    failure.
    """
    if not filler_data:
        return {}
    try:
        from execution_testing.specs.static_state.account import PreInFiller
        from execution_testing.specs.static_state.common import (
            ContractTag,
            SenderTag,
        )
        from execution_testing.test_types.helpers import (
            contract_address_from_hash,
        )
    except Exception:
        return {}
    try:
        raw: dict | None = None
        for test_data in filler_data.values():
            if isinstance(test_data, dict) and "pre" in test_data:
                raw = test_data["pre"]
                break
        if raw is None:
            return {}
        pre_model = PreInFiller.model_validate(raw)
        addr_map: dict[str, str] = {}
        for key_obj, account in pre_model.root.items():
            if not hasattr(key_obj, "name"):
                continue
            if isinstance(key_obj, SenderTag):
                continue  # EOA addresses don't need remapping
            if not isinstance(key_obj, ContractTag):
                continue
            try:
                account_hash = account.hash()
                resolved_addr = contract_address_from_hash(account_hash, 0)
                resolved_hex = "0x" + bytes(resolved_addr).hex()
            except Exception:
                continue
            orig = _normalize_address(str(key_obj.original_string or ""))
            if orig and orig != resolved_hex and orig.startswith("0x"):
                addr_map[orig] = resolved_hex
        return addr_map
    except Exception:
        return {}


def _remap_expect_addresses(
    entries: list[dict],
    addr_map: dict[str, str],
) -> list[dict]:
    """
    Remap filler tag addresses in expect results to resolved addresses.

    Replace address keys and address-like values in storage using the
    mapping from ``_build_filler_address_map``.
    """
    if not addr_map:
        return entries

    def _remap_value(v: Any) -> Any:
        if not isinstance(v, str):
            return v
        s = v.strip()
        # Handle tag syntax: <contract:0xADDR>
        if s.startswith("<") and ":" in s:
            m = re.search(r"(0x[0-9a-fA-F]+)", s)
            if m:
                resolved = addr_map.get(m.group(1).lower())
                if resolved:
                    return resolved
        return addr_map.get(s.lower(), v)

    remapped = []
    for entry in entries:
        result = entry.get("result", {})
        new_result: dict[str, dict] = {}
        for addr, fields in result.items():
            new_addr = addr_map.get(addr.lower(), addr)
            new_fields: dict = {}
            for fk, fv in fields.items():
                if fk == "storage" and isinstance(fv, dict):
                    new_fields[fk] = {
                        _remap_value(k): _remap_value(v) for k, v in fv.items()
                    }
                else:
                    new_fields[fk] = _remap_value(fv)
            new_result[new_addr] = new_fields
        remapped.append({**entry, "result": new_result})
    return remapped


def load_filler_tx_arrays(
    filler_path: Path,
) -> dict[str, list] | None:
    """
    Load transaction data/gas/value arrays from a filler.

    Return dict with keys "data", "gas", "value", each a list of raw
    values.  Data entries are stripped of ``:label`` / ``:abi`` /
    ``:raw`` prefixes and converted to hex strings.  Returns None on
    failure.
    """
    data = _load_filler_data(filler_path)
    if not data:
        return None
    try:
        for _test_name, test_data in data.items():
            if not isinstance(test_data, dict):
                continue
            tx = test_data.get("transaction", {})
            if not isinstance(tx, dict):
                continue
            return {
                "data": tx.get("data", [""]),
                "gas": tx.get("gasLimit", [""]),
                "value": tx.get("value", [""]),
            }
        return None
    except Exception:
        return None


def _index_matches(selector: Any, case_idx: int) -> bool:
    """
    Check if an index selector matches a specific case index.

    Selector can be:
    - -1: matches any index
    - int: matches that exact index
    - list: matches if case_idx is in the list (items can be ints or ranges)
    - str range "0-2": matches 0, 1, 2
    - str label ":label ...": treated as matching the index position
    """
    if isinstance(selector, int):
        return selector == -1 or selector == case_idx
    if isinstance(selector, str):
        s = selector.strip()
        # Range like "0-2"
        range_match = re.match(r"^(\d+)-(\d+)$", s)
        if range_match:
            lo, hi = int(range_match.group(1)), int(range_match.group(2))
            return lo <= case_idx <= hi
        # Label syntax — can't resolve without the data array, treat as match
        if s.startswith(":label"):
            return True
        # Try as integer
        try:
            return int(s) == case_idx
        except ValueError:
            return True  # Unknown format, be permissive
    if isinstance(selector, list):
        return any(_index_matches(item, case_idx) for item in selector)
    return True  # Unknown type, be permissive


def extract_case_indices(fixture_key: str) -> tuple[int, int, int]:
    """
    Extract (data_idx, gas_idx, value_idx) from fixture key.

    Key formats:
        "tests/.../XFiller.json::TestName[d0g0v0-Cancun]"
        "[fork_Cancun-state_test-d0-g0-v0]"
        "[...-d1]" (g/v default to 0)
        "[...-v1]" (d/g default to 0)
        "[...-d1-v2]" (g default to 0)
    """
    # Old format: [d0g0v0-Cancun]
    m = re.search(r"\[d(\d+)g(\d+)v(\d+)-", fixture_key)
    if m:
        return int(m.group(1)), int(m.group(2)), int(m.group(3))
    # Extract d, g, v individually from dash-separated segments
    d, g, v = 0, 0, 0
    dm = re.search(r"-d(\d+)", fixture_key)
    if dm:
        d = int(dm.group(1))
    gm = re.search(r"-g(\d+)", fixture_key)
    if gm:
        g = int(gm.group(1))
    vm = re.search(r"-v(\d+)", fixture_key)
    if vm:
        v = int(vm.group(1))
    return d, g, v


# ---------------------------------------------------------------------------
# Code generation
# ---------------------------------------------------------------------------


def _find_top_level_eq(s: str) -> int:
    """Find the position of '=' that is not inside parens/brackets."""
    depth = 0
    for i, ch in enumerate(s):
        if ch in ("(", "["):
            depth += 1
        elif ch in (")", "]"):
            depth -= 1
        elif ch == "=" and depth == 0:
            return i
    return -1


def _wrap_long_op_call(op_call: str, indent: str) -> str:
    """
    Wrap a single long Op call across keyword arguments.

    E.g. Op.CALL(gas=X, address=Y, ...) becomes:
        Op.CALL(
            gas=X,
            address=Y,
            ...
        )
    Recursively wraps nested calls that are also too long.
    """
    # Find the opening paren
    if "(" not in op_call:
        return op_call
    paren_pos = op_call.index("(")
    func_name = op_call[: paren_pos + 1]
    args_str = op_call[paren_pos + 1 : -1]  # strip outer parens

    # Split by ", " but respect nested parens
    args: list[str] = []
    depth = 0
    current = ""
    for ch in args_str:
        if ch in ("(", "["):
            depth += 1
        elif ch in (")", "]"):
            depth -= 1
        if ch == "," and depth == 0:
            args.append(current.strip())
            current = ""
        else:
            current += ch
    if current.strip():
        args.append(current.strip())

    arg_indent = indent + "    "
    arg_lines: list[str] = []
    for a in args:
        line = f"{arg_indent}{a},"
        if len(line) > 79 and "(" in a:
            # Find top-level '=' (not inside parens)
            eq_pos = _find_top_level_eq(a)
            if eq_pos > 0:
                key = a[: eq_pos + 1]
                val = a[eq_pos + 1 :]
                wrapped_val = _wrap_long_op_call(val, arg_indent)
                arg_lines.append(f"{arg_indent}{key}{wrapped_val},")
            else:
                arg_lines.append(
                    f"{arg_indent}{_wrap_long_op_call(a, arg_indent)},"
                )
        else:
            arg_lines.append(line)
    return func_name + "\n" + "\n".join(arg_lines) + "\n" + indent + ")"


def _wrap_op_chain(
    op_str: str,
    indent: str = "        ",
    prefix: str = "code=",
) -> str:
    """
    Wrap a long Op chain string to fit within 79 chars.

    Return the original string if it fits, otherwise wrap with
    line continuations.
    """
    # Use 78 to leave room for trailing comma
    if len(indent + prefix + op_str) <= 78:
        return op_str
    parts = op_str.split(" + ")

    # Wrap individual Op calls that are too long on their own
    max_part_len = 79 - len(indent + "+ ")
    wrapped_parts = []
    for part in parts:
        if len(part) > max_part_len and "(" in part:
            wrapped_parts.append(_wrap_long_op_call(part, indent))
        else:
            wrapped_parts.append(part)

    lines: list[str] = []
    current = wrapped_parts[0]
    line_indent = indent + "+ "
    for part in wrapped_parts[1:]:
        has_newline = "\n" in current or "\n" in part
        candidate = current + " + " + part
        # First line has prefix, subsequent have "+ "
        # Use 78 to leave room for trailing comma
        if lines:
            limit = 78 - len(line_indent)
        else:
            limit = 78 - len(indent + prefix)
        if has_newline or len(candidate) > limit:
            lines.append(current)
            current = part
        else:
            current = candidate
    lines.append(current)
    joined = ("\n" + line_indent).join(lines)
    close_indent = indent[4:] if len(indent) >= 4 else ""
    return f"(\n{indent}{joined}\n{close_indent})"


def generate_code_expr(
    hex_code: str,
    indent: str = "        ",
    source_comment: str = "",
) -> tuple[str, str]:
    """
    Generate Python code expression for bytecode.

    Returns (code_expr, pre_comment) where:
    - code_expr is the Python expression (Op chain or bytes.fromhex fallback)
    - pre_comment is the source language comment (if provided)
    """
    if hex_code in ("0x", ""):
        return 'b""', ""

    raw = hex_code[2:] if hex_code.startswith("0x") else hex_code

    # Indent source comment lines to match the surrounding code
    comment = ""
    if source_comment:
        comment_indent = indent[4:] if len(indent) >= 4 else ""
        comment = "\n".join(
            f"{comment_indent}{line}" for line in source_comment.splitlines()
        )

    # Always use Op format — readable and round-trips to identical bytecode
    op_str = bytecode_to_op_string(hex_code)
    if op_str is not None:
        wrapped = _wrap_op_chain(op_str, indent=indent, prefix="code=")
        return wrapped, comment

    # bytes.fromhex fallback only if Op conversion fails entirely
    if len(raw) > 72:
        chunks = [raw[i : i + 72] for i in range(0, len(raw), 72)]
        if len(chunks) == 1:
            expr = f'bytes.fromhex(\n{indent}"{chunks[0]}"\n{indent[4:]})'
            return expr, comment
        hex_lines = f'"\n{indent}"'.join(chunks)
        expr = f'bytes.fromhex(\n{indent}"{hex_lines}"\n{indent[4:]})'
        return expr, comment

    return f'bytes.fromhex("{raw}")', comment


def generate_account_setup(
    address: str,
    account: dict[str, Any],
    var_name: str,
    indent: str = "    ",
    source_comment: str = "",
    is_sender: bool = False,
    var_is_used: bool = True,
    already_defined: bool = False,
) -> str:
    """
    Generate pre-state account setup code.

    For EOAs and the sender, emit pre[var] = Account(...).
    For contracts, emit var = pre.deploy_contract(...).
    For oversized contracts (>24576 bytes), keep pre[var] = Account(...).

    When already_defined is True, the variable (e.g. coinbase, sender) was
    already emitted earlier, so deploy_contract is called without assignment
    and uses address=var_name instead of a literal Address.
    """
    lines = []
    code_hex = account.get("code", "0x")
    balance = hex_to_int(account.get("balance", "0x00"))
    nonce = hex_to_int(account.get("nonce", "0x00"))
    storage = account.get("storage", {})

    # Determine if this is an EOA (no code) or contract
    is_eoa = code_hex in ("0x", "")

    # Check if contract code is oversized (>24576 bytes = >49152 hex chars)
    raw_hex = code_hex[2:] if code_hex.startswith("0x") else code_hex
    is_oversized = len(raw_hex) > 49152

    # Use deploy_contract for non-oversized contracts
    use_deploy = not is_eoa and not is_oversized

    if use_deploy:
        # Build deploy_contract call
        code_expr, code_comment = generate_code_expr(
            code_hex,
            indent=indent + "    ",
            source_comment=source_comment,
        )
        if code_comment:
            lines.append(code_comment.rstrip())

        deploy_parts = []
        deploy_parts.append(f"code={code_expr}")
        if storage:
            deploy_parts.append(f"storage={format_storage(storage)}")
        # balance: omit if 0 (deploy_contract default)
        if balance != 0:
            deploy_parts.append(f"balance={format_balance(balance)}")
        # nonce: omit if 1 (deploy_contract default), emit otherwise
        if nonce != 1:
            deploy_parts.append(f"nonce={nonce}")
        if already_defined:
            addr_part = f"address={var_name}"
        else:
            padded = _pad_address(address)
            addr_part = f'address=Address("{padded}")'

        # Always use multi-line for deploy_contract (address line needs
        # noqa: E501 and the call is almost always long).
        deploy_parts.append(addr_part)
        if var_is_used and not already_defined:
            lines.append(f"{indent}{var_name} = pre.deploy_contract(")
        else:
            lines.append(f"{indent}pre.deploy_contract(")
        for i, part in enumerate(deploy_parts):
            if i == len(deploy_parts) - 1 and part == addr_part:
                # Last part is address — add noqa: E501
                lines.append(f"{indent}    {part},  # noqa: E501")
            else:
                lines.append(f"{indent}    {part},")
        lines.append(f"{indent})")
    else:
        # Standard pre[var] = Account(...) form
        parts = []
        parts.append(f"balance={format_balance(balance)}")
        # Omit nonce=0 for sender (it's the default)
        if is_sender:
            if nonce != 0:
                parts.append(f"nonce={nonce}")
        else:
            parts.append(f"nonce={nonce}")

        if not is_eoa:
            code_expr, code_comment = generate_code_expr(
                code_hex, indent=indent + "    "
            )
            if code_comment:
                lines.append(code_comment.rstrip())
            parts.append(f"code={code_expr}")

        if storage:
            parts.append(f"storage={format_storage(storage)}")

        # Format as single line or multi-line
        single = f"{indent}pre[{var_name}] = Account({', '.join(parts)})"
        if len(single) <= 79 and "\n" not in "".join(parts):
            lines.append(single)
        else:
            lines.append(f"{indent}pre[{var_name}] = Account(")
            for part in parts:
                lines.append(f"{indent}    {part},")
            lines.append(f"{indent})")

    return "\n".join(lines)


def _parse_result_int(v: Any) -> int:
    """Parse an int from a filler result value (may be str, int, hex)."""
    if isinstance(v, int):
        return v
    s = str(v).strip()
    if not s or s in ("0x", "0X"):
        return 0
    # YAML label syntax: <contract:name:0xADDR> or <contract:name>
    if s.startswith("<") and ":" in s:
        m = re.search(r"(0x[0-9a-fA-F]+)", s)
        if m:
            return int(m.group(1), 16)
        return 0
    if s.startswith("0x") or s.startswith("0X"):
        return int(s, 16)
    try:
        return int(s)
    except ValueError:
        pass
    # Try as bare hex (e.g. "60A7" without 0x prefix)
    try:
        return int(s, 16)
    except ValueError:
        return 0


def _format_storage_from_result(
    storage: dict,
    indent: str = "                ",
) -> str:
    """Format storage dict from filler result."""
    if not storage:
        return "{}"
    # Deduplicate by int key (last value wins for duplicate keys)
    deduped: dict[int, int] = {}
    for k, v in storage.items():
        # Skip JSON comment keys (e.g. "//comment")
        if str(k).startswith("//"):
            continue
        deduped[_parse_result_int(k)] = _parse_result_int(v)
    items = []
    for key_int, val_int in sorted(deduped.items()):
        item = f"{format_int(key_int)}: {format_int(val_int)}"
        items.append(item)
    single = "{" + ", ".join(items) + "}"
    if len(single) <= 50:
        return single
    formatted: list[str] = []
    for item in items:
        formatted.append(item + ",")
    inner = ("\n" + indent).join(formatted)
    close = indent[4:] if len(indent) >= 4 else ""
    return "{\n" + indent + inner + "\n" + close + "}"


def _truncate_at_word(text: str, max_len: int) -> str:
    """Truncate text at a word boundary, appending '...'."""
    if len(text) <= max_len:
        return text
    # Find last space before the limit (leaving room for "...")
    cut = text.rfind(" ", 0, max_len - 3)
    if cut <= 0:
        # No space found; hard-cut
        return text[: max_len - 3] + "..."
    return text[:cut] + "..."


def _pad_address(addr: str) -> str:
    """Pad a short hex address to 40 hex chars (20 bytes)."""
    raw = addr[2:] if addr.startswith("0x") else addr
    if len(raw) < 40:
        raw = raw.zfill(40)
    return "0x" + raw


def generate_post_value_string(result: dict | None) -> str:
    """
    Generate a post dict expression for use in parametrize values.

    Use Address("0x...") literals (not variable names) since parametrize
    evaluates at module import time.  Return "{}" for None/empty results.
    """
    if not result:
        return "{}"
    parts: list[str] = []
    for addr, fields in sorted(result.items()):
        if addr.lower() == COINBASE_ADDRESS:
            continue

        # Skip unresolved Yul/label addresses
        if "<" in addr:
            continue

        padded = _pad_address(addr)

        if "shouldnotexist" in fields:
            parts.append(f'Address("{padded}"): Account.NONEXISTENT')
            continue

        acct_parts: list[str] = []
        if "storage" in fields:
            acct_parts.append(
                f"storage={_format_storage_from_result(fields['storage'])}"
            )
        if "nonce" in fields:
            acct_parts.append(f"nonce={_parse_result_int(fields['nonce'])}")
        if "balance" in fields:
            val = _parse_result_int(fields["balance"])
            acct_parts.append(f"balance={format_balance(val)}")
        if "code" in fields:
            code_val = fields["code"]
            if isinstance(code_val, int):
                raw = hex(code_val)[2:]
                if len(raw) % 2:
                    raw = "0" + raw
                acct_parts.append(f'code=bytes.fromhex("{raw}")')
            elif isinstance(code_val, str) and "<" in code_val:
                resolved = _resolve_code_labels(code_val)
                raw = resolved[2:] if resolved.startswith("0x") else resolved
                acct_parts.append(f'code=bytes.fromhex("{raw}")')
            elif code_val in ("", "0x"):
                acct_parts.append('code=b""')
            else:
                raw = code_val[2:] if code_val.startswith("0x") else code_val
                acct_parts.append(f'code=bytes.fromhex("{raw}")')

        if acct_parts:
            acct_str = ", ".join(acct_parts)
            parts.append(f'Address("{padded}"): Account({acct_str})')

    if not parts:
        return "{}"
    if len(parts) == 1:
        return "{" + parts[0] + "}"
    inner = ", ".join(parts)
    return "{" + inner + "}"


def _generate_post_from_fixture_state(
    post_state: dict[str, dict],
    addr_vars: dict[str, str],
) -> str:
    """
    Generate the post = {...} dict from compiled fixture post state.

    The fixture post state format is:
        {address: {balance: "0x...", nonce: "0x...", code: "0x...",
                   storage: {key: value}}}

    Only assert on storage and code (not balance/nonce) since those
    depend on gas costs which vary across forks.
    Skip coinbase and accounts with no interesting assertions.
    """
    lines = ["    post = {"]
    has_entries = False
    for addr, fields in sorted(post_state.items()):
        addr_l = addr.lower()
        # Skip coinbase
        if addr_l == COINBASE_ADDRESS:
            continue
        padded = _pad_address(addr_l)
        var = addr_vars.get(addr_l, f'Address("{padded}")')

        parts = []
        if "storage" in fields and fields["storage"]:
            parts.append(
                f"storage={_format_storage_from_result(fields['storage'])}"
            )

        if parts:
            parts_str = ", ".join(parts)
            single = f"        {var}: Account({parts_str}),"
            if len(single) <= 79 and "\n" not in parts_str:
                lines.append(single)
            else:
                lines.append(f"        {var}: Account(")
                for j, p in enumerate(parts):
                    comma = "," if j < len(parts) - 1 else ","
                    lines.append(f"            {p}{comma}")
                lines.append("        ),")
            has_entries = True

    lines.append("    }")
    if not has_entries:
        return "    post: dict = {}"
    return "\n".join(lines)


def _generate_expect_entries_source(
    entries: list[dict],
    addr_vars: dict[str, str] | None = None,
    indent: str = "",
) -> str:
    """
    Generate ``expect_entries_ = [...]`` Python source from expect entries.

    When *addr_vars* is provided, addresses in result dicts are replaced
    with variable names (for use inside function bodies where variables
    like ``callee``, ``contract`` etc. are defined).
    """
    lines = [f"{indent}expect_entries_: list[dict] = ["]
    for entry in entries:
        indexes = entry.get("indexes", {})
        network = entry.get("network", [])
        result = entry.get("result", {})
        if addr_vars:
            result_str = _generate_post_with_vars(result, addr_vars)
        else:
            result_str = generate_post_value_string(result)
        idx_d = indexes.get("data", -1)
        idx_g = indexes.get("gas", -1)
        idx_v = indexes.get("value", -1)
        net_str = json.dumps(network)
        lines.append(f"{indent}    {{")
        lines.append(
            f'{indent}        "indexes": {{"data": {idx_d}, "gas": {idx_g},'
            f' "value": {idx_v}}},'
        )
        lines.append(f'{indent}        "network": {net_str},')
        lines.append(f'{indent}        "result": {result_str},')
        exc = entry.get("expect_exception")
        if exc:
            lines.append(
                f'{indent}        "expect_exception": {json.dumps(exc)},'
            )
        lines.append(f"{indent}    }},")
    lines.append(f"{indent}]")
    return "\n".join(lines)


def _generate_post_with_vars(
    result: dict[str, dict],
    addr_vars: dict[str, str],
) -> str:
    """Generate a post dict expression using variable names for addresses."""
    if not result:
        return "{}"
    parts: list[str] = []
    for addr, fields in sorted(result.items()):
        if addr.lower() == COINBASE_ADDRESS:
            continue
        if "<" in addr:
            continue
        padded = _pad_address(addr)
        var = addr_vars.get(addr.lower(), f'Address("{padded}")')

        if "shouldnotexist" in fields:
            parts.append(f"{var}: Account.NONEXISTENT")
            continue

        acct_parts: list[str] = []
        if "storage" in fields:
            acct_parts.append(
                f"storage={_format_storage_from_result(fields['storage'])}"
            )
        if "nonce" in fields:
            acct_parts.append(f"nonce={_parse_result_int(fields['nonce'])}")
        if "balance" in fields:
            val = _parse_result_int(fields["balance"])
            acct_parts.append(f"balance={format_balance(val)}")
        if "code" in fields:
            code_val = fields["code"]
            if isinstance(code_val, int):
                raw = hex(code_val)[2:]
                if len(raw) % 2:
                    raw = "0" + raw
                acct_parts.append(f'code=bytes.fromhex("{raw}")')
            elif isinstance(code_val, str) and "<" in code_val:
                resolved = _resolve_code_labels(code_val)
                raw = resolved[2:] if resolved.startswith("0x") else resolved
                acct_parts.append(f'code=bytes.fromhex("{raw}")')
            elif code_val in ("", "0x"):
                acct_parts.append('code=b""')
            else:
                raw = code_val[2:] if code_val.startswith("0x") else code_val
                acct_parts.append(f'code=bytes.fromhex("{raw}")')
        if acct_parts:
            acct_str = ", ".join(acct_parts)
            parts.append(f"{var}: Account({acct_str})")

    if not parts:
        return "{}"
    if len(parts) == 1:
        return "{" + parts[0] + "}"
    inner = ", ".join(parts)
    return "{" + inner + "}"


def generate_test_file(
    fixture_data: dict[str, Any],
    filler_path: str,
    filler_comment: str,
    valid_until: str | None = None,
    valid_from_override: str | None = None,
    filler_full_path: Path | None = None,  # noqa: ARG001
    code_sources: _FillerCodeSources | None = None,
    slow: bool = False,
    expect_entries: list[dict] | None = None,
    filler_tx_arrays: dict[str, list] | None = None,
) -> str:
    """
    Generate a complete Python test file from fixture data.

    Parameters
    ----------
    fixture_data
        Parsed JSON fixture mapping test keys to test data.
    filler_path
        Relative path for the filler comment in the generated file.
    filler_comment
        Comment string identifying the source filler.
    valid_until
        Last fork name for which this test is valid (None = no bound).
    valid_from_override
        Override the detected valid_from fork name.
    filler_full_path
        Absolute path to the filler file (unused).
    code_sources
        Pre-resolved code source mappings for bytecode generation.
    slow
        Whether to mark the generated test with @pytest.mark.slow.
    expect_entries
        Parsed filler expect entries for Path A post generation.
    filler_tx_arrays
        Transaction data/gas/value arrays from the filler, used for
        TX_DATA/TX_GAS/TX_VALUE constants.

    """
    # Compiled fixtures have one top-level key per (case × fork).
    # Collect all forks, find the earliest, then collect cases for that fork.
    all_keys = list(fixture_data.keys())
    first_test = fixture_data[all_keys[0]]

    env = first_test["env"]

    # Merge pre from ALL cases — different cases may deploy different
    # contracts (e.g. test_push has 32 cases each with a unique contract).
    pre: dict[str, Any] = {}
    for key in all_keys:
        for addr, acct in fixture_data[key]["pre"].items():
            if addr.lower() not in {a.lower() for a in pre}:
                pre[addr] = acct

    # Detect all forks present across all entries
    all_forks: set[str] = set()
    for key in all_keys:
        test = fixture_data[key]
        all_forks.update(test["post"].keys())
    # Use filler network lower bound if available, else earliest from
    # fixture post keys
    fork_name = valid_from_override or earliest_fork(all_forks)

    post_fork = fork_name

    # Collect all cases for this fork.
    # Determine (d, g, v) indices: try extract_case_indices first, then
    # fall back to matching compiled calldata against filler tx arrays.
    cases_for_fork: list[dict[str, Any]] = []

    # First pass: collect entries and try extract_case_indices
    raw_cases: list[tuple[str, dict]] = []
    for key in all_keys:
        test = fixture_data[key]
        if post_fork in test["post"]:
            raw_cases.append((key, test))

    # Check if extract_case_indices gives unique d values
    extracted = [extract_case_indices(k) for k, _ in raw_cases]
    d_values = [e[0] for e in extracted]
    all_d_zero = len(raw_cases) > 1 and all(d == 0 for d in d_values)

    if all_d_zero and filler_tx_arrays:
        # extract_case_indices failed (label-based keys).
        # Match fixture key labels against filler label map.
        label_to_d: dict[str, list[int]] = {}
        for d_idx, filler_entry in enumerate(filler_tx_arrays.get("data", [])):
            m = re.match(r"^:label\s+(\S+)", str(filler_entry).strip())
            if m:
                label_to_d.setdefault(m.group(1), []).append(d_idx)

        def _resolve_label_d(label: str) -> int | None:
            """Match a fixture key label against the filler label map."""
            # Strip -dN/-gN/-vN suffixes (already parsed by
            # extract_case_indices) before label matching.
            cleaned = re.sub(r"(?:-[dgv]\d+)+$", "", label)

            # Exact match: unique label → first (only) d-index
            if cleaned in label_to_d:
                return label_to_d[cleaned][0]
            # Pytest deduplication: "fail-N" means the Nth entry with
            # label "fail". Bare "fail" = 1st, "fail-2" = 2nd, etc.
            m_suffix = re.match(r"(.+)-(\d+)$", cleaned)
            if m_suffix:
                prefix = m_suffix.group(1)
                nth = int(m_suffix.group(2))
                if prefix in label_to_d:
                    d_list = label_to_d[prefix]
                    # "fail-2" = 2nd entry (0-based index 1)
                    pos = nth - 1
                    if 0 <= pos < len(d_list):
                        return d_list[pos]
            return None

        for i, (key, _test) in enumerate(raw_cases):
            # Extract label from fixture key: "[...-<label>]"
            lm = re.search(r"state_test-(.+?)\]", key)
            if not lm:
                # Try other formats: [fork_X-blockchain_test...-<label>]
                lm = re.search(r"-([^-\[\]]+)\]$", key)
            d_resolved = _resolve_label_d(lm.group(1)) if lm else None
            if d_resolved is not None:
                d = d_resolved
            else:
                # Fall back to position-based assignment
                d = i
            _, g, v = extracted[i]
            extracted[i] = (d, g, v)

    for i, (_key, test) in enumerate(raw_cases):
        tx = test["transaction"]
        post_entry = test["post"][post_fork][0]
        post_state = post_entry.get("state", {})
        expect_exception = post_entry.get("expectException")
        access_lists = tx.get("accessLists", [])
        al = access_lists[0] if access_lists else None
        case_to = (tx.get("to") or "").lower()
        d, g, v = extracted[i]

        cases_for_fork.append(
            {
                "d": d,
                "g": g,
                "v": v,
                "data": tx["data"][0] if tx["data"] else "0x",
                "gas_limit": hex_to_int(tx["gasLimit"][0])
                if tx["gasLimit"]
                else 100000,
                "value": hex_to_int(tx["value"][0]) if tx["value"] else 0,
                "access_list": al,
                "expect_exception": expect_exception,
                "post_state": post_state,
                "to": case_to,
            }
        )

    # Extract TX arrays — prefer filler (has all entries) over compiled
    # fixture (may only have the first entry per dimension).
    def _safe_int(v: Any) -> int:
        """Convert a filler value to int, handling various formats."""
        if isinstance(v, int):
            return v
        s = str(v).strip()
        if s.startswith("0x") or s.startswith("0X"):
            return int(s, 16)
        try:
            return int(s)
        except ValueError:
            return 0

    # Build TX arrays from compiled fixture data using the resolved
    # d-indices from cases_for_fork (which handle label-based keys).
    first_tx_c = first_test["transaction"]
    tx_data_map: dict[int, str] = {}
    for case in cases_for_fork:
        d_idx = case["d"]
        if d_idx not in tx_data_map:
            data_hex = case["data"]
            tx_data_map[d_idx] = data_hex
    max_d = max(tx_data_map.keys()) if tx_data_map else 0
    tx_data_arr = [tx_data_map.get(i, "0x") for i in range(max_d + 1)]

    if filler_tx_arrays:
        tx_gas_arr = [
            _safe_int(g_val)
            for g_val in filler_tx_arrays.get("gas", ["0x5f5e100"])
        ]
        tx_value_arr = [
            _safe_int(v_val)
            for v_val in filler_tx_arrays.get("value", ["0x0"])
        ]
    else:
        tx_gas_arr = [
            hex_to_int(g_val)
            for g_val in first_tx_c.get("gasLimit", ["0x5f5e100"])
        ]
        tx_value_arr = [
            hex_to_int(v_val) for v_val in first_tx_c.get("value", ["0x0"])
        ]

    is_multi = len(cases_for_fork) > 1

    # Use first case's tx for shared fields (secret_key, to, gas_price, nonce)
    tx = first_test["transaction"]

    # Determine test name
    filler_stem = Path(filler_path).stem  # e.g. "callcode_checkPCFiller"
    test_func_name = filler_name_to_test_name(filler_stem)

    # Identify accounts
    sender_addr = tx.get("sender", "").lower()
    to_addr = (tx.get("to") or "").lower()
    coinbase_addr = env.get("currentCoinbase", "").lower()

    # Build address variable mapping
    addr_vars: dict[str, str] = {}
    var_names: list[tuple[str, str, str]] = []  # (addr, var_name, display)

    # Always add coinbase
    if coinbase_addr:
        addr_vars[coinbase_addr] = "coinbase"
        var_names.append((coinbase_addr, "coinbase", coinbase_addr))

    # Add sender
    if sender_addr:
        addr_vars[sender_addr] = "sender"
        var_names.append((sender_addr, "sender", sender_addr))

    # Reserve "contract" for the to_addr first
    if to_addr and to_addr not in addr_vars:
        addr_vars[to_addr] = "contract"
        var_names.append((to_addr, "contract", to_addr))

    # Add other accounts with unique names
    contract_idx = 0
    for addr in sorted(pre.keys()):
        addr_l = addr.lower()
        if addr_l in addr_vars:
            continue
        if contract_idx == 0 and "contract" not in addr_vars.values():
            name = "contract"
        else:
            name = f"callee_{contract_idx}" if contract_idx > 0 else "callee"
        addr_vars[addr_l] = name
        var_names.append((addr_l, name, addr_l))
        contract_idx += 1

    # Module docstring
    doc_lines = []
    if filler_comment:
        comment_lines = [line.rstrip() for line in filler_comment.splitlines()]
        # Find first non-empty line for the summary
        summary = ""
        rest_start = 0
        for i, line in enumerate(comment_lines):
            if line.strip():
                summary = line.strip()
                rest_start = i + 1
                break
        if not summary:
            summary = "Test ported from static filler"
        # D404: first word should not be "This"
        if summary.startswith("This "):
            summary = summary[5:]
            summary = summary[0].upper() + summary[1:]
        # D400/D415: ensure ends with punctuation
        if summary and summary[-1] not in ".?!":
            summary += "."
        # Truncate/wrap summary to 79 chars
        if len(summary) > 79:
            summary = _truncate_at_word(summary, 79)
        doc_lines.append(summary)
        # Add remaining lines with blank separator
        remaining = comment_lines[rest_start:]
        if remaining and any(x.strip() for x in remaining):
            doc_lines.append("")
            for line in remaining:
                if len(line) <= 79:
                    doc_lines.append(line)
                elif line.startswith("http"):
                    # Don't wrap URLs — add noqa
                    doc_lines.append(line)
                else:
                    doc_lines.extend(textwrap.wrap(line, width=79))
        doc_lines.append("")
    else:
        doc_lines.append("Test ported from static filler.")
        doc_lines.append("")
    doc_lines.append("Ported from:")
    if len(filler_path) > 79:
        # Break path at directory separator
        parts = filler_path.split("/")
        current = parts[0]
        for p in parts[1:]:
            candidate = current + "/" + p
            if len(candidate) > 79:
                doc_lines.append(current)
                current = p
            else:
                current = candidate
        doc_lines.append(current)
    else:
        doc_lines.append(filler_path)

    # Add assembly summaries for contracts
    for addr in sorted(pre.keys()):
        addr_l = addr.lower()
        code_hex = pre[addr].get("code", "0x")
        if code_hex in ("0x", ""):
            continue
        var = addr_vars.get(addr_l, addr)
        asm = bytecode_to_assembly_summary(code_hex)
        if asm:
            doc_lines.append("")
            doc_lines.append(f"{var} code:")
            for line in asm.split("\n"):
                doc_lines.append(f"    {line}")

    # Escape content that would break triple-quoted docstrings
    safe_lines = [
        line.replace("\\", "\\\\").replace('"""', '""\\"')
        for line in doc_lines
    ]
    module_doc = '"""\n' + "\n".join(safe_lines) + '\n"""'

    # Check if we need Op import
    needs_op = False
    for addr in pre:
        code_hex = pre[addr].get("code", "0x")
        if (
            code_hex not in ("0x", "")
            and bytecode_to_op_string(code_hex) is not None
        ):
            needs_op = True
            break

    # Check if we need AccessList import (non-empty lists only)
    needs_access_list = any(c["access_list"] for c in cases_for_fork)
    # Check if we need TransactionException import
    needs_tx_exception = any(c.get("expect_exception") for c in cases_for_fork)

    # Check if Hash is needed (e.g. in access_list entries or blob hashes)
    needs_hash = False
    blob_hashes = tx.get("blobVersionedHashes")
    if blob_hashes:
        needs_hash = True
    if not needs_hash and is_multi:
        # Check if any access list entries use Hash
        for c in cases_for_fork:
            al = c.get("access_list")
            if al:
                for entry in al:
                    if entry.get("storageKeys"):
                        needs_hash = True
                        break
            if needs_hash:
                break
    if not needs_hash and not is_multi:
        al = cases_for_fork[0].get("access_list")
        if al:
            for entry in al:
                if entry.get("storageKeys"):
                    needs_hash = True
                    break

    # Build imports
    imports = [
        "import pytest",
        "from execution_testing import (",
    ]
    if needs_access_list:
        imports.append("    AccessList,")
    imports.extend(
        [
            "    Account,",
            "    Address,",
            "    Alloc,",
            "    EOA,",
            "    Environment,",
        ]
    )
    if needs_hash:
        imports.append("    Hash,")
    imports.extend(
        [
            "    StateTestFiller,",
            "    Transaction,",
        ]
    )
    if needs_tx_exception:
        imports.append("    TransactionException,")
    imports.append(")")
    # Fork import for tests that use resolve_expect_post
    if is_multi or expect_entries:
        imports.append("from execution_testing.forks import Fork")
        imports.append(
            "from execution_testing.specs.static_state.expect_section import ("
        )
        imports.append("    resolve_expect_post,")
        imports.append(")")
    if needs_op:
        imports.append("from execution_testing.vm import Op")

    # Build env
    env_parts = []
    env_parts.append("fee_recipient=coinbase")

    num = hex_to_int(env.get("currentNumber", "0x01"))
    env_parts.append(f"number={num}")

    ts = hex_to_int(env.get("currentTimestamp", "0x03e8"))
    env_parts.append(f"timestamp={ts}")

    diff = hex_to_int(env.get("currentDifficulty", "0x00"))
    if diff > 0:
        env_parts.append(f"difficulty={hex(diff)}")

    randao = hex_to_int(env.get("currentRandom", "0x00"))
    if randao > 0:
        env_parts.append(f"prev_randao={hex(randao)}")

    base_fee = hex_to_int(env.get("currentBaseFee", "0x0a"))
    if base_fee > 0:
        env_parts.append(f"base_fee_per_gas={base_fee}")

    excess_blob = hex_to_int(env.get("currentExcessBlobGas", "0x00"))
    if excess_blob > 0:
        env_parts.append(f"excess_blob_gas={excess_blob}")

    # Include gas_limit from original fixture for hasher match.
    # Amsterdam update: remove this to get framework default 100M.
    block_gas_limit = hex_to_int(env.get("currentGasLimit", "0x05f5e100"))
    env_parts.append(f"gas_limit={block_gas_limit}")

    # Detect which tx params vary across cases
    to_varies = False
    al_varies = False
    exc_varies = False
    if is_multi:
        all_to = [c["to"] for c in cases_for_fork]
        all_al = [
            json.dumps(c["access_list"], sort_keys=True)
            for c in cases_for_fork
        ]
        all_exc = [c.get("expect_exception") or "" for c in cases_for_fork]
        to_varies = len(set(all_to)) > 1
        al_varies = len(set(all_al)) > 1
        exc_varies = len(set(all_exc)) > 1

    # Extract secret key for EOA
    secret_key_hex = tx["secretKey"]
    if secret_key_hex.startswith("0x"):
        secret_key_hex = secret_key_hex[2:]

    # Build tx
    tx_parts = []
    tx_parts.append("sender=sender")

    if is_multi and to_varies:
        tx_parts.append("to=tx_to")
    elif to_addr:
        q = chr(34)
        fallback = f"Address({q}{to_addr}{q})"
        tx_parts.append(f"to={addr_vars.get(to_addr, fallback)}")
    else:
        tx_parts.append("to=None")

    # TX data/gas/value always reference the module-level arrays via d, g, v
    if is_multi:
        tx_parts.append("data=_tx_data(d)")
        tx_parts.append("gas_limit=TX_GAS[g]")
    else:
        # Single case — inline data for readability
        case = cases_for_fork[0]
        data_hex = case["data"]
        data_raw = data_hex[2:] if data_hex.startswith("0x") else data_hex
        if data_raw:
            if len(data_raw) > 72:
                chunks = [
                    data_raw[i : i + 72] for i in range(0, len(data_raw), 72)
                ]
                hex_joined = '"\n            "'.join(chunks)
                fromhex = (
                    f"data=bytes.fromhex(\n"
                    f'            "{hex_joined}"\n'
                    f"        )"
                )
                tx_parts.append(fromhex)
            else:
                tx_parts.append(f'data=bytes.fromhex("{data_raw}")')
        if case["gas_limit"] != 21000:
            tx_parts.append(f"gas_limit={case['gas_limit']}")

    gas_price = tx.get("gasPrice")
    max_fee = tx.get("maxFeePerGas")
    max_priority = tx.get("maxPriorityFeePerGas")
    max_fee_blob = tx.get("maxFeePerBlobGas")
    blob_hashes = tx.get("blobVersionedHashes")

    if max_fee:
        tx_parts.append(f"max_fee_per_gas={hex_to_int(max_fee)}")
        if max_priority and hex_to_int(max_priority) != 0:
            tx_parts.append(
                f"max_priority_fee_per_gas={hex_to_int(max_priority)}"
            )
    elif gas_price and hex_to_int(gas_price) != 10:
        tx_parts.append(f"gas_price={hex_to_int(gas_price)}")

    if max_fee_blob:
        tx_parts.append(f"max_fee_per_blob_gas={hex_to_int(max_fee_blob)}")
    if blob_hashes is not None:
        if blob_hashes:
            hash_items = [f'Hash("{h}")' for h in blob_hashes]
            single = "blob_versioned_hashes=[" + ", ".join(hash_items) + "]"
            if len("        " + single + ",") <= 79:
                tx_parts.append(single)
            else:
                inner = ",\n                ".join(hash_items)
                tx_parts.append(
                    "blob_versioned_hashes=[\n"
                    "                " + inner + ",\n"
                    "            ]"
                )
        else:
            tx_parts.append("blob_versioned_hashes=[]")

    tx_nonce = hex_to_int(tx.get("nonce", "0x00"))
    if tx_nonce != 0:
        tx_parts.append(f"nonce={tx_nonce}")

    if is_multi:
        tx_parts.append("value=TX_VALUE[v]")
    else:
        if cases_for_fork[0]["value"] != 0:
            tx_parts.append(f"value={cases_for_fork[0]['value']}")

    # Access list handling
    if is_multi:
        if al_varies:
            tx_parts.append("access_list=tx_access_list")
        else:
            al = cases_for_fork[0]["access_list"]
            if al:
                tx_parts.append(f"access_list={_format_access_list(al)}")
    else:
        al = cases_for_fork[0]["access_list"]
        if al:
            tx_parts.append(f"access_list={_format_access_list(al)}")

    # Expected transaction error — skip when using expect_entries_
    # (exception will be resolved at runtime via _exc)
    if not expect_entries:
        if is_multi and exc_varies:
            tx_parts.append("error=tx_error")
        else:
            expect_exception = cases_for_fork[0].get("expect_exception")
            if expect_exception:
                tx_parts.append(f"error={_format_exception(expect_exception)}")

    # -----------------------------------------------------------------------
    # Build expect_entries_ for runtime post-state resolution
    # -----------------------------------------------------------------------
    # Use filler expect entries when addresses are resolvable.
    # Fall back to synthesizing from compiled fixture state otherwise.
    expect_entries_source = ""
    pre_addrs_lower = {a.lower() for a in pre.keys()}
    all_fixture_addrs = set(pre_addrs_lower)
    for key in all_keys:
        test_item = fixture_data[key]
        for fork_posts in test_item.get("post", {}).values():
            for pe in fork_posts:
                for addr in pe.get("state", {}):
                    all_fixture_addrs.add(addr.lower())
    # Use filler Path A only when the filler has fork-specific entries
    # (different network values) or expect_exception — that's when it adds
    # value over Path B.  Otherwise Path B is safer because its values
    # come from the compiled fixture (EELS).
    filler_has_fork_info = False
    if expect_entries:
        networks = set()
        for entry in expect_entries:
            net = tuple(entry.get("network", []))
            networks.add(net)
            if entry.get("expect_exception"):
                filler_has_fork_info = True
        if len(networks) > 1:
            filler_has_fork_info = True

    filler_addrs_ok = True
    if expect_entries and filler_has_fork_info:
        for entry in expect_entries:
            for addr in entry.get("result", {}):
                a = addr.lower()
                if a == COINBASE_ADDRESS or "<" in a:
                    continue
                if a not in addr_vars and a not in all_fixture_addrs:
                    filler_addrs_ok = False
                    break
            if not filler_addrs_ok:
                break
    if expect_entries and filler_has_fork_info and filler_addrs_ok:
        expect_entries_source = _generate_expect_entries_source(
            expect_entries, addr_vars=addr_vars, indent="    "
        )
    else:
        # Synthesize from compiled fixture per-case post states,
        # carrying expect_exception from the compiled fixture.
        synth: list[dict] = []
        for case in cases_for_fork:
            ps = case.get("post_state", {})
            result: dict[str, dict] = {}
            for addr, acct in ps.items():
                fields: dict[str, Any] = {}
                storage = acct.get("storage", {})
                if storage:
                    fields["storage"] = storage
                code = acct.get("code", "0x")
                if code not in ("0x", ""):
                    fields["code"] = code
                if fields:
                    result[_normalize_address(addr)] = fields
            entry_dict: dict[str, Any] = {
                "indexes": {
                    "data": case["d"],
                    "gas": case["g"],
                    "value": case["v"],
                },
                "network": [f">={fork_name}"],
                "result": result,
            }
            exc = case.get("expect_exception")
            if exc:
                entry_dict["expect_exception"] = {
                    f">={fork_name}": exc,
                }
            synth.append(entry_dict)
        if synth:
            expect_entries_source = _generate_expect_entries_source(
                synth, addr_vars=addr_vars, indent="    "
            )

    # Post resolution via expect_entries_
    if is_multi and expect_entries_source:
        post_code = (
            "    post, _exc = resolve_expect_post("
            "expect_entries_, d, g, v, fork)"
        )
    elif not is_multi and expect_entries_source:
        # Single case: d=0, g=0, v=0
        c = cases_for_fork[0]
        post_code = (
            f"    post, _exc = resolve_expect_post("
            f"expect_entries_, {c['d']}, {c['g']}, {c['v']}, fork)"
        )
    elif not is_multi:
        ps = cases_for_fork[0].get("post_state", {})
        post_code = (
            _generate_post_from_fixture_state(ps, addr_vars)
            if ps
            else "    post: dict = {}"
        )
    else:
        post_code = "    post: dict = {}"

    # Check if post assertions use Op (needs import)
    if "Op." in post_code or "Op." in expect_entries_source:
        needs_op = True
    op_import = "from execution_testing.vm import Op"
    if needs_op and op_import not in imports:
        imports.append(op_import)

    # -----------------------------------------------------------------------
    # Assemble the file
    # -----------------------------------------------------------------------
    out = []
    out.append(module_doc)
    out.append("")
    out.extend(imports)
    out.append("")
    out.append('REFERENCE_SPEC_GIT_PATH = "N/A"')
    out.append('REFERENCE_SPEC_VERSION = "N/A"')
    out.append("")

    # --- Emit TX arrays and expect_entries_ constants ---
    if is_multi:
        # TX_DATA
        out.append("TX_DATA = [")
        for raw in tx_data_arr:
            s = str(raw)
            # Strip 0x prefix for consistency with bytes.fromhex
            if s.startswith("0x"):
                s = s[2:]
            out.append(f'    "{s}",')
        out.append("]")
        out.append("")
        # TX_GAS
        out.append(f"TX_GAS = {tx_gas_arr!r}")
        out.append("")
        # TX_VALUE
        out.append(f"TX_VALUE = {tx_value_arr!r}")
        out.append("")

    # expect_entries_ is emitted inside the function body (after variable
    # definitions) so it can reference variable names like callee, contract.

    # --- Helper for converting tx data hex to bytes ---
    if is_multi:
        out.append("")
        out.append("def _tx_data(d: int) -> bytes:")
        out.append('    """Convert TX_DATA[d] hex string to bytes."""')
        out.append(
            '    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""'
        )
        out.append("")

    # --- Parametrize + decorators ---
    if is_multi:
        # Build (d, g, v) tuples + optional extra params
        param_names = ["d", "g", "v"]
        extra_names: list[str] = []
        if to_varies:
            extra_names.append("tx_to")
        if al_varies:
            extra_names.append("tx_access_list")
        if exc_varies and not expect_entries:
            extra_names.append("tx_error")
        param_names.extend(extra_names)

        out.append("")
        ported_line = f'    ["{filler_path}"],'
        if len(ported_line) > 79:
            out.append("@pytest.mark.ported_from(")
            inner = f'        "{filler_path}",'
            out.append("    [")
            out.append(inner)
            out.append("    ],")
            out.append(")")
        else:
            out.append("@pytest.mark.ported_from(")
            out.append(ported_line)
            out.append(")")
        out.append(f'@pytest.mark.valid_from("{fork_name}")')
        if valid_until:
            out.append(f'@pytest.mark.valid_until("{valid_until}")')

        # Build parametrize values
        out.append("@pytest.mark.parametrize(")
        out.append(f'    "{", ".join(param_names)}",')
        out.append("    [")
        case_has_exc = []
        for i, case in enumerate(cases_for_fork):
            d_val, g_val, v_val = case["d"], case["g"], case["v"]
            vals = [str(d_val), str(g_val), str(v_val)]
            has_exc = False
            if to_varies:
                if case["to"]:
                    vals.append(f'Address("{_pad_address(case["to"])}")')
                else:
                    vals.append("None")
            if al_varies:
                al_case = case["access_list"]
                if al_case is None:
                    vals.append("None")
                else:
                    vals.append(_format_access_list(al_case, multiline=False))
            if exc_varies and not expect_entries:
                exc = case.get("expect_exception") or ""
                if exc:
                    vals.append(_format_exception(exc))
                    has_exc = True
                else:
                    vals.append("None")
            # When using expect_entries_, check if any matching filler
            # entry has expect_exception for this (d, g, v)
            if expect_entries and not has_exc:
                for ee in expect_entries:
                    if ee.get("expect_exception"):
                        idx = ee.get("indexes", {})
                        d_s = idx.get("data", -1)
                        g_s = idx.get("gas", -1)
                        v_s = idx.get("value", -1)
                        if (
                            _index_matches(d_s, d_val)
                            and _index_matches(g_s, g_val)
                            and _index_matches(v_s, v_val)
                        ):
                            has_exc = True
                            break
            case_has_exc.append(has_exc)
            pid = f"case{i}"
            if has_exc:
                joined = ", ".join(vals)
                entry = (
                    f"pytest.param({joined},"
                    f' id="{pid}",'
                    f" marks=pytest.mark.exception_test)"
                )
            else:
                entry = f'pytest.param({", ".join(vals)}, id="{pid}")'
            out.append(f"        {entry},")
        out.append("    ],")
        out.append(")")
    else:
        out.append("")
        ported_line = f'    ["{filler_path}"],'
        if len(ported_line) > 79:
            out.append("@pytest.mark.ported_from(")
            inner = f'        "{filler_path}",'
            out.append("    [")
            out.append(inner)
            out.append("    ],")
            out.append(")")
        else:
            out.append("@pytest.mark.ported_from(")
            out.append(ported_line)
            out.append(")")
        out.append(f'@pytest.mark.valid_from("{fork_name}")')
        if valid_until:
            out.append(f'@pytest.mark.valid_until("{valid_until}")')

    # pre_alloc_mutable since generated tests assign pre[addr] = Account(...)
    out.append("@pytest.mark.pre_alloc_mutable")

    if slow:
        out.append("@pytest.mark.slow")

    # Add exception_test marker if ALL cases expect transaction failure
    if needs_tx_exception and not (is_multi and exc_varies):
        out.append("@pytest.mark.exception_test")

    # Function signature
    func_params = ["    state_test: StateTestFiller,", "    pre: Alloc,"]
    if is_multi or expect_entries_source:
        func_params.append("    fork: Fork,")
    if is_multi:
        func_params.append("    d: int,")
        func_params.append("    g: int,")
        func_params.append("    v: int,")
        if to_varies:
            func_params.append("    tx_to: Address,")
        if al_varies:
            func_params.append("    tx_access_list: list | None,")
        if exc_varies and not expect_entries:
            func_params.append("    tx_error: object,")
    def_line = f"def {test_func_name}("
    out.append(def_line)
    out.extend(func_params)
    out.append(") -> None:")

    # Function docstring — single-line, with punctuation (D400/D415)
    func_doc = filler_comment.split("\n")[0].rstrip() if filler_comment else ""
    # D404: first word should not be "This"
    if func_doc.startswith("This "):
        func_doc = func_doc[5:]
    if not func_doc:
        func_doc = "Test ported from static filler"
    # Capitalize first letter (D403)
    func_doc = func_doc[0].upper() + func_doc[1:]
    if func_doc[-1] not in ".?!":
        func_doc += "."
    # Truncate if too long for single-line docstring (79 - 4 - 6 = 69)
    if len(func_doc) > 69:
        func_doc = _truncate_at_word(func_doc, 69)
    # Escape content that would break triple-quoted docstrings
    func_doc = func_doc.replace("\\", "\\\\")
    func_doc = func_doc.replace('"""', '""\\"')
    out.append(f'    """{func_doc}"""')

    # Determine which accounts will use deploy_contract (so we skip
    # emitting a separate Address variable for them — deploy_contract
    # assigns the variable directly).
    deploy_contract_vars: set[str] = set()
    for addr in sorted(pre.keys()):
        addr_l = addr.lower()
        var = addr_vars.get(addr_l, "")
        code_hex = pre[addr].get("code", "0x")
        raw_hex = code_hex[2:] if code_hex.startswith("0x") else code_hex
        is_eoa_acct = code_hex in ("0x", "")
        is_oversized_acct = len(raw_hex) > 49152
        is_sender_acct = var == "sender"
        if not is_eoa_acct and not is_oversized_acct:
            deploy_contract_vars.add(var)

    # Address variables — only emit if used somewhere
    pre_addrs = {a.lower() for a in pre.keys()}
    all_code = (
        post_code
        + " "
        + expect_entries_source
        + " "
        + " ".join(str(p) for p in tx_parts)
    )
    sender_emitted = False
    for addr, var, _ in var_names:
        # Skip vars that will be assigned by deploy_contract
        # (but not coinbase — it must be defined before env)
        if var in deploy_contract_vars and var != "coinbase":
            continue
        used = (
            addr in pre_addrs
            or var == "coinbase"  # fee_recipient=coinbase
            or var == "sender"  # always used (Transaction sender=sender)
            or bool(re.search(rf"\b{re.escape(var)}\b", all_code))
        )
        if used:
            if var == "sender":
                out.append(
                    f"    sender = EOA(\n        key=0x{secret_key_hex}\n    )"
                )
                sender_emitted = True
            else:
                out.append(f'    {var} = Address("{_pad_address(addr)}")')
    # Handle "no sender" tests: sender not in var_names but we still need it
    if not sender_emitted:
        out.append(f"    sender = EOA(\n        key=0x{secret_key_hex}\n    )")
    out.append("")

    # Environment
    out.append("    env = Environment(")
    for p in env_parts:
        out.append(f"        {p},")
    out.append("    )")
    out.append("")

    # Pre-state accounts
    src = code_sources or _FillerCodeSources()
    for addr in sorted(pre.keys()):
        addr_l = addr.lower()
        var = addr_vars.get(addr_l, f'Address("{addr}")')
        code_hex = pre[addr].get("code", "0x")
        src_comment = src.lookup(
            addr_l,
            code_hex,
            is_to_addr=(addr_l == to_addr),
        )
        is_sender_acct = addr_l == sender_addr
        is_var_used = (
            bool(re.search(rf"\b{re.escape(var)}\b", all_code))
            or var == "coinbase"
        )
        # coinbase and sender are already defined (as Address / EOA)
        # before the pre-state section, so deploy_contract should not
        # re-assign them.
        is_already_defined = var in ("coinbase", "sender")
        account_code = generate_account_setup(
            addr_l,
            pre[addr],
            var,
            indent="    ",
            source_comment=src_comment,
            is_sender=is_sender_acct,
            var_is_used=is_var_used,
            already_defined=is_already_defined,
        )
        out.append(account_code)

    out.append("")

    # expect_entries_ — inside function body so it can use variable names
    if expect_entries_source:
        out.append(expect_entries_source)
        out.append("")

    # Post state assertions (resolved before tx so _exc is available)
    if expect_entries_source:
        out.append(post_code)
        out.append("")

    # Transaction
    out.append("    tx = Transaction(")
    for p in tx_parts:
        out.append(f"        {p},")
    # Add error=_exc when using expect_entries_ (exception from filler)
    if expect_entries_source:
        out.append("        error=_exc,")
    out.append("    )")
    out.append("")

    # Post state assertions (for non-expect_entries_ path)
    if not expect_entries_source:
        out.append(post_code)
        out.append("")

    out.append("    state_test(env=env, pre=pre, post=post, tx=tx)")
    out.append("")

    return "\n".join(out)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


# Reverse lookup: lowercase fork dir name -> canonical fork name
_DIR_TO_FORK = {name.lower(): name for name in FORK_ORDER}


def _extract_fork_from_path(path: Path, root: Path) -> str | None:
    """Extract the fork name from a for_* directory in the path."""
    for part in path.relative_to(root).parts:
        if part.startswith("for_"):
            name = part[4:]
            return _DIR_TO_FORK.get(name)
    return None


def _group_fixture_candidates(
    fixtures_dir: Path,
) -> dict[str, list[tuple[str, Path]]]:
    """
    Group fixture JSON files by identity across for_* directories.

    Return a dict mapping identity (path after for_*/) to list of
    (fork_name, path) pairs.
    """
    candidates: list[Path] = []
    for p in fixtures_dir.rglob("*.json"):
        if ".meta" in p.parts:
            continue
        rel = str(p.relative_to(fixtures_dir))
        # Must be under state_tests/for_* (not blockchain_tests)
        if not rel.startswith("state_tests/") and "/state_tests/" not in rel:
            continue
        if "/for_" not in rel and not rel.startswith("for_"):
            continue
        if "ported_static" in rel:
            continue
        candidates.append(p)

    groups: dict[str, list[tuple[str, Path]]] = {}
    for p in candidates:
        rel = str(p.relative_to(fixtures_dir))
        idx = rel.find("/static/")
        if idx >= 0:
            identity = rel[idx + len("/static/") :]
        else:
            import re as _re

            m = _re.search(r"/for_[^/]+/", rel)
            if m:
                identity = rel[m.end() :]
            elif rel.startswith("for_"):
                slash = rel.find("/")
                identity = rel[slash + 1 :] if slash >= 0 else rel
            else:
                continue
        fork = _extract_fork_from_path(p, fixtures_dir)
        if fork is None:
            continue
        groups.setdefault(identity, []).append((fork, p))
    return groups


def find_fixture_files(fixtures_dir: Path) -> list[Path]:
    """
    Find state_test fixture JSON files from static fillers.

    Supports two output layouts:
      - with ``static/``:  state_tests/for_*/static/state_tests/{cat}/…
      - without:           state_tests/for_*/{cat}/…

    When the same fixture exists across multiple for_* directories
    (e.g. for_cancun, for_prague), only the earliest fork's file is
    kept so that valid_from is set correctly.
    """
    groups = _group_fixture_candidates(fixtures_dir)

    # Pick the earliest fork per fixture
    results = []
    for _identity, fork_paths in groups.items():
        known = [(f, p) for f, p in fork_paths if f in FORK_RANK]
        if known:
            known.sort(key=lambda fp: FORK_RANK[fp[0]])
            results.append(known[0][1])
        else:
            results.append(fork_paths[0][1])

    return sorted(results)


def find_fixture_files_grouped(
    fixtures_dir: Path,
) -> list[tuple[Path, dict[str, Path]]]:
    """
    Find fixture files and return with all fork variants.

    Return a list of (earliest_path, {fork: path}) for each unique
    fixture identity.
    """
    groups = _group_fixture_candidates(fixtures_dir)

    results = []
    for _identity, fork_paths in groups.items():
        known = [(f, p) for f, p in fork_paths if f in FORK_RANK]
        if not known:
            fp_dict = {fork_paths[0][0]: fork_paths[0][1]}
            results.append((fork_paths[0][1], fp_dict))
            continue
        known.sort(key=lambda fp: FORK_RANK[fp[0]])
        fp_dict = dict(known)
        results.append((known[0][1], fp_dict))

    return sorted(results, key=lambda x: x[0])


def fixture_to_filler_path(fixture_data: dict) -> str | None:
    """Extract the filler path from a fixture's test key."""
    for key in fixture_data:
        # Key: "tests/static/.../XFiller.json::TestName[...]"
        if "::" in key:
            return key.split("::")[0]
    return None


def process_single_fixture(
    fixture_path: Path,
    fillers_dir: Path,
    output_dir: Path,
    all_fork_paths: dict[str, Path] | None = None,  # noqa: ARG001
) -> tuple[bool, str]:
    """
    Process a single fixture file. Returns (success, message).

    Parameters
    ----------
    fixture_path
        Path to the fixture JSON file to process.
    fillers_dir
        Root directory containing filler source files.
    output_dir
        Directory where the generated Python test file is written.
    all_fork_paths
        Unused. Kept for call-site compatibility.

    """
    with open(fixture_path) as f:
        fixture_data = json.load(f)

    filler_path = fixture_to_filler_path(fixture_data)
    if not filler_path:
        return False, f"Could not extract filler path from {fixture_path}"

    # Load filler comment
    filler_full_path = fillers_dir.parent.parent / filler_path
    if not filler_full_path.exists():
        # Try relative to repo root
        filler_full_path = Path(filler_path)
    filler_comment = load_filler_comment(filler_full_path)

    # Extract source code comments from filler pre-state
    filler_data = _load_filler_data(filler_full_path)
    code_sources = _extract_filler_code_sources(filler_data)

    # Load filler expect entries, resolve labels and remap tag addresses
    expect_entries = load_filler_expect_results(filler_full_path)
    if expect_entries:
        expect_entries = _resolve_filler_labels(
            filler_full_path, expect_entries
        )
        # Remap filler tag addresses to compiled fixture addresses
        addr_map = _build_filler_address_map(filler_data)
        if addr_map:
            expect_entries = _remap_expect_addresses(expect_entries, addr_map)

    # Detect fork bounds from filler network (e.g. ">=Cancun<Osaka")
    upper_bound = load_filler_network_upper_bound(filler_full_path)
    valid_until = fork_before(upper_bound) if upper_bound else None
    filler_lower_bound = load_filler_network_lower_bound(filler_full_path)

    # Determine output path
    filler_stem = Path(filler_path).stem  # e.g. "callcode_checkPCFiller"
    test_name = filler_name_to_test_name(filler_stem)

    # Extract category from filler path
    # e.g. tests/static/state_tests/stCallCodes/... -> stCallCodes
    filler_parts = Path(filler_path).parts
    # Find the part after "state_tests"
    category = ""
    for i, part in enumerate(filler_parts):
        if part == "state_tests" and i + 1 < len(filler_parts):
            # If there's a subfolder (e.g. Cancun/stEIP...), include it
            remaining = filler_parts[i + 1 : -1]
            category = str(Path(*remaining)) if remaining else ""
            break

    # Check if the top-level category is slow
    top_category = Path(category).parts[0] if category else ""
    is_slow = top_category in SLOW_CATEGORIES

    # Load filler TX arrays for TX_DATA/TX_GAS/TX_VALUE constants
    filler_tx = load_filler_tx_arrays(filler_full_path)

    # No more fork-range variant generation — fork handling is at runtime
    # via resolve_expect_post(expect_entries_, d, g, v, fork).
    try:
        python_code = generate_test_file(
            fixture_data,
            filler_path,
            filler_comment,
            valid_until=valid_until,
            valid_from_override=filler_lower_bound,
            filler_full_path=filler_full_path,
            code_sources=code_sources,
            slow=is_slow,
            expect_entries=expect_entries or None,
            filler_tx_arrays=filler_tx,
        )
    except Exception as e:
        return False, f"Error generating {fixture_path}: {e}"

    out_dir = output_dir / category if category else output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    # Write __init__.py files with docstrings in every package dir
    for parent in [out_dir, *out_dir.parents]:
        if parent == output_dir.parent:
            break
        init_file = parent / "__init__.py"
        if not init_file.exists() or init_file.stat().st_size == 0:
            pkg = parent.name
            init_file.write_text(f'"""Tests ported from {pkg}."""\n')

    out_file = out_dir / f"{test_name}.py"
    out_file.write_text(python_code)

    return True, f"Generated {out_file}"


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Convert compiled state_test fixtures to Python."
    )
    parser.add_argument(
        "--fixtures",
        type=Path,
        required=True,
        help="Path to compiled fixture directory (from --fill-static-tests)",
    )
    parser.add_argument(
        "--fillers",
        type=Path,
        required=True,
        help="Path to source filler directory (tests/static/state_tests/)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Output directory for generated Python tests",
    )
    parser.add_argument(
        "--single",
        type=Path,
        default=None,
        help="Process a single fixture file (for testing)",
    )
    parser.add_argument(
        "--filter",
        type=Path,
        default=None,
        help="Only convert fixtures in this file (one per line)",
    )
    args = parser.parse_args()

    # Load filter list if provided
    filter_set: set[str] | None = None
    if args.filter:
        with open(args.filter) as f:
            filter_set = {line.strip() for line in f if line.strip()}

    if args.single:
        # Single mode: no fork grouping
        entries: list[tuple[Path, dict[str, Path] | None]] = [
            (args.single, None),
        ]
    else:
        grouped = find_fixture_files_grouped(args.fixtures)
        entries = [(fp, fork_paths) for fp, fork_paths in grouped]

    # Filter fixtures to only those matching the filter list
    if filter_set is not None:
        filtered = []
        for fp, fork_paths in entries:
            with open(fp) as f:
                data = json.load(f)
            filler_path = fixture_to_filler_path(data)
            if filler_path and filler_path in filter_set:
                filtered.append((fp, fork_paths))
        print(f"Filtered: {len(filtered)}/{len(entries)} fixtures match")
        entries = filtered

    if not entries:
        print("No fixture files found.")
        sys.exit(1)

    args.output.mkdir(parents=True, exist_ok=True)

    success_count = 0
    fail_count = 0
    for fixture_path, fork_paths in entries:
        ok, msg = process_single_fixture(
            fixture_path,
            args.fillers,
            args.output,
            all_fork_paths=fork_paths,
        )
        if ok:
            success_count += 1
            print(f"  OK: {msg}")
        else:
            fail_count += 1
            print(f"FAIL: {msg}", file=sys.stderr)

    print(f"\nDone: {success_count} generated, {fail_count} failed")
    if fail_count > 0:
        sys.exit(1)

    # Post-process: ruff format + add noqa: E501 to unsplittable lines
    _post_format(args.output)


def _post_format(output_dir: Path) -> None:
    """Run ruff format on generated files, then suppress E501."""
    # Increase Rust stack size to prevent ruff stack overflow on deeply
    # nested generated code (which can corrupt files to 0 bytes).
    env = {**os.environ, "RUST_MIN_STACK": "16777216"}
    print("\nRunning ruff format...")
    subprocess.run(
        ["ruff", "format", str(output_dir)],
        check=False,
        env=env,
    )
    print("Running ruff check --fix (import sorting)...")
    subprocess.run(
        ["ruff", "check", "--fix", str(output_dir)],
        check=False,
        env=env,
    )

    print("Adding # noqa: E501 to long lines...")
    count = 0
    for py_file in output_dir.rglob("*.py"):
        text = py_file.read_text()
        lines = text.split("\n")
        changed = False
        for i, line in enumerate(lines):
            if len(line) > 79 and "# noqa: E501" not in line:
                lines[i] = line + "  # noqa: E501"
                changed = True
        if changed:
            py_file.write_text("\n".join(lines))
            count += 1
    print(f"  Patched {count} files")


if __name__ == "__main__":
    main()
