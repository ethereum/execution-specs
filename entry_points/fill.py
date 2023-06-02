"""
Define an entry point wrapper for pytest.
"""

import sys

import pytest


def main():  # noqa: D103
    pytest.main(sys.argv[1:])


if __name__ == "__main__":
    main()
