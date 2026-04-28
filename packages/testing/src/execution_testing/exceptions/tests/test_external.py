"""Tests for YAML-backed exception mappers."""

from pathlib import Path

import pytest

from execution_testing.exceptions import (
    BlockException,
    ExceptionBase,
    ExceptionMapper,
    TransactionException,
    UndefinedException,
    extend_exception_mapper,
    load_external_exception_mapper,
)


class BuiltInMapper(ExceptionMapper):
    """Small built-in mapper for composition tests."""

    mapping_substring = {
        TransactionException.INSUFFICIENT_ACCOUNT_FUNDS: "built-in funds",
    }
    mapping_regex = {
        BlockException.INVALID_GASLIMIT: r"built-in gas \d+",
    }


def write_mapper(tmp_path: Path, content: str) -> Path:
    """Write a mapper file."""
    path = tmp_path / "mapper.yaml"
    path.write_text(content)
    return path


def test_load_external_mapper_accepts_strings_and_lists(
    tmp_path: Path,
) -> None:
    """Load substring and regex mappings from YAML."""
    mapper = load_external_exception_mapper(
        write_mapper(
            tmp_path,
            """
version: 1
name: geth-ci
substring:
  TransactionException.INSUFFICIENT_ACCOUNT_FUNDS:
    - insufficient funds
regex:
  BlockException.INVALID_GASLIMIT: child gas_limit \\d+
""",
        )
    )

    assert mapper.mapper_name == "geth-ci"
    assert mapper.message_to_exception("has insufficient funds now") == [
        TransactionException.INSUFFICIENT_ACCOUNT_FUNDS
    ]
    assert mapper.message_to_exception("child gas_limit 123") == [
        BlockException.INVALID_GASLIMIT
    ]


@pytest.mark.parametrize(
    "content, match",
    [
        (
            """
version: 1
substring:
  TransactionException.DOES_NOT_EXIST: nope
""",
            "Unknown exception name",
        ),
        (
            """
version: 1
regex:
  BlockException.INVALID_GASLIMIT: "["
""",
            "Invalid regex",
        ),
        (
            """
version: 1
substring:
  TransactionException.INSUFFICIENT_ACCOUNT_FUNDS: ""
""",
            "Empty pattern",
        ),
        (
            """
version: 1
unknown: true
""",
            "Extra inputs are not permitted",
        ),
        (
            """
name: missing-version
""",
            "Field required",
        ),
    ],
)
def test_load_external_mapper_rejects_invalid_yaml(
    tmp_path: Path,
    content: str,
    match: str,
) -> None:
    """Reject invalid external mapper files."""
    with pytest.raises(ValueError, match=match):
        load_external_exception_mapper(write_mapper(tmp_path, content))


def test_external_mapper_returns_undefined_for_unmatched(
    tmp_path: Path,
) -> None:
    """Return UndefinedException when no external pattern matches."""
    mapper = load_external_exception_mapper(
        write_mapper(
            tmp_path,
            """
version: 1
substring:
  TransactionException.INSUFFICIENT_ACCOUNT_FUNDS: insufficient funds
""",
        )
    )

    mapped = mapper.message_to_exception("different error")

    assert isinstance(mapped, UndefinedException)
    assert mapped.mapper_name == "ExternalExceptionMapper"


def test_extend_exception_mapper_combines_and_deduplicates(
    tmp_path: Path,
) -> None:
    """External mappings extend built-ins without duplicate matches."""
    external = load_external_exception_mapper(
        write_mapper(
            tmp_path,
            """
version: 1
substring:
  TransactionException.INSUFFICIENT_ACCOUNT_FUNDS: built-in funds
  BlockException.INVALID_GASLIMIT: external gas
""",
        )
    )
    mapper = extend_exception_mapper(BuiltInMapper(), external)
    assert mapper is not None

    assert mapper.message_to_exception("built-in funds and external gas") == [
        TransactionException.INSUFFICIENT_ACCOUNT_FUNDS,
        BlockException.INVALID_GASLIMIT,
    ]


def test_exception_keys_are_exact_eest_names(tmp_path: Path) -> None:
    """Accepted keys resolve through ExceptionBase.from_str."""
    mapper = load_external_exception_mapper(
        write_mapper(
            tmp_path,
            """
version: 1
substring:
  BlockException.INVALID_GASLIMIT: gas
""",
        )
    )

    assert mapper.substring == {
        ExceptionBase.from_str("BlockException.INVALID_GASLIMIT"): ["gas"]
    }
