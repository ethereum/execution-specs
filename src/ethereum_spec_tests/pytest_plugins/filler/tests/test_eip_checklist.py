"""Test the EIP checklist plugin functionality."""

import re
import textwrap


def test_eip_checklist_collection(testdir):
    """Test that checklist markers are collected correctly."""
    # Create the test in an EIP-specific directory
    tests_dir = testdir.mkdir("tests")

    prague_tests_dir = tests_dir.mkdir("prague")
    eip_7702_tests_dir = prague_tests_dir.mkdir("eip7702_set_code_tx")
    test_7702_module = eip_7702_tests_dir.join("test_eip7702.py")
    test_7702_module.write(
        textwrap.dedent(
            """
            import pytest
            from ethereum_test_tools import StateTestFiller

            from ethereum_test_checklists import EIPChecklist

            REFERENCE_SPEC_GIT_PATH = "N/A"
            REFERENCE_SPEC_VERSION = "N/A"

            @pytest.mark.valid_at("Prague")
            @EIPChecklist.TransactionType.Test.IntrinsicValidity.GasLimit.Exact()
            def test_exact_gas(state_test: StateTestFiller):
                pass

            @pytest.mark.valid_at("Prague")
            @EIPChecklist.TransactionType.Test.Signature.Invalid.V.Two(eip=[2930])
            def test_invalid_v(state_test: StateTestFiller):
                pass
            """
        )
    )
    eip_7702_external_coverage_file = eip_7702_tests_dir.join(
        "eip_checklist_external_coverage.txt"
    )
    eip_7702_external_coverage_file.write(
        textwrap.dedent(
            """
            general/code_coverage/eels = DEBUG EXTERNAL COVERAGE REASON
            """
        )
    )

    berlin_tests_dir = tests_dir.mkdir("berlin")
    eip_2930_tests_dir = berlin_tests_dir.mkdir("eip2930_access_list")
    test_2930_module = eip_2930_tests_dir.join("test_eip2930.py")
    test_2930_module.write(
        textwrap.dedent(
            """
            import pytest
            from ethereum_test_tools import StateTestFiller

            REFERENCE_SPEC_GIT_PATH = "N/A"
            REFERENCE_SPEC_VERSION = "N/A"

            @pytest.mark.valid_at("Berlin")
            def test_berlin_one(state_test: StateTestFiller):
                pass
            """
        )
    )
    test_2930_n_a_file = eip_2930_tests_dir.join("eip_checklist_not_applicable.txt")
    test_2930_n_a_file.write(
        textwrap.dedent(
            """
            system_contract = DEBUG NOT APPLICABLE REASON
            """
        )
    )
    # Run pytest with checklist-only mode
    testdir.copy_example(name="src/cli/pytest_commands/pytest_ini_files/pytest-fill.ini")
    result = testdir.runpytest(
        "-c",
        "pytest-fill.ini",
        "-p",
        "pytest_plugins.filler.eip_checklist",
        "--collect-only",
        "--checklist-output",
        str(testdir.tmpdir / "checklists"),
        str(tests_dir),
    )
    result.assert_outcomes(
        passed=0,
        failed=0,
        skipped=0,
        errors=0,
    )

    # Check that checklists were generated
    checklist_dir = testdir.tmpdir / "checklists"
    assert checklist_dir.exists()

    checklist_file = checklist_dir / "eip7702_checklist.md"
    assert checklist_file.exists()

    # Verify the checklist contains the expected markers
    content = checklist_file.readlines()
    assert any(re.search(r"✅.*test_exact_gas", line) for line in content)
    assert any(re.search(r"✅.*test_invalid_v", line) for line in content)
    assert any(re.search(r"✅.*DEBUG EXTERNAL COVERAGE REASON", line) for line in content)

    checklist_file = checklist_dir / "eip2930_checklist.md"
    assert checklist_file.exists()
    content = checklist_file.readlines()
    assert not any(re.search(r"✅.*test_exact_gas", line) for line in content)
    assert any(re.search(r"✅.*test_invalid_v", line) for line in content)
    assert any(re.search(r"N/A.*DEBUG NOT APPLICABLE REASON", line) for line in content)
