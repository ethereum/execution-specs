#!/usr/bin/env -S uv run --script
"""Validate a zkEVM benchmark fixture archive before release."""

import json
import re
import sys
import tarfile
from pathlib import Path, PurePosixPath
from typing import Any, NoReturn

EXPECTED_FORMAT = "blockchain_tests"
EXPECTED_TARGETS = {
    "for_amsterdam_at_0010M",
    "for_amsterdam_at_0030M",
    "for_amsterdam_at_0060M",
}
FIXTURE_FORMATS = {
    "state_tests",
    "blockchain_tests",
    "blockchain_tests_engine",
    "blockchain_tests_engine_x",
    "blockchain_tests_sync",
}
HEX_BYTES_RE = re.compile(r"^0x(?:[0-9a-fA-F]{2})+$")


def fail(message: str) -> NoReturn:
    """Raise a release validation error."""
    raise ValueError(message)


def validate_hex_bytes(value: Any, field: str) -> None:
    """Validate one non-empty hexadecimal byte string."""
    if not isinstance(value, str) or not HEX_BYTES_RE.fullmatch(value):
        fail(f"{field} must be a non-empty, even-length 0x byte string")


def validate_case(case_name: str, fixture: Any) -> None:
    """Validate one fixture case."""
    if not isinstance(fixture, dict):
        fail(f"{case_name}: fixture must be an object")
    if fixture.get("network") != "Amsterdam":
        fail(f"{case_name}: network must be Amsterdam")

    blocks = fixture.get("blocks")
    if not isinstance(blocks, list) or not blocks:
        fail(f"{case_name}: blocks must be a non-empty list")
    final_block = blocks[-1]
    if not isinstance(final_block, dict):
        fail(f"{case_name}: final block must be an object")
    validate_hex_bytes(
        final_block.get("statelessInputBytes"),
        f"{case_name}: final block statelessInputBytes",
    )
    validate_hex_bytes(
        final_block.get("statelessOutputBytes"),
        f"{case_name}: final block statelessOutputBytes",
    )

    info = fixture.get("_info")
    metadata = info.get("metadata") if isinstance(info, dict) else None
    opcode_counts = (
        metadata.get("opcode_count_per_block")
        if isinstance(metadata, dict)
        else None
    )
    if not isinstance(opcode_counts, list):
        fail(f"{case_name}: opcode_count_per_block must be a list")
    if len(opcode_counts) != len(blocks):
        fail(
            f"{case_name}: opcode_count_per_block has {len(opcode_counts)} "
            f"entries for {len(blocks)} blocks"
        )
    if not isinstance(opcode_counts[-1], dict) or not opcode_counts[-1]:
        fail(f"{case_name}: final opcode count must be a non-empty object")


def validate_archive(archive_path: Path) -> tuple[int, int]:
    """Validate *archive_path* and return its file and fixture counts."""
    fixture_files = 0
    fixture_cases = 0
    seen_formats: set[str] = set()

    with tarfile.open(archive_path, mode="r:gz") as archive:
        for member in archive:
            path = PurePosixPath(member.name)
            member_formats = FIXTURE_FORMATS.intersection(path.parts)
            seen_formats.update(member_formats)
            if not member.isfile() or path.suffix != ".json":
                continue
            if EXPECTED_FORMAT not in path.parts or ".meta" in path.parts:
                continue

            format_index = path.parts.index(EXPECTED_FORMAT)
            if len(path.parts) <= format_index + 1:
                fail(f"{member.name}: missing benchmark target directory")
            target = path.parts[format_index + 1]
            if target not in EXPECTED_TARGETS:
                fail(
                    f"{member.name}: target must be one of "
                    f"{', '.join(sorted(EXPECTED_TARGETS))}. Got {target}"
                )

            extracted = archive.extractfile(member)
            if extracted is None:
                fail(f"{member.name}: could not read fixture file")
            try:
                contents = json.load(extracted)
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                fail(f"{member.name}: invalid JSON: {error}")
            if not isinstance(contents, dict) or not contents:
                fail(f"{member.name}: fixture file must be a non-empty object")

            fixture_files += 1
            for case_name, fixture in contents.items():
                validate_case(f"{member.name}:{case_name}", fixture)
                fixture_cases += 1

    unexpected_formats = seen_formats - {EXPECTED_FORMAT}
    if unexpected_formats:
        fail(
            "archive contains unexpected fixture formats: "
            + ", ".join(sorted(unexpected_formats))
        )
    if fixture_files == 0 or fixture_cases == 0:
        fail("archive contains no zkEVM benchmark fixtures")
    return fixture_files, fixture_cases


def main() -> None:
    """Validate the command-line fixture archive."""
    if len(sys.argv) != 2:
        print(
            "Usage: validate_zkevm_benchmark_fixtures.py <archive.tar.gz>",
            file=sys.stderr,
        )
        sys.exit(1)
    archive_path = Path(sys.argv[1])
    try:
        fixture_files, fixture_cases = validate_archive(archive_path)
    except (OSError, tarfile.TarError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
    print(
        f"Validated {fixture_cases} fixture cases in "
        f"{fixture_files} fixture files."
    )


if __name__ == "__main__":
    main()
