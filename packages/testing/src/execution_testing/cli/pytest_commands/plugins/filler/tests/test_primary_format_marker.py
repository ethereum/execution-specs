"""
Test that the `primary_format` marker tracks the first fixture format that is
actually generated for a test, not merely the first entry in
``supported_fixture_formats``.

Two ways the positional-first format can drop out, leaving a later format as
the test's effective primary:

1. A single-format marker such as ``blockchain_test_engine_only`` discards
   the test's default (primary) format.
2. A session-level format filter (e.g. a ``--generate-pre-alloc-groups``
   session, which only generates EngineX fixtures) excludes the primary
   format from parametrization entirely.

In both cases the surviving format is the test's effective primary, so it must
carry the mark and stay selectable via ``-m primary_format``.
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
            id="normal_test_primary_is_default_format",
        ),
        pytest.param(
            STATE_ONLY_MODULE,
            "-state_test]",
            "-blockchain_test_from_state_test]",
            id="state_only_survivor_is_primary",
        ),
    ],
)
def test_primary_format_selects_first_survivor(
    pytester: pytest.Pytester,
    module_source: str,
    present: str,
    absent: str,
) -> None:
    """
    Collect with ``-m primary_format`` and assert the test's primary (first
    surviving) fixture format is selected while its other formats are not.
    """
    write_test_module(pytester, module_source)

    result = pytester.runpytest(
        "-c",
        "pytest-fill.ini",
        "--fork",
        FORK,
        "-m",
        "primary_format",
        TEST_MODULE_DIR,
        "--collect-only",
        "-q",
    )

    assert result.ret == 0, f"Collection failed:\n{result.outlines}"
    result.stdout.fnmatch_lines([f"*{present}"])
    result.stdout.no_fnmatch_line(f"*{absent}")


def test_primary_format_selects_session_filter_survivor(
    pytester: pytest.Pytester,
) -> None:
    """
    Collect a plain state test in a ``--generate-pre-alloc-groups`` session
    with ``-m primary_format`` and assert that the only format generated in
    this session (EngineX) is selected as the test's primary.

    The session-level format filter (``should_generate_format``) excludes all
    other formats before parametrization, so the EngineX fixture must receive
    the mark despite its position in ``supported_fixture_formats``.
    """
    write_test_module(pytester, NORMAL_STATE_MODULE)

    result = pytester.runpytest(
        "-c",
        "pytest-fill.ini",
        "--fork",
        FORK,
        "--generate-pre-alloc-groups",
        "-m",
        "primary_format",
        TEST_MODULE_DIR,
        "--collect-only",
        "-q",
    )

    assert result.ret == 0, f"Collection failed:\n{result.outlines}"
    result.stdout.fnmatch_lines(
        ["*-blockchain_test_engine_x_from_state_test]"]
    )
    result.stdout.no_fnmatch_line("*-state_test]")
