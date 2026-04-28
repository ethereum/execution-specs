"""Tests for consume exception mapper selection."""

from pathlib import Path

from execution_testing.cli.pytest_commands.plugins.consume.simulators import (
    exceptions,
)
from execution_testing.exceptions import (
    BlockException,
    TransactionException,
)


def test_parse_exception_mapper_option(tmp_path: Path) -> None:
    """Parse repeatable CLIENT=PATH mapper options."""
    mapper_path = tmp_path / "mapper.yaml"
    mapper_path.write_text(
        """
version: 1
substring:
  BlockException.INVALID_GASLIMIT: custom gas
"""
    )

    mappers = exceptions._parse_external_exception_mapper_options(
        [f"geth={mapper_path}"]
    )

    assert list(mappers) == ["geth"]
    assert mappers["geth"].message_to_exception("custom gas") == [
        BlockException.INVALID_GASLIMIT
    ]


def test_configured_exception_mapper_extends_matching_client(
    tmp_path: Path,
) -> None:
    """Extend the selected built-in mapper for matching Hive client names."""
    mapper_path = tmp_path / "mapper.yaml"
    mapper_path.write_text(
        """
version: 1
substring:
  BlockException.INVALID_GASLIMIT: custom gas
"""
    )
    external = exceptions._parse_external_exception_mapper_options(
        [f"geth={mapper_path}"]
    )

    mapper = exceptions.get_configured_exception_mapper(
        "go-ethereum", external
    )

    assert mapper is not None
    assert mapper.message_to_exception("custom gas") == [
        BlockException.INVALID_GASLIMIT
    ]


def test_unmatched_exception_mapper_option_is_ignored(
    tmp_path: Path,
) -> None:
    """Do not apply external mappings to non-matching clients."""
    mapper_path = tmp_path / "mapper.yaml"
    mapper_path.write_text(
        """
version: 1
substring:
  TransactionException.INSUFFICIENT_ACCOUNT_FUNDS: custom funds
"""
    )
    external = exceptions._parse_external_exception_mapper_options(
        [f"besu={mapper_path}"]
    )

    mapper = exceptions.get_configured_exception_mapper(
        "go-ethereum", external
    )

    assert mapper is not None
    assert mapper.message_to_exception("custom funds") != [
        TransactionException.INSUFFICIENT_ACCOUNT_FUNDS
    ]
