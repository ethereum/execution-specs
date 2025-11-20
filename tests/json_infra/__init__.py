"""Tests related to json infrastructure."""

from typing import Dict, TypedDict

from typing_extensions import NotRequired

from .hardfork import TestHardfork


class _FixtureSource(TypedDict):
    url: str
    fixture_path: str
    commit_hash: NotRequired[str]


# Update the links and commit hash in order to consume
# newer/other tests
TEST_FIXTURES: Dict[str, _FixtureSource] = {
    "evm_tools_testdata": {
        "url": "https://github.com/gurukamath/evm-tools-testdata.git",
        "commit_hash": "792422d",
        "fixture_path": "tests/json_infra/fixtures/evm_tools_testdata",
    },
    "ethereum_tests": {
        "url": "https://github.com/ethereum/tests.git",
        "commit_hash": "c67e485ff8b5be9abc8ad15345ec21aa22e290d9",
        "fixture_path": "tests/json_infra/fixtures/ethereum_tests",
    },
    "latest_fork_tests": {
        "url": "https://github.com/ethereum/execution-spec-tests/releases/download/v5.0.0/fixtures_develop.tar.gz",
        "fixture_path": "tests/json_infra/fixtures/latest_fork_tests",
    },
}


FORKS: Dict[str, TestHardfork] = {
    fork.json_test_name: fork for fork in TestHardfork.discover()
}
