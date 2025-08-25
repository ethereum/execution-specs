"""Command to display EEST and system information."""

import platform
import subprocess
import sys

import click

from config.app import AppConfig
from ethereum_test_tools.utility.versioning import get_current_commit_hash_or_tag


def run_command(command: list[str]) -> str:
    """Run a CLI command and return its output."""
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except (subprocess.SubprocessError, FileNotFoundError):
        return "unknown"


def get_uv_version() -> str:
    """Get the installed uv package manager version."""
    return run_command(["uv", "--version"])


@click.command(name="info")
def info():
    """Display EEST and system information."""
    # Format headers
    title = click.style("EEST", fg="green", bold=True)

    version = AppConfig().version

    info_text = f"""
    {title} {click.style(f"v{version}", fg="blue", bold=True)}
{"─" * 50}

    Git commit: {click.style(get_current_commit_hash_or_tag(shorten_hash=True), fg="yellow")}
    Python: {click.style(platform.python_version(), fg="blue")}
    uv: {click.style(get_uv_version(), fg="magenta")}
    OS: {click.style(f"{platform.system()} {platform.release()}", fg="cyan")}
    Platform: {click.style(platform.machine(), fg="cyan")}
    Python Path: {click.style(sys.executable, dim=True)}
    """

    click.echo(info_text)
