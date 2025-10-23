"""Pytest configuration for the json infra tests."""

import json
import os
import shutil
import tarfile
from glob import glob
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    Final,
    Generator,
    List,
    Optional,
    Self,
    Set,
    Type,
)

import git
import pytest
import requests_cache
from _pytest.config import Config
from _pytest.config.argparsing import Parser
from _pytest.nodes import Item
from filelock import FileLock
from git.exc import GitCommandError, InvalidGitRepositoryError
from pytest import Collector, File, Session, StashKey, fixture
from requests_cache import CachedSession
from requests_cache.backends.sqlite import SQLiteCache

from ethereum_spec_tools.evm_tools.statetest import TestCase as StateTestCase
from ethereum_spec_tools.evm_tools.statetest import (
    read_test_case as read_state_test_case,
)

from . import FORKS, TEST_FIXTURES
from .helpers.exceptional_test_patterns import (
    exceptional_blockchain_test_patterns,
    exceptional_state_test_patterns,
)
from .helpers.load_blockchain_tests import Load, run_blockchain_st_test
from .helpers.load_state_tests import run_state_test

try:
    from xdist import get_xdist_worker_id
except ImportError:

    def get_xdist_worker_id(request_or_session: object) -> str:
        """Fallback implementation when xdist is not available."""
        del request_or_session
        return "master"


@fixture()
def root_relative() -> Callable[[str | Path], Path]:
    """
    A fixture that provides a function to resolve a path relative to
    `conftest.py`.
    """

    def _(path: str | Path) -> Path:
        return Path(__file__).parent / path

    return _


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

    parser.addoption(
        "--fork",
        dest="fork",
        type=str,
        help="Run tests for this fork only (e.g., --fork Osaka)",
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
        from ethereum_spec_tools.evm_tools.t8n.evm_trace.eip3155 import (
            Eip3155Tracer,
        )

        # Replace the function in the module
        ethereum.trace.set_evm_trace(Eip3155Tracer())


def pytest_collection_modifyitems(config: Config, items: list[Item]) -> None:
    """Filter test items based on the specified fork option."""
    desired_fork = config.getoption("fork", None)
    if not desired_fork:
        return

    selected = []
    deselected = []

    for item in items:
        forks_of_test = [m.args[0] for m in item.iter_markers(name="fork")]
        if forks_of_test and desired_fork not in forks_of_test:
            deselected.append(item)
        # Check if the test has a vm test marker
        elif any(item.iter_markers(name="vm_test")):
            callspec = getattr(item, "callspec", None)
            if not callspec or "fork" not in getattr(callspec, "params", {}):
                # no fork param on this test. We keep the test
                selected.append(item)
                continue
            fork_param = callspec.params["fork"]
            if fork_param[0] == desired_fork:
                selected.append(item)
            else:
                deselected.append(item)
        else:
            selected.append(item)

    if deselected:
        config.hook.pytest_deselected(items=deselected)
        items[:] = selected  # keep only what matches


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
        # Try to checkout the relevant commit hash and if that fails
        # fetch the latest changes and checkout the commit hash
        last_exception = None
        try:
            repo.git.checkout(commit_hash)
        except GitCommandError as e:
            last_exception = e
            for head in repo.heads:
                repo.remotes.origin.fetch(head.name)
                try:
                    repo.git.checkout(commit_hash)
                    last_exception = None
                    break
                except GitCommandError as e:
                    last_exception = e

            if last_exception:
                raise last_exception from None

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
        del exc_type, exc_value, traceback
        cached = self.cache.filter(expired=True, invalid=True)
        to_delete = set(x.cache_key for x in cached) - self.keep_cache_keys
        if to_delete:
            print(f"Evicting {len(to_delete)} from HTTP cache")
            self.cache.delete(*to_delete, vacuum=True)
        self.keep_cache_keys.clear()


fixture_lock = StashKey[Optional[FileLock]]()


def pytest_sessionstart(session: Session) -> None:
    """Initialize test fixtures and file locking at session start."""
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
                downloader.fetch_http(
                    props["url"],
                    fixture_path,
                )

            # Remove any python files in the downloaded files to avoid
            # importing them.
            for python_file in glob(
                os.path.join(fixture_path, "**/*.py"), recursive=True
            ):
                os.unlink(python_file)


def pytest_sessionfinish(session: Session, exitstatus: int) -> None:
    """Clean up file locks at session finish."""
    del exitstatus
    if get_xdist_worker_id(session) != "master":
        return

    lock_file = session.stash[fixture_lock]
    session.stash[fixture_lock] = None

    assert lock_file is not None
    lock_file.release()


def pytest_collect_file(
    file_path: Path, parent: Collector
) -> Collector | None:
    """
    Pytest hook that collects test cases from fixture JSON files.
    """
    if file_path.suffix == ".json":
        return FixturesFile.from_parent(parent, path=file_path)
    return None


class Fixture:
    """Single fixture from a JSON file."""

    @classmethod
    def is_format(cls, obj: object) -> bool:
        """Return true if the object can be parsed as the fixture type."""
        raise NotImplementedError("Not implemented.")

    @classmethod
    def collect(
        cls, file_path: str, key: str, obj: Dict[str, Any]
    ) -> Generator[Item, None, None]:
        """Collect tests from a single fixture dictionary."""
        pass


class StateTest(Item):
    """Single state test case item."""

    test_case: StateTestCase
    test_dict: Dict[str, Any]

    def __init__(
        self,
        *args: Any,
        test_case: StateTestCase,
        test_dict: Dict[str, Any],
        **kwargs: Any,
    ) -> None:
        """Initialize a single test case item."""
        super().__init__(*args, **kwargs)
        self.test_case = test_case
        self.test_dict = test_dict
        self.own_markers.append(pytest.mark.fork(self.test_case.fork_name))
        self.own_markers.append(pytest.mark.evm_tools)
        self.own_markers.append(pytest.mark.json_state_tests)
        eels_fork = FORKS[test_case.fork_name]["eels_fork"]
        test_patterns = exceptional_state_test_patterns(
            test_case.fork_name, eels_fork
        )
        if any(x.search(test_case.key) for x in test_patterns.slow):
            self.own_markers.append(pytest.mark.slow)

    def runtest(self) -> None:
        """Execute the test logic for this specific static test."""
        test_case_dict = {
            "test_file": self.test_case.path,
            "test_key": self.test_case.key,
            "index": self.test_case.index,
            "json_fork": self.test_case.fork_name,
            "test_dict": self.test_dict,
        }
        run_state_test(test_case_dict)


class StateTestFixture(Fixture):
    """Single state test fixture from a JSON file."""

    @classmethod
    def is_format(cls, obj: object) -> bool:
        """Return true if the object can be parsed as the fixture type."""
        if "env" not in obj:
            return False
        if "pre" not in obj:
            return False
        if "transaction" not in obj:
            return False
        if "post" not in obj:
            return False
        return True

    @classmethod
    def collect(
        cls, parent: Collector, file_path: str, key: str, obj: Dict[str, Any]
    ) -> Generator[Item, None, None]:
        """Collect state tests from a single fixture dictionary."""
        for test_case in read_state_test_case(
            test_file_path=file_path, key=key, test=obj
        ):
            if test_case.fork_name not in FORKS:
                continue
            name = f"{key} - {test_case.index}"
            new_item = StateTest.from_parent(
                parent,
                name=name,
                test_case=test_case,
                test_dict=obj,
            )
            yield new_item


class BlockchainTest(Item):
    """Single state test case item."""

    test_file: str
    test_key: str
    fork_name: str
    test_dict: Dict[str, Any]

    def __init__(
        self,
        *args: Any,
        test_file: str,
        test_key: str,
        fork_name: str,
        test_dict: Dict[str, Any],
        **kwargs: Any,
    ) -> None:
        """Initialize a single test case item."""
        super().__init__(*args, **kwargs)
        self.test_file = test_file
        self.test_key = test_key
        self.test_dict = test_dict
        self.fork_name = fork_name
        self.own_markers.append(pytest.mark.fork(fork_name))
        self.own_markers.append(pytest.mark.evm_tools)
        self.own_markers.append(pytest.mark.json_blockchain_tests)
        eels_fork = FORKS[fork_name]["eels_fork"]
        test_patterns = exceptional_blockchain_test_patterns(
            fork_name, eels_fork
        )
        _identifier = "(" + test_file + "|" + test_key + ")"
        if any(
            x.search(test_file) for x in test_patterns.expected_fail
        ) or any(x.search(_identifier) for x in test_patterns.expected_fail):
            self.own_markers.append(pytest.mark.skip("Expected to fail"))
        if any(x.search(_identifier) for x in test_patterns.slow):
            self.own_markers.append(pytest.mark.slow)
        if any(x.search(_identifier) for x in test_patterns.big_memory):
            self.own_markers.append(pytest.mark.bigmem)

    def runtest(self) -> None:
        """Execute the test logic for this specific static test."""
        test_case_dict = {
            "test_file": self.test_file,
            "test_key": self.test_key,
            "test_dict": self.test_dict,
        }
        eels_fork = FORKS[self.fork_name]["eels_fork"]
        load = Load(
            self.fork_name,
            eels_fork,
        )
        run_blockchain_st_test(test_case_dict, load=load)


class BlockchainTestFixture(Fixture):
    """Single blockchain test fixture from a JSON file."""

    @classmethod
    def is_format(cls, obj: Dict) -> bool:
        """Return true if the object can be parsed as the fixture type."""
        if "genesisBlockHeader" not in obj:
            return False
        if "blocks" not in obj:
            return False
        if "engineNewPayloads" in obj:
            return False
        if "preHash" in obj:
            return False
        if "network" not in obj:
            return False
        return True

    @classmethod
    def collect(
        cls, parent: Collector, file_path: str, key: str, obj: Dict[str, Any]
    ) -> Generator[Item, None, None]:
        """Collect blockchain tests from a single fixture dictionary."""
        name = f"{key}"
        if "network" not in obj or obj["network"] not in FORKS:
            return
        new_item = BlockchainTest.from_parent(
            parent,
            name=name,
            test_file=file_path,
            test_key=key,
            fork_name=obj["network"],
            test_dict=obj,
        )
        yield new_item


FixtureTypes: List[Type[Fixture]] = [
    StateTestFixture,
    BlockchainTestFixture,
]


class FixturesFile(File):
    """Single JSON file containing fixtures."""

    def collect(
        self: Self,
    ) -> Generator[StateTestFixture | BlockchainTestFixture, None, None]:
        """Collect test cases from a single JSON fixtures file."""
        with open(self.path, "r") as file:
            try:
                loaded_file = json.load(file)
            except Exception:
                return  # Skip *.json files that are unreadable.
            if not isinstance(loaded_file, dict):
                return
            for key, fixture_dict in loaded_file.items():
                if not isinstance(fixture_dict, dict):
                    continue
                for fixture_type in FixtureTypes:
                    if not fixture_type.is_format(fixture_dict):
                        continue
                    yield from fixture_type.collect(
                        parent=self,
                        file_path=str(self.path),
                        key=key,
                        obj=fixture_dict,
                    )
