import os
import shutil
import tarfile
import tempfile
import urllib.request

import git
from _pytest.config import Config
from _pytest.config.argparsing import Parser
from filelock import SoftFileLock
from git.exc import GitCommandError, InvalidGitRepositoryError
from pytest import Session

import ethereum
from ethereum import trace
from ethereum_spec_tools.evm_trace import (
    capture_evm_stop,
    capture_gas_and_refund,
    capture_op_end,
    capture_op_exception,
    capture_op_start,
    capture_precompile_end,
    capture_precompile_start,
    capture_tx_end,
    output_traces,
)
from tests.helpers import TEST_FIXTURES


def pytest_addoption(parser: Parser) -> None:
    """
    Accept --evm-trace option in pytest.
    """
    parser.addoption(
        "--evm-trace",
        dest="vmtrace",
        default=1,
        action="store_const",
        const=10,
        help="Run trace",
    )
    parser.addoption(
        "--optimized",
        dest="optimized",
        default=False,
        action="store_const",
        const=True,
        help="Use optimized state and ethash",
    )


def pytest_configure(config: Config) -> None:
    """
    Configure the ethereum module and log levels to output evm trace.
    """
    if config.getoption("vmtrace", default=1) == 10:
        trace.capture_op_start = capture_op_start
        trace.capture_op_end = capture_op_end
        trace.capture_op_exception = capture_op_exception
        trace.capture_gas_and_refund = capture_gas_and_refund
        trace.capture_tx_end = capture_tx_end
        trace.output_traces = output_traces
        trace.capture_evm_stop = capture_evm_stop
        trace.capture_precompile_start = capture_precompile_start
        trace.capture_precompile_end = capture_precompile_end
        # config.option.__dict__["log_cli_level"] = "10"
        # config.option.__dict__["log_format"] = "%(message)s"
        # setattr(ethereum, "evm_trace", evm_trace)
    if config.getoption("optimized"):
        import ethereum_optimized

        ethereum_optimized.monkey_patch(None)


def download_fixtures(url: str, location: str) -> None:

    # xdist processes will all try to download the fixtures.
    # Using lockfile to make it parallel safe
    with SoftFileLock(f"{location}.lock"):
        if not os.path.exists(location):
            print(f"Downloading {location}...")
            with tempfile.TemporaryFile() as tfile:
                with urllib.request.urlopen(url) as response:
                    shutil.copyfileobj(response, tfile)

                tfile.seek(0)

                with tarfile.open(fileobj=tfile, mode="r:gz") as tar:
                    tar.extractall(location)
        else:
            print(f"{location} already available.")


def git_clone_fixtures(url: str, commit_hash: str, location: str) -> None:

    # xdist processes will all try to download the fixtures.
    # Using lockfile to make it parallel safe
    with SoftFileLock(f"{location}.lock"):
        if not os.path.exists(location):
            print(f"Cloning {location}...")
            repo = git.Repo.clone_from(url, to_path=location)
        else:
            print(f"{location} already available.")
            repo = git.Repo(location)

        print(f"Checking out the correct commit {commit_hash}...")
        branch = repo.heads["develop"]
        # Try to checkout the relevant commit hash and if that fails
        # fetch the latest changes and checkout the commit hash
        try:
            repo.git.checkout(commit_hash)
        except GitCommandError:
            repo.remotes.origin.fetch(branch.name)
            repo.git.checkout(commit_hash)

        # Check if the submodule head matches the parent commit
        # If not, update the submodule
        for submodule in repo.submodules:
            # Initialize the submodule if not already initialized
            try:
                submodule_repo = submodule.module()
            except InvalidGitRepositoryError:
                submodule.update(init=True, recursive=True)
                continue

            # Commit expected by the parent repo
            parent_commit = submodule.hexsha

            # Actual submodule head
            submodule_head = submodule_repo.head.commit.hexsha
            if parent_commit != submodule_head:
                submodule.update(init=True, recursive=True)


def pytest_sessionstart(session: Session) -> None:

    fixtures_location = "tests"

    for _, props in TEST_FIXTURES.items():
        fixture_path = props["fixture_path"]

        try:
            os.makedirs(os.path.dirname(fixture_path))
        except FileExistsError:
            pass

        if "commit_hash" in props:
            git_clone_fixtures(
                props["url"], props["commit_hash"], fixture_path
            )
        else:
            download_fixtures(props["url"], fixture_path)
