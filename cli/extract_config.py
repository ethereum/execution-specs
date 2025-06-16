#!/usr/bin/env python
"""
CLI tool to extract client configuration files (chainspec/genesis.json) from Ethereum clients.

This tool spawns an Ethereum client using Hive and extracts the generated configuration
files such as /chainspec/test.json, /configs/test.cfg, or /genesis.json from the Docker container.
"""

import io
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple, cast

import click
from hive.simulation import Simulation
from hive.testing import HiveTestResult

from ethereum_test_base_types import Alloc, to_json
from ethereum_test_fixtures import BlockchainFixtureCommon
from ethereum_test_fixtures.blockchain import FixtureHeader
from ethereum_test_fixtures.file import Fixtures
from ethereum_test_fixtures.shared_alloc import SharedPreStateGroup
from ethereum_test_forks import Fork
from pytest_plugins.consume.hive_simulators.ruleset import ruleset


def get_docker_containers() -> set[str]:
    """Get the current list of Docker container IDs."""
    result = subprocess.run(["docker", "ps", "-q"], capture_output=True, text=True, check=True)
    return set(result.stdout.strip().split("\n")) if result.stdout.strip() else set()


def extract_client_files(
    container_id: str,
    output_dir: Path,
    fixture_name: str,
    client_name: str,
) -> Dict[str, Path]:
    """
    Extract configuration files from a running client container.

    Returns a dictionary mapping file type to extracted file path.
    """
    extracted_files = {}

    # List of files to try to extract
    files_to_extract = [
        ("/chainspec/test.json", "chainspec.json"),
        ("/configs/test.cfg", "config.cfg"),
        ("/genesis.json", "genesis.json"),
    ]

    for container_path, output_filename in files_to_extract:
        try:
            # Use docker exec to read the file from the container
            # First check if file exists
            check_cmd = ["docker", "exec", container_id, "test", "-f", container_path]
            check_result = subprocess.run(check_cmd, capture_output=True)

            if check_result.returncode == 0:
                # File exists, now read it
                read_cmd = ["docker", "exec", container_id, "cat", container_path]
                result = subprocess.run(read_cmd, capture_output=True, text=True)

                if result.returncode == 0 and result.stdout:
                    output_folder = output_dir / fixture_name / client_name
                    if not output_folder.exists():
                        output_folder.mkdir(parents=True)
                    output_path = output_folder / output_filename
                    output = result.stdout
                    if output_filename == "genesis.json":
                        # Indent the json
                        output = json.dumps(json.loads(output), indent=4)
                    output_path.write_text(output)
                    extracted_files[container_path] = output_path
                    click.echo(f"✓ Extracted {container_path} to {output_path}")
                else:
                    click.echo(f"✗ Failed to read {container_path}: {result.stderr}", err=True)
            else:
                click.echo(f"- File {container_path} does not exist in container")

        except Exception as e:
            click.echo(f"✗ Error extracting {container_path}: {e}", err=True)

    return extracted_files


def create_genesis_from_fixture(fixture_path: Path) -> Tuple[FixtureHeader, Alloc, int]:
    """Create a client genesis state from a fixture file."""
    genesis: FixtureHeader
    alloc: Alloc
    chain_id: int = 1
    with open(fixture_path, "r") as f:
        fixture_json = json.load(f)

    if "_info" in fixture_json:
        fixture = Fixtures.model_validate(fixture_json)
        # Load the fixture
        fixtures = Fixtures.model_validate_json(fixture_path.read_text())

        # Get the first fixture (assuming single fixture file)
        fixture_id = list(fixtures.keys())[0]
        fixture = fixtures[fixture_id]

        if not isinstance(fixture, BlockchainFixtureCommon):
            raise ValueError(f"Fixture {fixture_id} is not a blockchain fixture")

        genesis = fixture.genesis
        alloc = fixture.pre
        chain_id = int(fixture.config.chain_id)
    else:
        shared_alloc = SharedPreStateGroup.model_validate(fixture_json)
        genesis = shared_alloc.genesis  # type: ignore
        alloc = shared_alloc.pre

    return genesis, alloc, chain_id


def get_client_environment_for_fixture(fork: Fork, chain_id: int) -> dict:
    """Get the environment variables for starting a client with the given fixture."""
    if fork not in ruleset:
        raise ValueError(f"Fork '{fork}' not found in hive ruleset")

    return {
        "HIVE_CHAIN_ID": str(chain_id),
        "HIVE_FORK_DAO_VOTE": "1",
        "HIVE_NODETYPE": "full",
        "HIVE_CHECK_LIVE_PORT": "8545",  # Using RPC port for liveness check
        **{k: f"{v:d}" for k, v in ruleset[fork].items()},
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
    help="Path to a fixture JSON file to use for genesis",
    default=None,
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    default="./extracted_configs",
    help="Output directory for extracted files",
)
@click.option(
    "--hive-url",
    default="http://127.0.0.1:3000",
    help="Hive server URL",
)
@click.option(
    "--list-files",
    "-l",
    is_flag=True,
    help="List files in the container root before extraction",
)
def extract_config(
    client: str,
    fixture: Optional[Path],
    output: Path,
    hive_url: str,
    list_files: bool,
) -> None:
    """
    Extract client configuration files from Ethereum clients.

    This tool spawns an Ethereum client using Hive and extracts the generated
    configuration files such as /chainspec/test.json, /configs/test.cfg, or /genesis.json
    from the Docker container.
    """
    if not fixture:
        raise click.UsageError("No fixture provided, use --fixture to specify a fixture")

    if fixture.is_dir():
        fixture_files = list(fixture.glob("*.json"))
    elif fixture.is_file():
        fixture_files = [fixture]
    else:
        raise click.UsageError(f"Invalid fixture path: {fixture}")

    # Create output directory
    output.mkdir(parents=True, exist_ok=True)

    # Initialize Hive test
    simulation = Simulation(url=hive_url)
    suite = simulation.start_suite(
        name="extract-config",
        description="Extract client configuration files",
    )
    hive_test = suite.start_test(
        name="extract-config",
        description="Extract client configuration files",
    )

    client_types = []
    for client_type in simulation.client_types():
        if client and client not in client_type.name:
            continue
        client_types.append(client_type)

    if not client_types:
        raise click.UsageError(f"No client types found for {client}")

    for fixture_path in fixture_files:
        # Prepare client files and environment

        click.echo(f"Using fixture: {fixture_path}")

        # Load fixture and create genesis
        genesis, alloc, chain_id = create_genesis_from_fixture(fixture_path)
        fork = genesis.fork
        assert fork is not None
        client_environment = get_client_environment_for_fixture(fork, chain_id)

        genesis_json = to_json(genesis)
        alloc_json = to_json(alloc)
        genesis_json["alloc"] = {k.replace("0x", ""): v for k, v in alloc_json.items()}

        genesis_json_str = json.dumps(genesis_json)
        genesis_bytes = genesis_json_str.encode("utf-8")

        for client_type in client_types:
            client_files = {}
            client_files["/genesis.json"] = io.BufferedReader(
                cast(io.RawIOBase, io.BytesIO(genesis_bytes))
            )
            # Get containers before starting client
            containers_before = get_docker_containers()

            # Start the client
            click.echo(f"Starting client: {client_type.name}")
            client_instance = hive_test.start_client(
                client_type=client_type,
                environment=client_environment,
                files=client_files,
            )

            if not client_instance:
                click.echo("Failed to start client", err=True)
                sys.exit(1)

            try:
                # Get containers after starting client
                containers_after = get_docker_containers()
                new_containers = containers_after - containers_before

                if len(new_containers) != 1:
                    click.echo(
                        f"Expected exactly 1 new container, found {len(new_containers)}", err=True
                    )
                    sys.exit(1)

                container_id = new_containers.pop()
                click.echo(f"Client started successfully (Container ID: {container_id})")

                # Optionally list files in container
                if list_files:
                    click.echo("\nListing files in container root:")
                    list_cmd = ["docker", "exec", container_id, "ls", "-la", "/"]
                    result = subprocess.run(list_cmd, capture_output=True, text=True)
                    if result.returncode == 0:
                        click.echo(result.stdout)
                    else:
                        click.echo(f"Failed to list files: {result.stderr}", err=True)

                # Extract files
                click.echo("\nExtracting configuration files...")
                extract_client_files(container_id, output, fixture_path.stem, client_type.name)

            except Exception as e:
                click.echo(f"Error: {e}", err=True)
                import traceback

                traceback.print_exc()
                sys.exit(1)
            finally:
                # Clean up
                click.echo("\nStopping client...")
                client_instance.stop()

            click.echo()

    hive_test.end(result=HiveTestResult(test_pass=True, details=""))
    suite.end()


if __name__ == "__main__":
    extract_config()
