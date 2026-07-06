"""
Test that the `derived_test` marker tracks the first fixture format that is
actually generated for a test, not merely the first entry in
``supported_fixture_formats``.

Two ways the positional-first format can drop out, leaving a fixture that
used to be tagged ``derived_test`` purely because of its list position:

1. A single-format marker such as ``blockchain_test_engine_only`` discards
   the test's default (primary) format.
2. A session-level format filter (e.g. a ``--generate-pre-alloc-groups``
   session, which only generates EngineX fixtures) excludes the primary
   format from parametrization entirely.

In both cases the surviving format is the test's effective primary, so it
must stay unmarked and remain selectable via ``-m "not derived_test"``.
"""

import textwrap

import pytest

# A post-Paris fork is required: pre-Paris hive/engine fixtures are removed
# during collection (see `pytest_collection_modifyitems` in filler.py), which
# would empty a `blockchain_test_engine_only` test regardless of this marker.
FORK = "Prague"

ENGINE_ONLY_MODULE = textwrap.dedent(
    f"""\
    import pytest

    @pytest.mark.valid_at("{FORK}")
    @pytest.mark.blockchain_test_engine_only
    def test_case(blockchain_test) -> None:
        pass
    """
)

NORMAL_BLOCKCHAIN_MODULE = textwrap.dedent(
    f"""\
    import pytest

    @pytest.mark.valid_at("{FORK}")
    def test_case(blockchain_test) -> None:
        pass
    """
)

STATE_ONLY_MODULE = textwrap.dedent(
    f"""\
    import pytest

    @pytest.mark.valid_at("{FORK}")
    @pytest.mark.state_test_only
    def test_case(state_test) -> None:
        pass
    """
)

NORMAL_STATE_MODULE = textwrap.dedent(
    f"""\
    import pytest

    @pytest.mark.valid_at("{FORK}")
    def test_case(state_test) -> None:
        pass
    """
)

TEST_MODULE_DIR = "tests/prague/dummy_test_module"


def write_test_module(pytester: pytest.Pytester, module_source: str) -> None:
    """
    Write a test module and the fill ini file to the pytester directory.
    """
    module_dir = pytester.path / TEST_MODULE_DIR
    module_dir.mkdir(parents=True)
    (module_dir / "test_dummy.py").write_text(module_source)
    pytester.copy_example(
        name="src/execution_testing/cli/pytest_commands/pytest_ini_files/pytest-fill.ini"
    )


@pytest.mark.parametrize(
    "module_source,present,absent",
    [
        pytest.param(
            ENGINE_ONLY_MODULE,
            "-blockchain_test_engine]",
            "-blockchain_test]",
            id="engine_only_survivor_is_primary",
        ),
        pytest.param(
            NORMAL_BLOCKCHAIN_MODULE,
            "-blockchain_test]",
            "-blockchain_test_engine]",
            id="normal_test_still_marks_derived",
        ),
        pytest.param(
            STATE_ONLY_MODULE,
            "-state_test]",
            "-blockchain_test_from_state_test]",
            id="state_only_survivor_is_primary",
        ),
    ],
)
def test_not_derived_test_selects_primary_survivor(
    pytester: pytest.Pytester,
    module_source: str,
    present: str,
    absent: str,
) -> None:
    """
    Collect with ``-m "not derived_test"`` and assert the test's primary
    (first surviving) fixture format is selected while its derived formats are
    not.
    """
    write_test_module(pytester, module_source)

    result = pytester.runpytest(
        "-c",
        "pytest-fill.ini",
        "--fork",
        FORK,
        "-m",
        "not derived_test",
        TEST_MODULE_DIR,
        "--collect-only",
        "-q",
    )

    assert result.ret == 0, f"Collection failed:\n{result.outlines}"
    assert any(present in line for line in result.outlines), (
        f"Expected {present!r} to be collected:\n{result.outlines}"
    )
    assert not any(absent in line for line in result.outlines), (
        f"Expected {absent!r} to be absent under `not derived_test`:\n"
        f"{result.outlines}"
    )


def test_not_derived_test_selects_session_filter_survivor(
    pytester: pytest.Pytester,
) -> None:
    """
    Collect a plain state test in a ``--generate-pre-alloc-groups`` session
    with ``-m "not derived_test"`` and assert that the only format generated
    in this session (EngineX) is selected as the test's primary.

    The session-level format filter (``should_generate_format``) excludes all
    other formats before parametrization, so the EngineX fixture must not
    inherit a ``derived_test`` mark from its position in
    ``supported_fixture_formats``.
    """
    write_test_module(pytester, NORMAL_STATE_MODULE)

    result = pytester.runpytest(
        "-c",
        "pytest-fill.ini",
        "--fork",
        FORK,
        "--generate-pre-alloc-groups",
        "-m",
        "not derived_test",
        TEST_MODULE_DIR,
        "--collect-only",
        "-q",
    )

    engine_x = "-blockchain_test_engine_x_from_state_test]"
    assert result.ret == 0, f"Collection failed:\n{result.outlines}"
    assert any(engine_x in line for line in result.outlines), (
        f"Expected {engine_x!r} to be collected:\n{result.outlines}"
    )
    assert not any("-state_test]" in line for line in result.outlines), (
        "Expected the state test format to be excluded by the session "
        f"format filter:\n{result.outlines}"
    )
