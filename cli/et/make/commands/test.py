"""
This module provides a CLI command to scaffold a test file.

The `test` command guides the user through a series of prompts to generate a test file
based on the selected test type, fork, EIP number, and EIP name. The generated test file
is saved in the appropriate directory with a rendered template using Jinja2.
"""

import os
import sys
from pathlib import Path

import click
import jinja2

from cli.input import input_select, input_text
from config.docs import DocsConfig
from ethereum_test_forks import get_development_forks, get_forks

template_loader = jinja2.PackageLoader("cli.et.make")
template_env = jinja2.Environment(
    loader=template_loader, keep_trailing_newline=True, trim_blocks=True, lstrip_blocks=True
)


@click.command()
def test():
    """
    Create a new specification test file for an EIP.

    This function guides the user through a series of prompts to generate a test file
    for Ethereum execution specifications. The user is prompted to select the type of test,
    the fork to use, and to provide the EIP number and name. Based on the inputs, a test file
    is created in the appropriate directory with a rendered template.

    Prompts:
    - Choose the type of test to generate (State or Blockchain)
    - Select the fork to use (Prague or Osaka)
    - Enter the EIP number
    - Enter the EIP name

    The generated test file is saved in the following format:
    `tests/{fork}/eip{eip_number}_{eip_name}/test_{eip_name}.py`

    Example:
    If the user selects "State" as the test type, "Prague" as the fork,
    enters "1234" as the EIP number,
    and "Sample EIP" as the EIP name, the generated file will be:
    `tests/prague/eip1234_sample_eip/test_sample_eip.py`

    The function uses Jinja2 templates to render the content of the test file.

    Raises:
    - FileNotFoundError: If the template file does not exist.
    - IOError: If there is an error writing the file.
    """
    test_type = input_select(
        "Choose the type of test to generate", choices=["State", "Blockchain"]
    )

    fork_choices = [str(fork) for fork in get_forks()]
    fork = input_select(
        "Select the fork where this functionality was introduced", choices=fork_choices
    )

    eip_number = input_text("Enter the EIP number").strip()

    # TODO: Perhaps get the EIP name from the number using an API?
    eip_name = input_text("Enter the EIP name").strip()

    test_name = eip_name.lower().replace(" ", "_")

    file_name = f"test_{test_name}.py"

    directory_path = Path("tests") / fork.lower() / f"eip{eip_number}_{test_name}"

    file_path = directory_path / file_name

    if file_path.exists():
        click.echo(
            click.style(f"\n 🛑 The target test module {file_path} already exists!", fg="red"),
            err=True,
        )
        sys.exit(1)

    # Create directories if they don't exist
    os.makedirs(directory_path, exist_ok=True)

    template = template_env.get_template(f"{test_type.lower()}_test.py.j2")
    rendered_template = template.render(
        fork=fork,
        eip_number=eip_number,
        eip_name=eip_name,
        test_name=test_name,
    )

    with open(file_path, "w") as file:
        file.write(rendered_template)

    click.echo(
        click.style(
            f"\n 🎉 Success! Test file created at: {file_path}",
            fg="green",
        )
    )

    fork_option = ""
    if fork in [dev_fork.name() for dev_fork in get_development_forks()]:
        fork_option = f" --until={fork}"

    click.echo(
        click.style(
            f"\n 📝 Get started with tests:  {DocsConfig().DOCS_URL__WRITING_TESTS}"
            f"\n ⛽ To fill this test, run: `uv run fill {file_path}{fork_option}`",
            fg="cyan",
        )
    )
