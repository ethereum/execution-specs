"""
Test fork covariant markers and their effect on test parametrization.
"""

import pytest


@pytest.mark.parametrize(
    "test_function,passed,failed,skipped,errors",
    [
        pytest.param(
            """
            import pytest
            @pytest.mark.with_all_tx_types()
            @pytest.mark.valid_from("Paris")
            @pytest.mark.valid_until("Paris")
            def test_case(state_test_only, tx_type):
                pass
            """,
            3,
            0,
            0,
            0,
            id="with_all_tx_types",
        ),
        pytest.param(
            """
            import pytest
            @pytest.mark.with_all_tx_types(selector=lambda tx_type: tx_type != 0)
            @pytest.mark.valid_from("Paris")
            @pytest.mark.valid_until("Paris")
            def test_case(state_test_only, tx_type):
                pass
            """,
            2,
            0,
            0,
            0,
            id="with_all_tx_types_with_selector",
        ),
        pytest.param(
            """
            import pytest
            @pytest.mark.with_all_contract_creating_tx_types()
            @pytest.mark.valid_from("Paris")
            @pytest.mark.valid_until("Paris")
            def test_case(state_test_only, tx_type):
                pass
            """,
            3,
            0,
            0,
            0,
            id="with_all_contract_creating_tx_types",
        ),
        pytest.param(
            """
            import pytest
            @pytest.mark.with_all_contract_creating_tx_types()
            @pytest.mark.valid_from("Cancun")
            @pytest.mark.valid_until("Cancun")
            def test_case(state_test_only, tx_type):
                pass
            """,
            3,
            0,
            0,
            0,
            id="with_all_contract_creating_tx_types",
        ),
        pytest.param(
            """
            import pytest
            @pytest.mark.with_all_precompiles()
            @pytest.mark.valid_from("Cancun")
            @pytest.mark.valid_until("Cancun")
            def test_case(state_test_only, precompile):
                pass
            """,
            10,
            0,
            0,
            0,
            id="with_all_precompiles",
        ),
        pytest.param(
            """
            import pytest
            @pytest.mark.with_all_evm_code_types()
            @pytest.mark.valid_from("Cancun")
            @pytest.mark.valid_until("Cancun")
            def test_case(state_test_only, evm_code_type):
                pass
            """,
            1,
            0,
            0,
            0,
            id="with_all_evm_code_types",
        ),
        pytest.param(
            """
            import pytest
            @pytest.mark.with_all_call_opcodes()
            @pytest.mark.valid_from("Cancun")
            @pytest.mark.valid_until("Cancun")
            def test_case(state_test_only, call_opcode):
                pass
            """,
            4,
            0,
            0,
            0,
            id="with_all_call_opcodes",
        ),
        pytest.param(
            """
            import pytest
            @pytest.mark.with_all_create_opcodes()
            @pytest.mark.valid_from("Cancun")
            @pytest.mark.valid_until("Cancun")
            def test_case(state_test_only, create_opcode):
                pass
            """,
            2,
            0,
            0,
            0,
            id="with_all_create_opcodes",
        ),
        pytest.param(
            """
            import pytest
            @pytest.mark.with_all_system_contracts()
            @pytest.mark.valid_from("Cancun")
            @pytest.mark.valid_until("Cancun")
            def test_case(state_test_only, system_contract):
                pass
            """,
            1,
            0,
            0,
            0,
            id="with_all_system_contracts",
        ),
        pytest.param(
            """
            import pytest
            @pytest.mark.with_all_tx_types(invalid_parameter="invalid")
            @pytest.mark.valid_from("Paris")
            @pytest.mark.valid_until("Paris")
            def test_case(state_test_only, tx_type):
                pass
            """,
            0,
            0,
            0,
            1,
            id="invalid_covariant_marker_parameter",
        ),
        pytest.param(
            """
            import pytest
            @pytest.mark.with_all_tx_types(selector=None)
            @pytest.mark.valid_from("Paris")
            @pytest.mark.valid_until("Paris")
            def test_case(state_test_only, tx_type):
                pass
            """,
            0,
            0,
            0,
            1,
            id="invalid_selector",
        ),
    ],
)
def test_fork_covariant_markers(
    pytester,
    test_function: str,
    passed: int,
    failed: int,
    skipped: int,
    errors: int,
):
    """
    Test that a test with an invalid marker cases:
        - Creates an outcome with exactly one error.
        - Triggers the expected error string in pytest's console output.

    Each invalid marwith_all_tx_typesker/marker combination is tested with one test in its own test
    session.
    """
    pytester.makepyfile(test_function)
    pytester.copy_example(name="pytest.ini")
    result = pytester.runpytest()
    result.assert_outcomes(
        passed=passed,
        failed=failed,
        skipped=skipped,
        errors=errors,
    )
    # assert error_string in "\n".join(result.stdout.lines)
