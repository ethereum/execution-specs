"""Test the EIP checklist plugin functionality."""

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

            REFERENCE_SPEC_GIT_PATH = "N/A"
            REFERENCE_SPEC_VERSION = "N/A"

            @pytest.mark.valid_at("Prague")
            @pytest.mark.eip_checklist(
                "new_transaction_type/test/intrinsic_validity/gas_limit/exact"
            )
            def test_exact_gas(state_test: StateTestFiller):
                pass

            @pytest.mark.valid_at("Prague")
            @pytest.mark.eip_checklist(
                "new_transaction_type/test/signature/invalid/v/2",
                eip=[7702, 2930]
            )
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
    eip_2930_tests_dir = berlin_tests_dir.mkdir("eip2930_set_code_tx")
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
            new_system_contract = DEBUG NOT APPLICABLE REASON
            """
        )
    )
    # Run pytest with checklist-only mode
    testdir.copy_example(name="pytest.ini")
    result = testdir.runpytest(
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
    content = checklist_file.read()
    assert "✅" in content
    assert "test_exact_gas" in content
    assert "test_invalid_v" in content
    assert "DEBUG EXTERNAL COVERAGE REASON" in content

    checklist_file = checklist_dir / "eip2930_checklist.md"
    assert checklist_file.exists()
    content = checklist_file.read()
    assert "✅" in content
    assert "test_invalid_v" in content
    assert "N/A" in content
    assert "DEBUG NOT APPLICABLE REASON" in content
