"""Tests for the extract_config CLI."""

from pathlib import Path

import pytest
from click.testing import CliRunner

from execution_testing.base_types import Alloc
from execution_testing.cli.extract_config.exportable_genesis import (
    ExportableGenesis,
)
from execution_testing.cli.extract_config.extract_config import (
    CLIENT_EXPORTERS,
    extract_config,
)
from execution_testing.fixtures.pre_alloc_groups import PreAllocGroupBuilder
from execution_testing.forks import (
    Fork,
    Prague,
    forks_from_until,
    get_deployed_forks,
)
from execution_testing.test_types import Environment

CURRENT_FOLDER = Path(__file__).parent
CANCUN_FIXTURE = CURRENT_FOLDER / "fixtures" / "1" / "cancun" / "fixture.json"


def forks_from_prague_onward() -> list[Fork]:
    """Return deployed forks from Prague onward."""
    all_forks = get_deployed_forks()
    return list(forks_from_until(Prague, all_forks[-1]))


@pytest.mark.parametrize("fork", forks_from_prague_onward())
def test_from_pre_alloc_group_uses_stored_chain_id(
    tmp_path: Path,
    fork: Fork,
) -> None:
    """Pre-alloc group files should preserve the configured chain ID."""
    builder = PreAllocGroupBuilder(
        test_ids=["test_id"],
        environment=Environment()
        .set_fork_requirements(fork)
        .model_dump(mode="json", exclude={"parent_hash"}),
        fork=fork.name(),
        chain_id=12345,
        pre=Alloc().model_dump(mode="json"),
    )
    fixture_path = tmp_path / "pre_alloc.json"
    fixture_path.write_text(
        builder.model_dump_json(by_alias=True, exclude_none=True, indent=2)
    )

    genesis = ExportableGenesis.from_fixture(fixture_path)

    assert genesis.chain_id == 12345


@pytest.mark.parametrize("fork", forks_from_prague_onward())
def test_from_legacy_pre_alloc_group_defaults_chain_id(
    tmp_path: Path,
    fork: Fork,
) -> None:
    """Legacy pre-alloc groups without chain ID should still default to 1."""
    builder = PreAllocGroupBuilder(
        test_ids=["test_id"],
        environment=Environment()
        .set_fork_requirements(fork)
        .model_dump(mode="json", exclude={"parent_hash"}),
        fork=fork.name(),
        pre=Alloc().model_dump(mode="json"),
    )
    fixture_path = tmp_path / "legacy_pre_alloc.json"
    fixture_path.write_text(builder.model_dump_json(exclude={"chain_id"}))

    genesis = ExportableGenesis.from_fixture(fixture_path)

    assert genesis.chain_id == 1


def test_cli_generates_files_for_every_client(tmp_path: Path) -> None:
    """With no `--client` filter, every registered client is generated."""
    runner = CliRunner()
    output_dir = tmp_path / "out"

    result = runner.invoke(
        extract_config,
        ["--fixture", str(CANCUN_FIXTURE), "--output", str(output_dir)],
    )

    assert result.exit_code == 0, result.output
    for client_name in CLIENT_EXPORTERS:
        client_dir = output_dir / CANCUN_FIXTURE.stem / client_name
        assert client_dir.is_dir()
        assert any(client_dir.iterdir())


def test_cli_client_filter_generates_only_matching_client(
    tmp_path: Path,
) -> None:
    """`--client` restricts generation to clients matching the substring."""
    runner = CliRunner()
    output_dir = tmp_path / "out"

    result = runner.invoke(
        extract_config,
        [
            "--fixture",
            str(CANCUN_FIXTURE),
            "--output",
            str(output_dir),
            "--client",
            "besu",
        ],
    )

    assert result.exit_code == 0, result.output
    fixture_output = output_dir / CANCUN_FIXTURE.stem
    assert [p.name for p in fixture_output.iterdir()] == ["besu"]
