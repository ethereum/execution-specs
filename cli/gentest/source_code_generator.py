"""
Pytest source code generator.

This module maps a test provider instance to pytest source code.
"""

import subprocess
import sys
import tempfile
from pathlib import Path

import jinja2

from .test_context_providers import Provider

template_loader = jinja2.PackageLoader("cli.gentest")
template_env = jinja2.Environment(loader=template_loader, keep_trailing_newline=True)

# This filter maps python objects to string
template_env.filters["stringify"] = lambda input: repr(input)


# generates a formatted pytest source code by writing provided data on a given template.
def get_test_source(provider: Provider, template_path: str) -> str:
    """
    Generates formatted pytest source code by rendering a template with provided data.

    This function uses the given template path to create a pytest-compatible source
    code string. It retrieves context data from the specified provider and applies
    it to the template.

    Args:
        provider: An object that provides the necessary context for rendering the template.
        template_path (str): The path to the Jinja2 template file used to generate tests.

    Returns:
        str: The formatted pytest source code.
    """
    template = template_env.get_template(template_path)
    rendered_template = template.render(provider.get_context())
    # return rendered_template
    return format_code(rendered_template)


def format_code(code: str) -> str:
    """
    Formats the provided Python code using the Black code formatter.

    This function writes the given code to a temporary Python file, formats it using
    the Black formatter, and returns the formatted code as a string.

    Args:
        code (str): The Python code to be formatted.

    Returns:
        str: The formatted Python code.
    """
    # Create a temporary python file
    with tempfile.NamedTemporaryFile(suffix=".py") as temp_file:
        # Write the code to the temporary file
        temp_file.write(code.encode("utf-8"))
        # Ensure the file is written
        temp_file.flush()

        # Create a Path object for the input file
        input_file_path = Path(temp_file.name)

        # Get the path to the black executable in the virtual environment
        if sys.platform.startswith("win"):
            black_path = Path(sys.prefix) / "Scripts" / "black.exe"
        else:
            black_path = Path(sys.prefix) / "bin" / "black"

        # Call black to format the file
        config_path = Path(sys.prefix).parent / "pyproject.toml"

        subprocess.run(
            [str(black_path), str(input_file_path), "--quiet", "--config", str(config_path)],
            check=True,
        )

        # Return the formatted source code
        return input_file_path.read_text()
