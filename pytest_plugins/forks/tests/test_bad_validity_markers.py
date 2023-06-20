"""
Test that the correct error is produced if bad/invalid validity markers are specified.
"""

import pytest

invalid_validity_marker_test_cases = (
    (
        "too_many_valid_from_markers",
        (
            """
            import pytest
            @pytest.mark.valid_from("Merge")
            @pytest.mark.valid_from("Merge")
            def test_case(state_test):
                assert 0
            """,
            "Too many 'valid_from' markers applied to test",
        ),
    ),
    (
        "too_many_valid_until_markers",
        (
            """
            import pytest
            @pytest.mark.valid_until("Merge")
            @pytest.mark.valid_until("Merge")
            def test_case(state_test):
                assert 0
            """,
            "Too many 'valid_until' markers applied to test",
        ),
    ),
    (
        "too_many_valid_at_transition_to_markers",
        (
            """
            import pytest
            @pytest.mark.valid_at_transition_to("Merge")
            @pytest.mark.valid_at_transition_to("Merge")
            def test_case(state_test):
                assert 0
            """,
            "Too many 'valid_at_transition_to' markers applied to test",
        ),
    ),
    (
        "valid_from_no_args",
        (
            """
            import pytest
            @pytest.mark.valid_from()
            def test_case(state_test):
                assert 0
            """,
            "Missing fork argument with 'valid_from' marker",
        ),
    ),
    (
        "valid_until_no_args",
        (
            """
            import pytest
            @pytest.mark.valid_until()
            def test_case(state_test):
                assert 0
            """,
            "Missing fork argument with 'valid_until' marker",
        ),
    ),
    (
        "valid_at_transition_to_no_args",
        (
            """
            import pytest
            @pytest.mark.valid_at_transition_to()
            def test_case(state_test):
                assert 0
            """,
            "Missing fork argument with 'valid_at_transition_to' marker",
        ),
    ),
    (
        "valid_from_too_many_args",
        (
            """
            import pytest
            @pytest.mark.valid_from("Merge", "Merge")
            def test_case(state_test):
                assert 0
            """,
            "Too many arguments specified to 'valid_from'",
        ),
    ),
    (
        "valid_until_too_many_args",
        (
            """
            import pytest
            @pytest.mark.valid_until("Merge", "Merge")
            def test_case(state_test):
                assert 0
            """,
            "Too many arguments specified to 'valid_until'",
        ),
    ),
    (
        "valid_at_transition_too_many_args",
        (
            """
            import pytest
            @pytest.mark.valid_at_transition_to("Merge", "Merge")
            def test_case(state_test):
                assert 0
            """,
            "Too many arguments specified to 'valid_at_transition_to'",
        ),
    ),
    (
        "valid_from_nonexistent_fork",
        (
            """
            import pytest
            @pytest.mark.valid_from("Marge")
            def test_case(state_test):
                assert 0
            """,
            "invalid fork 'Marge'",
        ),
    ),
    (
        "valid_until_nonexistent_fork",
        (
            """
            import pytest
            @pytest.mark.valid_until("Shangbye")
            def test_case(state_test):
                assert 0
            """,
            "invalid fork 'Shangbye'",
        ),
    ),
    (
        "valid_at_transition_to_nonexistent_fork",
        (
            """
            import pytest
            @pytest.mark.valid_at_transition_to("Cantcun")
            def test_case(state_test):
                assert 0
            """,
            "invalid fork 'Cantcun'",
        ),
    ),
    (
        "valid_at_transition_to_and_valid_from",
        (
            """
            import pytest
            @pytest.mark.valid_at_transition_to("Cancun")
            @pytest.mark.valid_from("Merge")
            def test_case(state_test):
                assert 0
            """,
            "The markers 'valid_from' and 'valid_at_transition_to' can't be combined",
        ),
    ),
    (
        "valid_at_transition_to_and_valid_until",
        (
            """
            import pytest
            @pytest.mark.valid_at_transition_to("Shanghai")
            @pytest.mark.valid_until("Cancun")
            def test_case(state_test):
                assert 0
            """,
            "The markers 'valid_until' and 'valid_at_transition_to' can't be combined",
        ),
    ),
    (
        "invalid_validity_range",
        (
            """
            import pytest
            @pytest.mark.valid_from("Merge")
            @pytest.mark.valid_until("Frontier")
            def test_case(state_test):
                assert 0
            """,
            "fork validity markers generate an empty fork range",
        ),
    ),
)


@pytest.mark.parametrize(
    "test_function, error_string",
    [test_case for _, test_case in invalid_validity_marker_test_cases],
    ids=[test_id for test_id, _ in invalid_validity_marker_test_cases],
)
def test_invalid_validity_markers(pytester, error_string, test_function):
    """
    Test that a test with an invalid marker cases:
        - Creates an outcome with exactly one error.
        - Triggers the expected error string in pytest's console output.

    Each invalid marker/marker combination is tested with one test in its own test
    session.
    """
    pytester.makepyfile(test_function)
    pytester.copy_example(name="pytest.ini")
    result = pytester.runpytest()
    result.assert_outcomes(
        passed=0,
        failed=0,
        skipped=0,
        errors=1,
    )
    assert error_string in "\n".join(result.stdout.lines)
