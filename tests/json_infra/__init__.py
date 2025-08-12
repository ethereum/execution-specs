from typing import Dict, Optional, TypedDict

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
        "fixture_path": "tests/json_infra/fixtures/evm_tools_testdata",
    },
    "ethereum_tests": {
        "url": "https://github.com/ethereum/tests.git",
        "commit_hash": "3129f16519013b265fa309208f49406b2ef57b13",
        "fixture_path": "tests/json_infra/fixtures/ethereum_tests",
    },
    "latest_fork_tests": {
        "url": "https://github.com/ethereum/execution-spec-tests/releases/download/v4.5.0/fixtures_stable.tar.gz",
        "fixture_path": "tests/json_infra/fixtures/latest_fork_tests",
    },
    "osaka_tests": {
        "url": "https://github.com/ethereum/execution-spec-tests/releases/download/fusaka-devnet-3%40v1.0.0/fixtures_fusaka-devnet-3.tar.gz",
        "fixture_path": "tests/json_infra/fixtures/osaka_tests",
    },
}


def _get_fixture_path(key: str) -> str:
    return TEST_FIXTURES[key]["fixture_path"]


def _build_ethereum_test_paths(
    base_path: str, legacy_fork: Optional[str] = None
) -> tuple:
    if legacy_fork:
        bc_path = f"{base_path}/LegacyTests/{legacy_fork}/BlockchainTests/"
        state_path = (
            f"{base_path}/LegacyTests/{legacy_fork}/GeneralStateTests/"
        )
    else:
        bc_path = f"{base_path}/BlockchainTests/"
        state_path = f"{base_path}/GeneralStateTests/"
    return bc_path, state_path


def _build_eest_test_paths(base_path: str) -> tuple:
    bc_path = f"{base_path}/fixtures/blockchain_tests/"
    state_path = f"{base_path}/fixtures/state_tests/"
    return bc_path, state_path


# Base paths
ETHEREUM_TESTS_BASE = _get_fixture_path("ethereum_tests")
EEST_TESTS_BASE = _get_fixture_path("latest_fork_tests")
OSAKA_TESTS_BASE = _get_fixture_path("osaka_tests")

# Ethereum test paths
(
    PRE_CONSTANTINOPLE_BC_ETHEREUM_TESTS,
    PRE_CONSTANTINOPLE_STATE_ETHEREUM_TESTS,
) = _build_ethereum_test_paths(ETHEREUM_TESTS_BASE, "Constantinople")
(
    PRE_CANCUN_BC_ETHEREUM_TESTS,
    PRE_CANCUN_STATE_ETHEREUM_TESTS,
) = _build_ethereum_test_paths(ETHEREUM_TESTS_BASE, "Cancun")
BC_ETHEREUM_TESTS, STATE_ETHEREUM_TESTS = _build_ethereum_test_paths(
    ETHEREUM_TESTS_BASE
)

# EEST test paths
EEST_BC_TESTS, EEST_STATE_TESTS = _build_eest_test_paths(EEST_TESTS_BASE)
EEST_OSAKA_BC_TESTS, EEST_OSAKA_STATE_TESTS = _build_eest_test_paths(
    OSAKA_TESTS_BASE
)


def _create_fork_config(
    eels_fork: str, bc_dirs: list, state_dirs: list
) -> dict:
    return {
        "eels_fork": eels_fork,
        "blockchain_test_dirs": bc_dirs,
        "state_test_dirs": state_dirs,
    }


PRE_CONSTANTINOPLE_DIRS = (
    [PRE_CONSTANTINOPLE_BC_ETHEREUM_TESTS, EEST_BC_TESTS],
    [PRE_CONSTANTINOPLE_STATE_ETHEREUM_TESTS, EEST_STATE_TESTS],
)

PRE_CANCUN_DIRS = (
    [PRE_CANCUN_BC_ETHEREUM_TESTS, EEST_BC_TESTS],
    [PRE_CANCUN_STATE_ETHEREUM_TESTS, EEST_STATE_TESTS],
)

CURRENT_DIRS = (
    [BC_ETHEREUM_TESTS, EEST_BC_TESTS],
    [STATE_ETHEREUM_TESTS, EEST_STATE_TESTS],
)

OSAKA_DIRS = (
    [BC_ETHEREUM_TESTS, EEST_OSAKA_BC_TESTS],
    [STATE_ETHEREUM_TESTS, EEST_OSAKA_STATE_TESTS],
)

FORKS = {
    **{
        json_fork: _create_fork_config(eels_fork, *PRE_CONSTANTINOPLE_DIRS)
        for json_fork, eels_fork in [
            ("Frontier", "frontier"),
            ("Homestead", "homestead"),
            ("EIP150", "tangerine_whistle"),
            ("EIP158", "spurious_dragon"),
            ("Byzantium", "byzantium"),
            ("ConstantinopleFix", "constantinople"),
        ]
    },
    **{
        json_fork: _create_fork_config(eels_fork, *PRE_CANCUN_DIRS)
        for json_fork, eels_fork in [
            ("Istanbul", "istanbul"),
            ("Berlin", "berlin"),
            ("London", "london"),
            ("Paris", "paris"),
            ("Shanghai", "shanghai"),
        ]
    },
    **{
        json_fork: _create_fork_config(eels_fork, *CURRENT_DIRS)
        for json_fork, eels_fork in [
            ("Cancun", "cancun"),
            ("Prague", "prague"),
        ]
    },
    "Osaka": _create_fork_config("osaka", *OSAKA_DIRS),
}
