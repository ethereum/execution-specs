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

    def get_xdist_worker_id(request_or_session: object) -> str:
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


class _FixturesDownloader:
    cache: Final[SQLiteCache]
    session: Final[CachedSession]
    root: Final[Path]
    keep_cache_keys: Final[Set[str]]

    def __init__(self, root: Path) -> None:
        self.root = root
        self.cache = SQLiteCache(use_cache_dir=True, db_path="eels_cache")
        self.session = requests_cache.CachedSession(
            backend=self.cache,
            ignored_parameters=["X-Amz-Signature", "X-Amz-Date"],
            expire_after=24 * 60 * 60,
            cache_control=True,
        )
        self.keep_cache_keys = set()

    def fetch_http(self, url: str, location: str) -> None:
        path = self.root.joinpath(location)
        print(f"Downloading {location}...")

        with self.session.get(url, stream=True) as response:
            if response.from_cache:
                print(f"Cache hit {url}")
            else:
                print(f"Cache miss {url} :(")

            # Track the cache keys we've hit this session so we don't delete
            # them.
            all_responses = [response] + response.history
            current_keys = set(
                self.cache.create_key(request=r.request) for r in all_responses
            )
            self.keep_cache_keys.update(current_keys)

            with tarfile.open(fileobj=response.raw, mode="r:gz") as tar:
                shutil.rmtree(path, ignore_errors=True)
                print(f"Extracting {location}...")
                tar.extractall(path)

    def fetch_git(self, url: str, location: str, commit_hash: str) -> None:
        path = self.root.joinpath(location)
        if not os.path.exists(path):
            print(f"Cloning {location}...")
            repo = git.Repo.clone_from(url, to_path=path)
        else:
            print(f"{location} already available.")
            repo = git.Repo(path)

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

    def __enter__(self) -> Self:
        assert not self.keep_cache_keys
        return self

    def __exit__(
        self, exc_type: object, exc_value: object, traceback: object
    ) -> None:
        cached = self.cache.filter(expired=True, invalid=True)
        to_delete = set(x.cache_key for x in cached) - self.keep_cache_keys
        if to_delete:
            print(f"Evicting {len(to_delete)} from HTTP cache")
            self.cache.delete(*to_delete, vacuum=True)
        self.keep_cache_keys.clear()


fixture_lock = StashKey[Optional[FileLock]]()


def pytest_sessionstart(session: Session) -> None:  # noqa: U100
    if get_xdist_worker_id(session) != "master":
        return

    lock_path = session.config.rootpath.joinpath("tests/fixtures/.lock")
    stash = session.stash
    lock_file = FileLock(str(lock_path), timeout=0)
    lock_file.acquire()

    assert fixture_lock not in stash
    stash[fixture_lock] = lock_file

    with _FixturesDownloader(session.config.rootpath) as downloader:
        for _, props in TEST_FIXTURES.items():
            fixture_path = props["fixture_path"]

            os.makedirs(os.path.dirname(fixture_path), exist_ok=True)

            if "commit_hash" in props:
                downloader.fetch_git(
                    props["url"], fixture_path, props["commit_hash"]
                )
            else:
                downloader.fetch_http(props["url"], fixture_path)


def pytest_sessionfinish(session: Session, exitstatus: int) -> None:
    if get_xdist_worker_id(session) != "master":
        return

    lock_file = session.stash[fixture_lock]
    session.stash[fixture_lock] = None

    assert lock_file is not None
    lock_file.release()
