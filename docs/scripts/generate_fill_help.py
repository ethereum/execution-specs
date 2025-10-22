#!/usr/bin/env python3
"""
Generate the fill command help output for documentation.

This script captures the output of 'fill --help' and generates a complete
documentation page that includes both static content and the auto-generated
help output. The generated page replaces the manual help output with
current command-line options.
"""

import logging
import subprocess
import sys
import textwrap

import mkdocs_gen_files

logger = logging.getLogger("mkdocs")


def get_fill_help_output() -> str:
    """Run 'fill --help' and capture its output."""
    try:
        result = subprocess.run(
            ["uv", "run", "fill", "--help"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running 'fill --help': {e}")
        logger.error(f"stderr: {e.stderr}")
        sys.exit(1)


def format_help_output(help_text: str, max_width: int = 88) -> str:
    """
    Format the help output with proper line wrapping.

    Args:
        help_text: The raw help output
        max_width: Maximum line width (default 88 to match existing docs)

    Returns:
        Formatted help text suitable for documentation

    """
    lines = help_text.splitlines()
    formatted_lines = []

    for line in lines:
        # Don't wrap lines that are part of the usage section or are empty
        if not line.strip() or line.startswith("usage:") or line.startswith("  ") and "--" in line:
            formatted_lines.append(line)
        else:
            # Wrap long lines while preserving indentation
            indent = len(line) - len(line.lstrip())
            if len(line) > max_width and indent == 0:
                wrapped = textwrap.fill(
                    line,
                    width=max_width,
                    subsequent_indent="  ",
                    break_long_words=False,
                    break_on_hyphens=False,
                )
                formatted_lines.append(wrapped)
            else:
                formatted_lines.append(line)

    return "\n".join(formatted_lines)


def generate_command_line_options_docs():
    """Generate a standalone page with just the fill command-line options."""
    # Get and format the help output
    help_output = get_fill_help_output()
    formatted_output = format_help_output(help_output)

    # Create the complete page content
    page_content = f"""# Fill Command-Line Options

Fill is a [pytest](https://docs.pytest.org/en/stable/)-based command. This page lists custom
options that the `fill` command provides. To see the full list of options that is available
to fill (including the standard pytest and plugin command-line options) use `fill --pytest-help`.

*This page is automatically generated from the current `fill --help` output.*

## Command Help Output

```text
{formatted_output}
```

---

*This page was automatically generated from `fill --help` output.*
"""

    # Write the generated content to a virtual file
    with mkdocs_gen_files.open("filling_tests/filling_tests_command_line_options.md", "w") as f:
        f.write(page_content)

    logger.info("Generated filling_tests_command_line_options.md with current fill --help output")


# Run the generation
generate_command_line_options_docs()
