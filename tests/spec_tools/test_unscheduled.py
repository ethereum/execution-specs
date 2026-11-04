"""
Tests for building unscheduled features on top of a fork.

Every feature here is synthetic. Building the repository's real features is
left to their owners, so that changes to a fork never fail these tests.
"""

from pathlib import Path
from textwrap import dedent
from types import ModuleType

import pytest

from ethereum_spec_tools.forks import Hardfork
from ethereum_spec_tools.unscheduled import (
    Feature,
    FeatureDriftError,
    FeatureError,
    _overlay,
    check,
)
from ethereum_spec_tools.utils import get_supported_forks


def write(path: Path, source: str) -> None:
    """Write `source`, dedented, to `path`."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dedent(source).lstrip())


def make_feature(
    root: Path, remove: str = "[]", base: str | None = None
) -> Feature:
    """Create an empty feature directory under `root`."""
    pin = "" if base is None else f'base = "{base}"'
    write(
        root / "feature.toml",
        f"""
        eips = [1, 2]
        owners = ["someone"]
        remove = {remove}
        {pin}
        """,
    )
    return Feature.load(root)


def make_fork(root: Path) -> Hardfork:
    """Wrap the fork package in `root` without importing it."""
    module = ModuleType("ethereum.forks.fake")
    module.__path__ = [str(root)]
    return Hardfork(module)


def test_overlay_replaces_and_appends() -> None:
    """
    Replace a definition in place, keeping the fork's layout, append a new
    one, and add only the imports that the fork lacks.
    """
    target = dedent(
        '''
        """Fork module."""

        from typing import List

        from .other import helper

        LIMIT = 1
        """Docstring of `LIMIT`."""


        def run() -> int:
            return LIMIT
        '''
    ).lstrip()
    overlay = dedent(
        """
        # Comments above the overlay are not copied.

        from typing import List

        from .extra import extra

        LIMIT = 2
        \"\"\"New docstring of `LIMIT`.\"\"\"

        BONUS = extra()
        """
    ).lstrip()

    result = _overlay(target, overlay)

    assert (
        result
        == dedent(
            '''
        """Fork module."""

        from typing import List

        from .other import helper
        from .extra import extra

        LIMIT = 2
        """New docstring of `LIMIT`."""


        def run() -> int:
            return LIMIT


        BONUS = extra()
        '''
        ).lstrip()
    )


@pytest.mark.parametrize(
    "target,overlay",
    [
        pytest.param("X = 1\n", "Y = 2\nX = Y\n", id="constant"),
        pytest.param(
            dedent(
                """
                from typing import Union


                class Legacy:
                    pass


                Transaction = Union[Legacy]


                def decode(data: bytes) -> Transaction:
                    return Legacy()
                """
            ),
            dedent(
                """
                from typing import Union


                class Framed:
                    pass


                Transaction = Union[Legacy, Framed]
                """
            ),
            id="transaction_union",
        ),
    ],
)
def test_overlay_keeps_definition_order(target: str, overlay: str) -> None:
    """
    A new definition that a replaced definition uses lands above it, so
    the built module runs.
    """
    result = _overlay(target, overlay)
    exec(compile(result, "<overlay>", "exec"), {})


def test_overlay_replaces_module_docstring() -> None:
    """An overlay's module docstring replaces the fork's."""
    result = _overlay('"""Old."""\n\nX = 1\n', '"""New."""\n')
    assert result == '"""New."""\n\nX = 1\n'


def test_overlay_rejects_conflicting_import() -> None:
    """
    Refuse to import a name that the fork binds from somewhere else, since
    the overlay would silently use the fork's.
    """
    with pytest.raises(FeatureError, match="binds it from"):
        _overlay(
            "from .state import set_account\n",
            "from ethereum.state_mpt import set_account\n",
        )


def test_overlay_rejects_statements() -> None:
    """Overlays may only hold imports and definitions."""
    with pytest.raises(FeatureError, match="only hold imports"):
        _overlay("X = 1\n", "if True:\n    X = 2\n")


def test_apply_removals(tmp_path: Path) -> None:
    """
    Remove files, definitions with their docstrings, class attributes,
    imports and `__all__` entries.
    """
    package = tmp_path / "fork"
    write(
        package / "__init__.py",
        """
        __all__ = ("A", "B")

        A = 1
        \"\"\"Docstring of `A`.\"\"\"
        B = 2
        """,
    )
    write(
        package / "mod.py",
        """
        from . import A, B


        class Costs:
            X = 1
            \"\"\"Docstring of `X`.\"\"\"
            Y = 2
        """,
    )
    write(package / "gone.py", "GONE = 1\n")
    feature = make_feature(
        tmp_path / "feature",
        remove='["gone.py", "A", "mod.A", "mod.Costs.X"]',
    )

    feature.apply(package)

    assert not (package / "gone.py").exists()
    assert (
        package / "__init__.py"
    ).read_text() == '__all__ = ("B",)\n\nB = 2\n'
    assert (package / "mod.py").read_text() == dedent(
        """
        from . import B


        class Costs:
            Y = 2
        """
    ).lstrip()


def test_apply_rejects_missing_removal(tmp_path: Path) -> None:
    """Removing a definition that the fork no longer has is an error."""
    package = tmp_path / "fork"
    write(package / "mod.py", "A = 1\n")
    feature = make_feature(tmp_path / "feature", remove='["mod.B"]')

    with pytest.raises(FeatureError, match="missing `mod.B`"):
        feature.apply(package)


def test_apply_adds_new_files(tmp_path: Path) -> None:
    """Files that the fork lacks are copied in as they are."""
    package = tmp_path / "fork"
    write(package / "__init__.py", "")
    feature = make_feature(tmp_path / "feature")
    write(feature.path / "vm" / "new.py", "NEW = 1\n")

    feature.apply(package)

    assert (package / "vm" / "new.py").read_text() == "NEW = 1\n"


def test_lock_detects_drift(tmp_path: Path) -> None:
    """
    Changing the code of a replaced definition breaks the lock, while
    changing its docstring or layout does not.
    """
    fork_path = tmp_path / "fork"
    write(fork_path / "fork.py", "def apply_fork(old):\n    return old\n")
    fork = make_fork(fork_path)
    feature = make_feature(tmp_path / "feature")
    write(feature.path / "fork.py", "def apply_fork(old):\n    return 1\n")

    with pytest.raises(FeatureDriftError):
        feature.check_lock(fork)

    feature.write_lock(fork)
    feature.check_lock(fork)
    assert list(feature.recorded_hashes()) == ["fork.apply_fork"]

    write(
        fork_path / "fork.py",
        '''
        def apply_fork(old):
            """Now with a docstring."""

            return old
        ''',
    )
    feature.check_lock(fork)

    write(fork_path / "fork.py", "def apply_fork(old):\n    return None\n")
    with pytest.raises(FeatureDriftError, match="fork.apply_fork"):
        feature.check_lock(fork)


def test_lock_ignores_attribute_docstrings(tmp_path: Path) -> None:
    """
    Rewording the docstring of a class attribute, as happens when a fork
    is copied into the next one, does not break the lock.
    """
    fork_path = tmp_path / "fork"
    header = """
        class Header:
            number: int
            \"\"\"Number of the block, as of {fork}.\"\"\"
        """
    write(fork_path / "blocks.py", header.format(fork="Amsterdam"))
    fork = make_fork(fork_path)
    feature = make_feature(tmp_path / "feature")
    write(feature.path / "blocks.py", "class Header:\n    number: int\n")
    feature.write_lock(fork)

    write(fork_path / "blocks.py", header.format(fork="Bogota"))
    feature.check_lock(fork)


def test_build_on_newest_fork(tmp_path: Path) -> None:
    """
    Build a feature on the newest fork, then import and use the result.
    """
    newest = Hardfork.discover()[-1]
    feature = make_feature(tmp_path / "feature")
    write(
        feature.path / "__init__.py",
        '''
        """
        A synthetic feature.
        """
        ''',
    )
    write(
        feature.path / "fork.py",
        """
        from .answer import ANSWER


        def apply_fork(old: BlockChain) -> int:
            \"\"\"Return the answer instead of the chain.\"\"\"
            return ANSWER
        """,
    )
    write(feature.path / "answer.py", "ANSWER = 42\n")
    feature.write_lock(newest)

    with feature.build(newest) as fork:
        assert fork.criteria > newest.criteria
        assert fork.mod.__doc__.strip() == "A synthetic feature."
        assert fork.module("answer").ANSWER == 42
        fork_module = fork.module("fork")
        assert fork_module.apply_fork(object()) == 42
        assert fork_module.PreviousHeader.__module__ == f"{newest.name}.blocks"


def test_build_on_pinned_base(tmp_path: Path) -> None:
    """
    A feature that pins a `base` fork builds on it instead of the newest
    fork.
    """
    feature = make_feature(tmp_path / "feature", base="osaka")
    assert feature.base_fork().short_name == "osaka"
    write(feature.path / "answer.py", "ANSWER = 42\n")
    feature.write_lock(feature.base_fork())

    with feature.build() as fork:
        assert fork.path is not None
        # Block access lists arrived after Osaka.
        assert not (Path(fork.path) / "block_access_lists.py").exists()
        assert fork.criteria > feature.base_fork().criteria
        assert fork.module("answer").ANSWER == 42


@pytest.mark.parametrize(
    "source,base,passes",
    [
        pytest.param("ANSWER: int = 42\n", None, True, id="clean"),
        pytest.param(
            "ANSWER: int = 42\n",
            "osaka",
            True,
            id="clean_pinned_to_older_fork",
        ),
        pytest.param(
            "ANSWER: int = undefined_name\n", None, False, id="undefined_name"
        ),
        pytest.param(
            "from ethereum.forks.bogota.blocks import Header\n\n"
            "HEADER = Header\n",
            "osaka",
            False,
            id="import_from_newer_fork",
        ),
        pytest.param(
            "from ethereum.forks.prague.blocks import Header\n\n"
            "HEADER = Header\n",
            "osaka",
            False,
            id="import_from_older_fork",
        ),
    ],
)
def test_check(
    tmp_path: Path, source: str, base: str | None, passes: bool
) -> None:
    """
    Checking a feature lints and type checks its built fork against the
    scheduled forks, so a mistake in an overlay or an import from a fork
    other than its base fails it, while a clean feature passes whatever its
    base.
    """
    feature = make_feature(tmp_path / "feature", base=base)
    write(feature.path / "answer.py", source)
    feature.write_lock(feature.base_fork())

    assert check(feature, feature.base_fork()) == passes


def test_supported_forks_include_features() -> None:
    """The transition tool accepts every feature by its fork name."""
    names = {feature.title_case_name for feature in Feature.discover()}
    assert names <= set(get_supported_forks())
