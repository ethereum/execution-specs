"""
CLI commands for managing the environment file.
"""

import click
from jinja2 import Environment, PackageLoader

from cli.eest.quotes import get_quote
from config.env import ENV_PATH, Config


@click.command(short_help="Generate the default environment file (env.yaml).", name="env")
def create_default_env():
    """
    A CLI command to generate the default environment file (env.yaml).

    If an `env.yaml` already exists, this command will NOT override it.
    In that case, it is recommended to manually make changes.

    _Easter egg: Shows a random quote after creating the environment file._

    Example:

        uv run eest make env

    Output:

        🎉 Success! Environment file created at: <path>/env.yaml

        🚀 Well begun is half done. - Aristotle
    """
    # Check if the env file already exists
    if ENV_PATH.exists():
        click.echo(
            click.style(
                f"🚧 The env file '{ENV_PATH}' already exists. "
                "Please update it manually if needed.",
                fg="red",
            )
        )
        exit(1)

    template_environment = Environment(
        loader=PackageLoader("config"), trim_blocks=True, lstrip_blocks=True
    )
    template = template_environment.get_template("env.yaml.j2")

    env_yaml = template.render(config=Config())

    with ENV_PATH.open("w") as file:
        file.write(env_yaml)
        click.echo(click.style(f"🎉 Success! Environment file created at: {ENV_PATH}", fg="green"))
        click.echo(get_quote())
