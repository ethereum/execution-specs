import os
import shutil
import tarfile
from pathlib import Path
from typing import Final, Optional, Set

import git
import requests_cache
from _pytest.config import Config
from _pytest.config.argparsing import Parser
from filelock import FileLock
from git.exc import GitCommandError, InvalidGitRepositoryError
from pytest import Session, StashKey
from requests_cache import CachedSession
from requests_cache.backends.sqlite import SQLiteCache
from typing_extensions import Self

from tests.helpers import TEST_FIXTURES

try:
    from xdist import get_xdist_worker_id  # type: ignore[import-untyped]
except ImportError:

    def get_xdist_worker_id(request_or_session: object) -> str:  # noqa: U100
        del request_or_session
        return "master"


def pytest_addoption(parser: Parser) -> None:
    """
    Accept --evm-trace option in pytest.
    """
    parser.addoption(
        "--optimized",
        dest="optimized",
        default=False,
        action="store_const",
        const=True,
        help="Use optimized state and ethash",
    )

    parser.addoption(
        "--evm_trace",
        dest="evm_trace",
        default=False,
        action="store_const",
        const=True,
        help="Create an evm trace",
    )


def pytest_configure(config: Config) -> None:
    """
    Configure the ethereum module and log levels to output evm trace.
    """
    if config.getoption("optimized"):
        import ethereum_optimized

        ethereum_optimized.monkey_patch(None)

    if config.getoption("evm_trace"):
        import ethereum.trace
        from ethereum_spec_tools.evm_tools.t8n.evm_trace import (
            evm_trace as new_trace_function,
        )

        # Replace the function in the module
        ethereum.trace.set_evm_trace(new_trace_function)

