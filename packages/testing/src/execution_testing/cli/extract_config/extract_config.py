#!/usr/bin/env python
"""
CLI tool to generate client-native configuration files (chainspec/genesis.json)
for Ethereum clients directly from a filled EEST fixture.

Each client's genesis/chainspec format is reproduced in Python from its hive
`mapper.jq`-style transform (see `clients/`), so no Hive server or Docker
container is required.
"""

from pathlib import Path
from typing import Dict, Optional, Type

import click

from .clients.besu import BesuExportableGenesis
from .clients.geth import GethExportableGenesis
from .clients.nethermind import NethermindExportableGenesis
from .exportable_genesis import ExportableGenesis

CLIENT_EXPORTERS: Dict[str, Type[ExportableGenesis]] = {
    exporter.client_name: exporter
    for exporter in (
        BesuExportableGenesis,
        GethExportableGenesis,
        NethermindExportableGenesis,
    )
}


@click.command()
@click.option(
    "--client",
    "-c",
    required=False,
    default=None,
    help="Client name (e.g., go-ethereum, besu, nethermind)",
)
@click.option(
    "--fixture",
    "-f",
    type=click.Path(exists=True, path_type=Path),
    help="Path to a fixture JSON file or directory to use for genesis",
    default=None,
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    default="./extracted_configs",
    help="Output directory for generated files",
)
def extract_config(
    client: Optional[str],
    fixture: Optional[Path],
    output: Path,
) -> None:
    """
    Generate client-native configuration files for Ethereum clients.

    Builds each client's genesis/chainspec files directly from a filled
    EEST fixture's genesis block and pre-state, without spawning a client
    via Hive or Docker.
    """
    if not fixture:
        raise click.UsageError(
            "No fixture provided, use --fixture to specify a fixture"
        )

    if fixture.is_dir():
        fixture_files = list(fixture.glob("*.json"))
    elif fixture.is_file():
        fixture_files = [fixture]
    else:
        raise click.UsageError(f"Invalid fixture path: {fixture}")

    exporters = {
        name: exporter_cls
        for name, exporter_cls in CLIENT_EXPORTERS.items()
        if not client or client in name
    }
    if not exporters:
        raise click.UsageError(f"No client types found for {client}")

    output.mkdir(parents=True, exist_ok=True)

    for fixture_path in fixture_files:
        click.echo(f"Using fixture: {fixture_path}")

        for name, exporter_cls in exporters.items():
            try:
                genesis = exporter_cls.from_fixture(fixture_path)
            except ValueError as e:
                click.echo(f"✗ Skipping {name}: {e}", err=True)
                continue

            output_folder = output / fixture_path.stem / name
            for written_path in genesis.export_to_folder(output_folder):
                click.echo(f"✓ Wrote {written_path}")

        click.echo()


if __name__ == "__main__":
    extract_config()
