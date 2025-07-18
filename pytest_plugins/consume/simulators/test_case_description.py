"""Pytest fixtures that help create the test case "Description" displayed in the Hive UI."""

import logging
import textwrap
import urllib
import warnings
from typing import List

import pytest
from hive.client import ClientType

from ethereum_test_fixtures import BaseFixture
from ethereum_test_fixtures.consume import TestCaseIndexFile, TestCaseStream

from ...pytest_hive.hive_info import ClientFile, HiveInfo

logger = logging.getLogger(__name__)


@pytest.fixture(scope="function")
def hive_clients_yaml_target_filename() -> str:
    """Return the name of the target clients YAML file."""
    return "clients_eest.yaml"


@pytest.fixture(scope="function")
def hive_clients_yaml_generator_command(
    client_type: ClientType,
    client_file: ClientFile,
    hive_clients_yaml_target_filename: str,
    hive_info: HiveInfo,
) -> str:
    """Generate a shell command that creates a clients YAML file for the current client."""
    try:
        if not client_file:
            raise ValueError("No client information available - try updating hive")
        client_config = [c for c in client_file.root if c.client in client_type.name]
        if not client_config:
            raise ValueError(f"Client '{client_type.name}' not found in client file")
        try:
            yaml_content = ClientFile(root=[client_config[0]]).yaml().replace(" ", "&nbsp;")
            return f'echo "\\\n{yaml_content}" > {hive_clients_yaml_target_filename}'
        except Exception as e:
            raise ValueError(f"Failed to generate YAML: {str(e)}") from e
    except ValueError as e:
        error_message = str(e)
        warnings.warn(
            f"{error_message}. The Hive clients YAML generator command will not be available.",
            stacklevel=2,
        )

        issue_title = f"Client {client_type.name} configuration issue"
        issue_body = f"Error: {error_message}\nHive version: {hive_info.commit}\n"
        issue_url = f"https://github.com/ethereum/execution-spec-tests/issues/new?title={urllib.parse.quote(issue_title)}&body={urllib.parse.quote(issue_body)}"

        return (
            f"Error: {error_message}\n"
            f'Please <a href="{issue_url}">create an issue</a> to report this problem.'
        )


@pytest.fixture(scope="function")
def filtered_hive_options(hive_info: HiveInfo) -> List[str]:
    """Filter Hive command options to remove unwanted options."""
    logger.info("Hive info: %s", hive_info.command)

    unwanted_options = [
        "--client",  # gets overwritten: we specify a single client; the one from the test case
        "--client-file",  # gets overwritten: we'll write our own client file
        "--results-root",  # use default value instead (or you have to pass it to ./hiveview)
        "--sim.limit",  # gets overwritten: we only run the current test case id
        "--sim.parallelism",  # skip; we'll only be running a single test
    ]

    command_parts = []
    skip_next = False
    for part in hive_info.command:
        if skip_next:
            skip_next = False
            continue

        if part in unwanted_options:
            skip_next = True
            continue

        if any(part.startswith(f"{option}=") for option in unwanted_options):
            continue

        command_parts.append(part)

    return command_parts


@pytest.fixture(scope="function")
def hive_client_config_file_parameter(hive_clients_yaml_target_filename: str) -> str:
    """Return the hive client config file parameter."""
    return f"--client-file {hive_clients_yaml_target_filename}"


@pytest.fixture(scope="function")
def hive_consume_command(
    test_case: TestCaseIndexFile | TestCaseStream,
    hive_client_config_file_parameter: str,
    filtered_hive_options: List[str],
    client_type: ClientType,
) -> str:
    """Command to run the test within hive."""
    command_parts = filtered_hive_options.copy()
    command_parts.append(f"{hive_client_config_file_parameter}")
    command_parts.append(f"--client={client_type.name}")
    command_parts.append(f'--sim.limit="id:{test_case.id}"')

    return " ".join(command_parts)


@pytest.fixture(scope="function")
def hive_dev_command(
    client_type: ClientType,
    hive_client_config_file_parameter: str,
) -> str:
    """Return the command used to instantiate hive alongside the `consume` command."""
    return f"./hive --dev {hive_client_config_file_parameter} --client {client_type.name}"


@pytest.fixture(scope="function")
def eest_consume_command(
    test_suite_name: str,
    test_case: TestCaseIndexFile | TestCaseStream,
    fixture_source_flags: List[str],
) -> str:
    """Commands to run the test within EEST using a hive dev back-end."""
    flags = " ".join(fixture_source_flags)
    return (
        f"uv run consume {test_suite_name.split('-')[-1]} "
        f'{flags} --sim.limit="id:{test_case.id}" -v -s'
    )


@pytest.fixture(scope="function")
def test_case_description(
    fixture: BaseFixture,
    test_case: TestCaseIndexFile | TestCaseStream,
    hive_clients_yaml_generator_command: str,
    hive_consume_command: str,
    hive_dev_command: str,
    eest_consume_command: str,
) -> str:
    """Create the description of the current blockchain fixture test case."""
    test_url = fixture.info.get("url", "")

    if "description" not in fixture.info or fixture.info["description"] is None:
        test_docstring = "No documentation available."
    else:
        # this prefix was included in the fixture description field for fixtures <= v4.3.0
        test_docstring = fixture.info["description"].replace("Test function documentation:\n", "")  # type: ignore

    description = textwrap.dedent(f"""
        <b>Test Details</b>
        <code>{test_case.id}</code>
        {f'<a href="{test_url}">[source]</a>' if test_url else ""}

        {test_docstring}

        <b>Run This Test Locally:</b>
        To run this test in <a href="https://github.com/ethereum/hive">hive</a></i>:
        <code>{hive_clients_yaml_generator_command}
            {hive_consume_command}</code>

        <b>Advanced: Run the test against a hive developer backend using EEST's <code>consume</code> command</b>
        Create the client YAML file, as above, then:
        1. Start hive in dev mode: <code>{hive_dev_command}</code>
        2. In the EEST repository root: <code>{eest_consume_command}</code>
    """)  # noqa: E501

    description = description.strip()
    description = description.replace("\n", "<br/>")
    return description
