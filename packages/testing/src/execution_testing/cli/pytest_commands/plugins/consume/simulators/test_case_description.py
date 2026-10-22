"""
Pytest fixtures that help create the test case "Description" displayed in the
Hive UI.
"""

import logging
from typing import List

import pytest
from hive.client import ClientType

from execution_testing.fixtures import BaseFixture
from execution_testing.fixtures.consume import (
    TestCaseIndexFile,
    TestCaseStream,
)

from ...pytest_hive.hive_info import HiveInfo

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
def test_case_description(
    fixture: BaseFixture,
    test_case: TestCaseIndexFile | TestCaseStream,
    hive_clients_yaml_target_filename: str,
    hive_consume_command: str,
) -> str:
    """
    Create the description of the current blockchain fixture test case.

    The description is kept short because hive stores it for every test
    in the run's result file. The client file and the hive command of the
    whole run are in the result file's run metadata, so only the command
    that runs this test is repeated here.
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
        "",
        "<b>Run This Test Locally:</b>",
        "Save the run's client file as "
        f"<code>{hive_clients_yaml_target_filename}</code>, then run in "
        '<a href="https://github.com/ethereum/hive">hive</a>:',
        f"<code>{hive_consume_command}</code>",
        "To debug it with the simulator's <code>consume</code> command "
        f'instead, see <a href="{HIVE_DEV_MODE_DOCS_URL}">'
        "Hive Development Mode</a>.",
    ]
    return "<br/>".join(lines).replace("\n", "<br/>")
