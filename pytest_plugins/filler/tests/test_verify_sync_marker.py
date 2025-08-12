"""Test blockchain sync fixture generation with verify_sync pytest marker."""

import textwrap

from ethereum_clis import TransitionTool

test_module_with_verify_sync = textwrap.dedent(
    """\
    import pytest
    from ethereum_test_tools import (
        Account,
        BlockException,
        Block,
        Environment,
        Header,
        TestAddress,
        Transaction,
    )

    TEST_ADDRESS = Account(balance=1_000_000)

    @pytest.mark.valid_at("Cancun")
    def test_verify_sync_default(blockchain_test):
        blockchain_test(
            pre={TestAddress: TEST_ADDRESS},
            post={},
            blocks=[Block(txs=[Transaction()])]
        )


    @pytest.mark.valid_at("Cancun")
    @pytest.mark.verify_sync
    def test_verify_sync_with_marker(blockchain_test):
        blockchain_test(
            pre={TestAddress: TEST_ADDRESS},
            post={},
            blocks=[Block(txs=[Transaction()])]
        )

    @pytest.mark.valid_at("Cancun")
    @pytest.mark.parametrize(
        "has_exception",
        [
            pytest.param(False, id="no_exception", marks=pytest.mark.verify_sync),
            pytest.param(
                True, id="with_exception", marks=pytest.mark.exception_test
            ),
        ]
    )
    def test_verify_sync_with_param_marks(blockchain_test, has_exception):
        blockchain_test(
            pre={TestAddress: TEST_ADDRESS},
            post={},
            blocks=[
                Block(
                    txs=[Transaction()],
                    rlp_modifier=Header(gas_limit=0) if has_exception else None,
                    exception=BlockException.INCORRECT_BLOCK_FORMAT if has_exception else None,
                )
            ],
        )

    """
)


def test_verify_sync_marker(
    pytester,
    default_t8n: TransitionTool,
):
    """
    Test blockchain sync fixture generation with verify_sync marker.

    The test module has 3 test functions (4 test cases with parametrization):
    - test_verify_sync_default: generates all formats except sync (no verify_sync marker)
    - test_verify_sync_with_marker: generates all formats including sync (has verify_sync marker)
    - test_verify_sync_with_param_marks: tests parametrized marks with verify_sync (2 cases)

    Each test generates fixture formats:
    - BlockchainFixture (always)
    - BlockchainEngineFixture (always)
    - BlockchainEngineSyncFixture (only when marked with verify_sync marker)

    Expected outcomes:
    - 4 test cases total
    - Each generates BlockchainFixture (4) and BlockchainEngineFixture (4) = 8 fixtures
    - Sync fixtures:
        - test_verify_sync_with_marker: 1 sync fixture ✓
        - test_verify_sync_with_param_marks[no_exception]: 1 sync fixture ✓
        - Total sync fixtures: 2
    - Not generated (due to exception_test marker):
        - test_verify_sync_with_param_marks[with_exception]: sync fixture not generated

    Final counts:
    - Passed: 8 (base fixtures) + 2 (sync fixtures) = 10 passed
    - Skipped: 0 skipped
    - Failed: 0 failed
    """
    # Create proper directory structure for tests
    tests_dir = pytester.mkdir("tests")
    cancun_tests_dir = tests_dir / "cancun"
    cancun_tests_dir.mkdir()
    verify_sync_test_dir = cancun_tests_dir / "verify_sync_test_module"
    verify_sync_test_dir.mkdir()
    test_module = verify_sync_test_dir / "test_verify_sync_marker.py"
    test_module.write_text(test_module_with_verify_sync)

    pytester.copy_example(name="src/cli/pytest_commands/pytest_ini_files/pytest-fill.ini")

    # Add the test directory to the arguments
    args = [
        "-c",
        "pytest-fill.ini",
        "-v",
        "--no-html",
        "--t8n-server-url",
        default_t8n.server_url,
        "tests/cancun/verify_sync_test_module/",
    ]

    expected_outcomes = {"passed": 10, "failed": 0, "skipped": 0, "errors": 0}

    result = pytester.runpytest(*args)
    result.assert_outcomes(**expected_outcomes)
