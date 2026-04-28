"""Tests for validate exception mapper config helpers."""

from pathlib import Path

from execution_testing.cli.pytest_commands.plugins.validate.conftest import (
    _resolve_config_relative_path,
)


def test_exception_mapper_path_resolves_relative_to_validate_toml(
    tmp_path: Path,
) -> None:
    """Resolve configured mapper paths relative to the TOML file."""
    config_path = tmp_path / "configs" / "validate.toml"
    mapper_path = _resolve_config_relative_path(
        "../client/eest-exceptions.yaml",
        config_path,
    )

    assert mapper_path == (
        tmp_path / "configs" / "../client/eest-exceptions.yaml"
    )
