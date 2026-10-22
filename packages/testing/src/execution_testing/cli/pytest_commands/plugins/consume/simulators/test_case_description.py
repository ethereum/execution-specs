"""
Pytest fixtures that help create the test case "Description" displayed in the
Hive UI, and the steps to reproduce a failed test.
"""

import logging
import urllib.parse
import warnings
from typing import List

import pytest
from hive.client import ClientType

from execution_testing.fixtures import BaseFixture
from execution_testing.fixtures.consume import (
    TestCaseIndexFile,
    TestCaseStream,
)

from ...pytest_hive.hive_info import ClientFile, HiveInfo

logger = logging.getLogger(__name__)

HIVE_DEV_MODE_DOCS_URL = (
    "https://steel.ethereum.foundation/docs/execution-specs/"
    "running_tests/hive/dev_mode/"
)
"""Docs page on running a simulator against a hive developer backend."""


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
    """
    Generate a shell command that creates a clients YAML file for the current
    client.
    """
    try:
        if not client_file:
            raise ValueError(
                "No client information available - try updating hive"
            )
        client_config = [
            c for c in client_file.root if c.client in client_type.name
        ]
        if not client_config:
            raise ValueError(
                f"Client '{client_type.name}' not found in client file"
            )
        try:
            yaml_content = ClientFile(root=[client_config[0]]).yaml()
        except Exception as e:
            raise ValueError(f"Failed to generate YAML: {str(e)}") from e
        target = hive_clients_yaml_target_filename
        return f"cat > {target} << 'EOF'\n{yaml_content}EOF"
    except ValueError as e:
        error_message = str(e)
        warnings.warn(
            f"{error_message}. The Hive clients YAML generator command will "
            "not be available.",
            stacklevel=2,
        )

        issue_title = f"Client {client_type.name} configuration issue"
        issue_body = (
            f"Error: {error_message}\nHive version: {hive_info.commit}\n"
        )
        issue_url = (
            "https://github.com/ethereum/execution-specs/issues/new"
            f"?title={urllib.parse.quote(issue_title)}"
            f"&body={urllib.parse.quote(issue_body)}"
        )
        return (
            f"# Error: {error_message}\n"
            f"# Please report this problem: {issue_url}"
        )


@pytest.fixture(scope="function")
def filtered_hive_options(hive_info: HiveInfo) -> List[str]:
    """Filter Hive command options to remove unwanted options."""
    logger.info("Hive info: %s", hive_info.command)

    unwanted_options = [
        "--client",  # gets overwritten: we specify a single client; the one
        # from the test case
        "--client-file",  # gets overwritten: we'll write our own client file
        "--results-root",  # use default value instead (or you have to pass it
        # to ./hiveview)
        "--sim.limit",  # gets overwritten: we only run the current test case
        # id
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
def hive_client_config_file_parameter(
    hive_clients_yaml_target_filename: str,
) -> str:
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
    """
    Return the command used to instantiate hive alongside the `consume`
    command.
    """
    return (
        f"./hive --dev {hive_client_config_file_parameter} "
        f"--client {client_type.name}"
    )


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
) -> str:
    """
    Create the description of the current blockchain fixture test case.

    Hive stores the description of every test in the run's result file, so
    it holds only what identifies the test. The steps to reproduce the
    test go into the details of failed tests instead, see
    `test_case_reproduction`.
    """
    test_url = fixture.info.get("url", "")

    if (
        "description" not in fixture.info
        or fixture.info["description"] is None
    ):
        test_docstring = "No documentation available."
    else:
        # this prefix was included in the fixture description field for
        # fixtures <= v4.3.0
        test_docstring = fixture.info["description"].replace(  # type: ignore
            "Test function documentation:\n", ""
        )

    source_link = f' <a href="{test_url}">[source]</a>' if test_url else ""
    lines = [
        "<b>Test Details</b>",
        f"<code>{test_case.id}</code>{source_link}",
        "",
        test_docstring.strip(),
    ]
    return "<br/>".join(lines).replace("\n", "<br/>")


@pytest.fixture(scope="function")
def test_case_reproduction(
    hive_clients_yaml_generator_command: str,
    hive_consume_command: str,
    hive_dev_command: str,
    eest_consume_command: str,
) -> str:
    """
    Return plain-text steps to reproduce the current test locally.

    The hive plugin appends them to the details of a failed test only, which
    hive stores in the run's test details log rather than in the result
    file.
    """
    return "\n".join(
        [
            "# Reproduce this test locally",
            "",
            "## Run the test in hive (https://github.com/ethereum/hive)",
            "",
            hive_clients_yaml_generator_command,
            hive_consume_command,
            "",
            "## Or debug it with the simulator's consume command against a "
            "hive developer backend",
            "",
            f"See {HIVE_DEV_MODE_DOCS_URL}",
            "1. Create the client file, as above.",
            f"2. Start hive in dev mode: {hive_dev_command}",
            "3. In the execution-specs repository root: "
            f"{eest_consume_command}",
        ]
    )
