"""
Provides a CLI command to scaffold a test file.

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

template_loader = jinja2.PackageLoader("cli.eest.make")
template_env = jinja2.Environment(
    loader=template_loader, keep_trailing_newline=True, trim_blocks=True, lstrip_blocks=True
)


@click.command(
    short_help="Generate a new test file for an EIP.",
    epilog=f"Further help: {DocsConfig().DOCS_URL__WRITING_TESTS}",
)
def test():
    """
    Generate a new test file for an EIP.

    This function guides the user through a series of prompts to generate a test file
    for Ethereum execution specifications. The user is prompted to select the type of test,
    the fork to use, and to provide the EIP number and name. Based on the inputs, a test file
    is created in the appropriate directory with a rendered template.

    Example:
        uv run eest make test

    \f
    <figure class="video_container">
        <video controls="true" allowfullscreen="true">
            <source
                src="/execution-spec-tests/writing_tests/img/eest_make_test.mp4"
                type="video/mp4"
            />
        </video>
    </figure>

    """  # noqa: D301
    test_type = input_select(
        "Choose the type of test to generate", choices=["State", "Blockchain"]
    )

    fork_choices = [str(fork) for fork in get_forks()]
    fork = input_select("Select the fork", choices=fork_choices)

    base_path = Path("tests") / fork.lower()
    base_path.mkdir(parents=True, exist_ok=True)

    existing_dirs = [d.name for d in base_path.iterdir() if d.is_dir() and d.name != "__pycache__"]

    location_choice = input_select(
        "Select test directory",
        choices=[
            {"name": "Use current location", "value": "current"},
            *existing_dirs,
            {"name": "** Create new sub-directory **", "value": "new"},
        ],
    )

    if location_choice == "new":
        eip_number = input_text("Enter the EIP number (int)").strip()
        eip_name = input_text("Enter the EIP name (spaces ok, only used in docstrings)").strip()
        directory_name = input_text(
            "Enter directory name (snake_case, part after eipXXXX_)"
        ).strip()
        dir_name = f"eip{eip_number}_{directory_name}"
        directory_path = base_path / dir_name
        raw_module = input_text("Enter module name (snake_case)").strip()
        module_name = raw_module if raw_module.startswith("test_") else f"test_{raw_module}"
    elif location_choice == "current":
        eip_number = input_text("Enter the EIP number (int)").strip()
        eip_name = input_text("Enter the EIP name (spaces ok, only used in docstrings)").strip()
        raw_module = input_text("Enter module name (snake_case)").strip()
        module_name = raw_module if raw_module.startswith("test_") else f"test_{raw_module}"
        directory_path = base_path
    else:
        dir_parts = location_choice.split("_")
        eip_number = dir_parts[0][3:]
        eip_name = " ".join(dir_parts[1:]).title()
        raw_module = input_text("Enter module name (snake_case)").strip()
        module_name = raw_module if raw_module.startswith("test_") else f"test_{raw_module}"
        directory_path = base_path / location_choice

    file_name = f"{module_name}.py"
    module_path = directory_path / file_name

    if module_path.exists():
        click.echo(
            click.style(
                f"\n 🛑 The target test module {module_path} already exists!",
                fg="red",
            ),
            err=True,
        )
        sys.exit(1)

    os.makedirs(directory_path, exist_ok=True)

    template = template_env.get_template(f"{test_type.lower()}_test.py.j2")
    rendered_template = template.render(
        fork=fork,
        eip_number=eip_number,
        eip_name=eip_name,
        module_name=module_name,
    )

    with open(module_path, "w") as file:
        file.write(rendered_template)

    click.echo(
        click.style(
            f"\n 🎉 Success! Test file created at: {module_path}",
            fg="green",
        )
    )

    fork_option = ""
    if fork in [dev_fork.name() for dev_fork in get_development_forks()]:
        fork_option = f" --until={fork}"

    click.echo(
        click.style(
            f"\n 📝 Get started with tests:  {DocsConfig().DOCS_URL__WRITING_TESTS}"
            f"\n ⛽ To fill this test, run: `uv run fill {module_path}{fork_option}`",
            fg="cyan",
        )
    )
