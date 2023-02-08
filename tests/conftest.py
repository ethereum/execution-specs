import os
import tarfile
import time
import urllib.request

import git
from _pytest.config import Config
from _pytest.config.argparsing import Parser
from filelock import SoftFileLock
from pytest import Session

import ethereum
from ethereum_spec_tools.evm_trace import evm_trace

# Update the links and commit has in order to consume
# newer/other tests
test_fixtures = {
    "execution-spec-generated-tests": {
        "url": "https://github.com/ethereum/execution-spec-tests/releases/download/v0.2.1/fixtures.tar.gz",
    },
    "fixtures": {
        "url": "https://github.com/ethereum/tests.git",
        "commit_hash": "afba21c63bcfb9b1ba3bd7cc1db95aef9452384e",
    },
}


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
        config.option.__dict__["log_cli_level"] = "10"
        config.option.__dict__["log_format"] = "%(message)s"
        setattr(ethereum, "evm_trace", evm_trace)
    if config.getoption("optimized"):
        import ethereum_optimized

        ethereum_optimized.monkey_patch(None)


def download_fixtures(url: str, location: str) -> None:

    # xdist processes will all try to download the fixtures.
    # Using lockfile to make ir parallel safe
    with SoftFileLock(f"{location}.lock"):

        try:
            if not os.path.exists(location):

                print(f"Downloading {location}...")
                urllib.request.urlretrieve(url, "temp.tar.gz")

                with tarfile.open("temp.tar.gz", "r:gz") as tar:
                    tar.extractall(location)

                os.remove("temp.tar.gz")
            else:
                print(f"{location} already available.")

        finally:
            # Prevent stale lock files in
            # the event of a crash
            os.remove(f"{location}.lock")


def git_clone_fixtures(url: str, commit_hash: str, location: str) -> None:

    # xdist processes will all try to download the fixtures.
    # Using lockfile to make ir parallel safe
    with SoftFileLock(f"{location}.lock"):

        try:
            if not os.path.exists(location):
                print(f"Cloning {location}...")
                repo = git.Repo.clone_from(url, to_path=location)
            else:
                print(f"{location} already available.")
                repo = git.Repo(location)

            print(f"Checking out the correct commit {commit_hash}...")
            branch = repo.heads["develop"]
            repo.remotes.origin.pull(branch.name)
            repo.git.checkout(commit_hash)

            repo.submodule_update(init=True, recursive=True)

        finally:
            # Prevent stale lock files in
            # the event of a crash
            os.remove(f"{location}.lock")


def pytest_sessionstart(session: Session) -> None:

    fixtures_location = "tests"

    for idx, props in test_fixtures.items():
        fixture_path = f"{fixtures_location}/{idx}"

        if "commit_hash" in props:
            git_clone_fixtures(
                props["url"], props["commit_hash"], fixture_path
            )
        else:
            download_fixtures(props["url"], fixture_path)
