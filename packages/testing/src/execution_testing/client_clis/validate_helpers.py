"""Shared helpers for validate / validate adapters."""

import json
from pathlib import Path
from typing import Any, Dict, List

from execution_testing.exceptions import (
    ExceptionBase,
    ExceptionMapper,
    UndefinedException,
)


def load_fixture_json(
    cache: Dict[str, Any],
    fixture_path: Path,
) -> Dict[str, Any]:
    """Load and cache fixture JSON keyed by file path."""
    key = str(fixture_path)
    if key not in cache:
        file_path = fixture_path if fixture_path.is_file() else None
        if file_path is None:
            return {}
        cache[key] = json.loads(file_path.read_text())
    return cache[key]


def get_expected_exceptions(
    fixture_cache: Dict[str, Any],
    fixture_path: Path,
    fixture_name: str,
    is_engine: bool = False,
    is_block: bool = False,
    is_state: bool = False,
) -> List[ExceptionBase]:
    """Extract expected exceptions from a fixture for a given test case."""
    fixture_json = load_fixture_json(fixture_cache, fixture_path)
    test_data = fixture_json.get(fixture_name, {})
    exceptions: List[ExceptionBase] = []

    if is_engine:
        for payload in test_data.get("engineNewPayloads", []):
            ve = payload.get("validationError")
            if ve:
                exceptions.extend(
                    ExceptionBase.from_str(e) for e in ve.split("|")
                )
    elif is_block:
        for block in test_data.get("blocks", []):
            ee = block.get("expectException")
            if ee:
                exceptions.extend(
                    ExceptionBase.from_str(e) for e in ee.split("|")
                )
    elif is_state:
        for fork_posts in test_data.get("post", {}).values():
            for post in fork_posts:
                ee = post.get("expectException")
                if ee:
                    exceptions.extend(
                        ExceptionBase.from_str(e) for e in ee.split("|")
                    )

    return exceptions


def check_exception(
    mapper: ExceptionMapper,
    label: str,
    fixture_name: str,
    error: str,
    expected: List[ExceptionBase],
) -> None:
    """Map client error through ExceptionMapper and compare to expected."""
    mapped = mapper.message_to_exception(error)
    if isinstance(mapped, UndefinedException):
        raise AssertionError(
            f"{label} test: unmapped error for {fixture_name}:\n"
            f"  expected: {expected}\n"
            f"  error: {error}\n"
            f"  mapper: {mapped.mapper_name}"
        )
    if not any(exc in expected for exc in mapped):
        raise AssertionError(
            f"{label} test: wrong exception for {fixture_name}:\n"
            f"  expected: {expected}\n"
            f"  got: {mapped}\n"
            f"  error: {error}"
        )


def validate_test_result(
    fixture_cache: Dict[str, Any],
    mapper: ExceptionMapper,
    label: str,
    fixture_name: str,
    result: Dict[str, Any],
    fixture_path: Path,
    is_engine: bool = False,
    is_block: bool = False,
    is_state: bool = False,
    exception_check: bool = True,
) -> None:
    """Validate a single test result: exceptions, fields, pass/fail.

    This is the shared core of every adapter's _validate_test.
    Call after looking up the result from dir_results.
    """
    expected = get_expected_exceptions(
        fixture_cache, fixture_path, fixture_name,
        is_engine=is_engine, is_block=is_block, is_state=is_state,
    )
    error = result.get("error", "")

    if expected and error and exception_check:
        check_exception(mapper, label, fixture_name, error, expected)

    check_result_fields(
        fixture_cache, label, fixture_name, result,
        fixture_path, expected,
        is_block=is_block, is_engine=is_engine,
    )

    if not result["pass"]:
        raise AssertionError(f"{label} test failed: {error}")


def check_result_fields(
    fixture_cache: Dict[str, Any],
    label: str,
    fixture_name: str,
    result: Dict[str, Any],
    fixture_path: Path,
    expected_exceptions: List[ExceptionBase],
    is_block: bool = False,
    is_engine: bool = False,
) -> None:
    """Cross-check lastBlockHash and lastPayloadStatus against fixture."""
    fixture_json = load_fixture_json(fixture_cache, fixture_path)
    test_data = fixture_json.get(fixture_name, {})

    # Check lastBlockHash for block/engine tests
    if is_block or is_engine:
        expected_hash = test_data.get("lastblockhash", "")
        actual_hash = result.get("lastBlockHash", "")
        if expected_hash and actual_hash:
            expected_hex = (
                "0x" + expected_hash
                if not expected_hash.startswith("0x")
                else expected_hash
            )
            if actual_hash.lower() != expected_hex.lower():
                raise AssertionError(
                    f"{label} test: lastBlockHash mismatch for "
                    f"{fixture_name}:\n"
                    f"  expected: {expected_hex}\n"
                    f"  got: {actual_hash}"
                )

    # Check lastPayloadStatus for engine tests
    if is_engine:
        actual_status = result.get("lastPayloadStatus", "")
        if actual_status and expected_exceptions:
            if actual_status != "INVALID":
                raise AssertionError(
                    f"{label} test: expected INVALID payload "
                    f"status for {fixture_name} (has expected "
                    f"exceptions), got {actual_status}"
                )
        elif actual_status and not expected_exceptions:
            if actual_status != "VALID":
                raise AssertionError(
                    f"{label} test: expected VALID payload "
                    f"status for {fixture_name}, "
                    f"got {actual_status}"
                )
