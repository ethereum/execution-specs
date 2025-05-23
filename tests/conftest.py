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

from tests.helpers import TEST_FIXTURES


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


def pytest_configure(config: Config) -> None:
    """
    Configure the ethereum module and log levels to output evm trace.
    """
    if config.getoption("optimized"):
        import ethereum_optimized

        ethereum_optimized.monkey_patch(None)


def download_fixtures(url: str, location: str) -> None:
    # xdist processes will all try to download the fixtures.

    version_file = os.path.join(location, "version.txt")

    # Using lockfile to make it parallel safe
    with SoftFileLock(f"{location}.lock"):

        current_version = url
        stored_version = None

        if os.path.exists(version_file):
            with open(version_file, "r") as vf:
                stored_version = vf.read().strip()

        if not os.path.exists(location) or stored_version != current_version:
            print(f"Downloading {location}...")

            with tempfile.TemporaryDirectory() as temp_dir:
                temp_file = os.path.join(temp_dir, "fixtures.tar.gz")
                with urllib.request.urlopen(url) as response, open(temp_file, "wb") as tfile:
                    shutil.copyfileobj(response, tfile)
                with tarfile.open(temp_file, mode="r:gz") as tar:
                    tar.extractall(temp_dir)

                if os.path.exists(location):
                    shutil.rmtree(location)

                os.makedirs(location, exist_ok=True)

                for item in os.listdir(temp_dir):
                    shutil.move(os.path.join(temp_dir, item), location)

            with open(version_file, "w") as f:
                f.write(url)
        else:
            print(f"{location} already available")


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
