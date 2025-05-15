from typing import Dict, TypedDict

from typing_extensions import NotRequired


class _FixtureSource(TypedDict):
    url: str
    fixture_path: str
    commit_hash: NotRequired[str]


# Update the links and commit has in order to consume
# newer/other tests
TEST_FIXTURES: Dict[str, _FixtureSource] = {
    "evm_tools_testdata": {
        "url": "https://github.com/gurukamath/evm-tools-testdata.git",
        "commit_hash": "792422d",
        "fixture_path": "tests/fixtures/evm_tools_testdata",
    },
    "ethereum_tests": {
        "url": "https://github.com/ethereum/tests.git",
        "commit_hash": "3129f16519013b265fa309208f49406b2ef57b13",
        "fixture_path": "tests/fixtures/ethereum_tests",
    },
    "latest_fork_tests": {
        "url": "https://github.com/ethereum/execution-spec-tests/releases/download/v4.5.0/fixtures_stable.tar.gz",
        "fixture_path": "tests/fixtures/latest_fork_tests",
    },
}


ETHEREUM_TESTS_PATH = TEST_FIXTURES["ethereum_tests"]["fixture_path"]
EEST_TESTS_PATH = TEST_FIXTURES["latest_fork_tests"]["fixture_path"]
