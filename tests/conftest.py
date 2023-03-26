import os
import shutil
import tarfile
import tempfile
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
    "execution_spec_generated_tests": {
        "url": "https://github.com/ethereum/execution-spec-tests/releases/download/v0.2.3/fixtures.tar.gz",
    },
    "t8n_testdata": {
        "url": "https://github.com/gurukamath/t8n_testdata.git",
        "commit_hash": "6b6a0fe",
    },
    "ethereum_tests": {
        "url": "https://github.com/ethereum/tests.git",
        "commit_hash": "69c4c2a",
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
        repo.remotes.origin.fetch(branch.name)
        repo.git.checkout(commit_hash)

        repo.submodule_update(init=True, recursive=True)


def pytest_sessionstart(session: Session) -> None:

    fixtures_location = "tests/fixtures"

    if not os.path.exists(fixtures_location):
        os.mkdir(fixtures_location)

    for idx, props in test_fixtures.items():
        fixture_path = f"{fixtures_location}/{idx}"

        # Set the path of the various downloaded fixtures
        # as environment variables
        os.environ[idx.upper()] = fixture_path

        if "commit_hash" in props:
            git_clone_fixtures(
                props["url"], props["commit_hash"], fixture_path
            )
        else:
            download_fixtures(props["url"], fixture_path)
