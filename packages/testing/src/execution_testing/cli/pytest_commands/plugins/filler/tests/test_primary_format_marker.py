"""
Test that the `primary_format` marker tracks the first fixture format a test
actually generates, not merely the first entry in
``supported_fixture_formats``.

A single-format marker such as ``blockchain_test_engine_only`` discards the
test's default (primary) format, so a later format becomes the effective
primary and must carry the mark to stay selectable via ``-m primary_format``.

The session-level format filter (``should_generate_format``) can drop the
default format too, but only in sessions that generate a single format per
test (``--generate-pre-alloc-groups``, ``fill --stateful``). There is nothing
to deduplicate there, so the marker is not a useful selector; the last test
pins that one-format-per-test property instead.
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


def test_pre_alloc_group_session_generates_one_format_per_test(
    pytester: pytest.Pytester,
) -> None:
    """
    Collect a plain state test in a ``--generate-pre-alloc-groups`` session and
    assert it yields a single fixture format.

    The session-level format filter narrows every spec type to EngineX in this
    phase, so each test already generates exactly one fixture and there is
    nothing for ``primary_format`` to deduplicate. The mark that
    ``fixture_format_parameters`` put on the default format is filtered out
    along with it, which is why ``-m primary_format`` is not a useful selector
    in this session.
    """
    write_test_module(pytester, NORMAL_STATE_MODULE)

    result = pytester.runpytest(
        "-c",
        "pytest-fill.ini",
        "--fork",
        FORK,
        "--generate-pre-alloc-groups",
        TEST_MODULE_DIR,
        "--collect-only",
        "-q",
    )

    assert result.ret == 0, f"Collection failed:\n{result.outlines}"
    collected = [line for line in result.outlines if "::test_case[" in line]
    assert len(collected) == 1, (
        f"Expected a single fixture format:\n{result.outlines}"
    )
    result.stdout.fnmatch_lines(
        ["*-blockchain_test_engine_x_from_state_test]"]
    )
