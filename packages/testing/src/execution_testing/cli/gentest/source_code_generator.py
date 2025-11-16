"""
Pytest source code generator.

This module maps a test provider instance to pytest source code.
"""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import jinja2

from execution_testing.config import AppConfig

from .test_context_providers import Provider

template_loader = jinja2.PackageLoader("execution_testing.cli.gentest")
template_env = jinja2.Environment(
    loader=template_loader, keep_trailing_newline=True
)

# This filter maps python objects to string
template_env.filters["stringify"] = lambda value: repr(value)


# generates a formatted pytest source code by writing provided data on a given
# template.
def get_test_source(provider: Provider, template_path: str) -> str:
    """
    Generate formatted pytest source code by rendering a template with provided
    data.

    This function uses the given template path to create a pytest-compatible
    source code string. It retrieves context data from the specified provider
    and applies it to the template.

    Args:
      provider: An object that provides the necessary context for rendering
                the template.
      template_path (str): The path to the Jinja2 template file
                           used to generate tests.

    Returns:
        str: The formatted pytest source code.

    """
    template = template_env.get_template(template_path)
    rendered_template = template.render(provider.get_context())
    # return rendered_template
    return format_code(rendered_template)


def format_code(code: str) -> str:
    """
    Format the provided Python code using ruff formatter.

    This function writes the given code to a temporary Python file, formats it
    using ruff if available, and returns the formatted (or original) code as a string.
    If ruff is not available, the code is returned unformatted.

    Args:
      code (str): The Python code to be formatted.

    Returns:
      str: The formatted Python code (or original if ruff is not available).

    """
    # Get the path to the formatter executable in the virtual environment
    if sys.platform.startswith("win"):
        formatter_path = Path(sys.prefix) / "Scripts" / "ruff.exe"
    else:
        formatter_path = Path(sys.prefix) / "bin" / "ruff"

    # Check if ruff is available
    if not formatter_path.exists():
        # Try to find ruff in PATH
        ruff_in_path = shutil.which("ruff")
        if ruff_in_path is None:
            # Ruff is not available, return code unformatted
            return code
        formatter_path = Path(ruff_in_path)

    # Create a temporary python file
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_file:
        # Write the code to the temporary file
        temp_file.write(code.encode("utf-8"))
        # Ensure the file is written
        temp_file.flush()

        # Create a Path object for the input file
        input_file_path = Path(temp_file.name)

    # Call ruff to format the file
    config_path = AppConfig().ROOT_DIR.parent / "pyproject.toml"

    try:
        subprocess.run(
            [
                str(formatter_path),
                "format",
                str(input_file_path),
                "--quiet",
                "--config",
                str(config_path),
            ],
            check=True,
            capture_output=True,
        )
        # Read the formatted source code
        formatted_code = input_file_path.read_text()
    except (subprocess.CalledProcessError, FileNotFoundError):
        # If formatting fails or ruff is not found, return original code
        formatted_code = code
    finally:
        # Clean up the temporary file
        try:
            input_file_path.unlink()
        except OSError:
            pass

    return formatted_code
