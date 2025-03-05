# Update the links and commit has in order to consume
# newer/other tests
TEST_FIXTURES = {
    "evm_tools_testdata": {
        "url": "https://github.com/gurukamath/evm-tools-testdata.git",
        "commit_hash": "792422d",
        "fixture_path": "tests/fixtures/evm_tools_testdata",
    },
    "ethereum_tests": {
        "url": "https://github.com/ethereum/tests.git",
        "commit_hash": "a0e8482",
        "fixture_path": "tests/fixtures/ethereum_tests",
    },
    "latest_fork_tests": {
        "url": "https://github.com/gurukamath/latest_fork_tests.git",
        "commit_hash": "bc74af5",
        "fixture_path": "tests/fixtures/latest_fork_tests",
    },
}


ETHEREUM_TESTS_PATH = TEST_FIXTURES["ethereum_tests"]["fixture_path"]
EEST_TESTS_PATH = TEST_FIXTURES["latest_fork_tests"]["fixture_path"]
