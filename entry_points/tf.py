"""
Define an entry point wrapper for the now-deprecated tf command-line tool that
advises users to use the new `fill` tool.
"""

import sys


def main():  # noqa: D103
    print(
        "The `tf` command-line tool has been superseded by `fill`, please "
        "see the docs for help running `fill`:\n"
        "https://ethereum.github.io/execution-spec-tests/getting_started/executing_tests_command_line/"  # noqa: E501
    )
    sys.exit(1)


if __name__ == "__main__":
    main()
