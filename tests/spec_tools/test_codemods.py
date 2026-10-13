"""
Unit tests for the codemods used by the ethereum-spec-new-fork tool.
"""

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from libcst.codemod import CodemodContext, CodemodTest
from libcst.metadata import FullRepoManager, FullyQualifiedNameProvider

from ethereum_spec_tools.new_fork.codemod.comment import CommentReplaceCommand
from ethereum_spec_tools.new_fork.codemod.constant import SetConstantCommand
from ethereum_spec_tools.new_fork.codemod.string_replace import (
    StringReplaceCommand,
)


class TestCommentReplaceCommand(CodemodTest):
    """Tests for `CommentReplaceCommand`."""

    TRANSFORM = CommentReplaceCommand

    def test_replaces_text_in_comments(self) -> None:
        """Comments are rewritten, code and strings are left alone."""
        before = """
            # Osaka fork
            osaka = "osaka"  # osaka
        """
        after = """
            # Prague fork
            osaka = "osaka"  # prague
        """
        self.assertCodemod(
            before,
            after,
            replacements=[["Osaka", "Prague"], ["osaka", "prague"]],
        )


class TestStringReplaceCommand(CodemodTest):
    """Tests for `StringReplaceCommand`."""

    TRANSFORM = StringReplaceCommand

    def test_replaces_text_in_strings(self) -> None:
        """Strings and docstrings are rewritten, code and comments are not."""
        before = '''
            """The Osaka fork."""
            osaka = "osaka"  # osaka
        '''
        after = '''
            """The Prague fork."""
            osaka = "prague"  # osaka
        '''
        self.assertCodemod(
            before,
            after,
            replacements=[["Osaka", "Prague"], ["osaka", "prague"]],
        )


class TestSetConstantCommand(CodemodTest):
    """
    Tests for `SetConstantCommand`.

    `FullyQualifiedNameProvider` needs a metadata cache, which
    `CodemodTest` does not set up, so each test writes the module to a
    temporary repository and passes a `FullRepoManager` in the context.
    """

    TRANSFORM = SetConstantCommand

    def assert_constant(self, before: str, after: str, **kwargs: Any) -> None:
        """Run the codemod on `before`, as module `pkg.mod`."""
        before = self.make_fixture_data(before)
        after = self.make_fixture_data(after)
        with TemporaryDirectory() as root:
            path = Path(root) / "pkg" / "mod.py"
            path.parent.mkdir()
            path.write_text(before)
            manager = FullRepoManager(
                root, [str(path)], {FullyQualifiedNameProvider}
            )
            context = CodemodContext(
                filename=str(path),
                full_module_name="pkg.mod",
                metadata_manager=manager,
            )
            kwargs.setdefault("imports", None)
            self.assertCodemod(
                before, after, context_override=context, **kwargs
            )

    def test_sets_annotated_constant(self) -> None:
        """Annotated assignments keep their annotation."""
        self.assert_constant(
            "X: int = 1\n",
            "X: int = 2\n",
            qualified_name="pkg.mod.X",
            value="2",
        )

    def test_ignores_class_attribute_with_same_name(self) -> None:
        """A class attribute has a different fully qualified name."""
        before = """
            class A:
                X = 1
            X = 1
        """
        after = """
            class A:
                X = 1
            X = 2
        """
        self.assert_constant(
            before, after, qualified_name="pkg.mod.X", value="2"
        )

    def test_adds_imports(self) -> None:
        """Requested imports are added to the module."""
        before = """
            X = 1
        """
        after = """
            from ethereum.fork_criteria import ByTimestamp

            X = ByTimestamp(7)
        """
        self.assert_constant(
            before,
            after,
            qualified_name="pkg.mod.X",
            value="ByTimestamp(7)",
            imports=[["ethereum.fork_criteria", "ByTimestamp"]],
        )

    def test_missing_constant_raises(self) -> None:
        """The codemod fails if the name is never assigned."""
        with self.assertRaisesRegex(Exception, "is not assigned"):
            self.assert_constant(
                "X = 1\n", "X = 1\n", qualified_name="pkg.mod.Y", value="2"
            )

    def test_chained_assignment_raises(self) -> None:
        """Assignments with several targets are not supported."""
        with self.assertRaises(NotImplementedError):
            self.assert_constant(
                "X = Y = 1\n",
                "X = Y = 1\n",
                qualified_name="pkg.mod.X",
                value="2",
            )

    def test_unpacking_assignment_raises(self) -> None:
        """Tuple unpacking is not supported."""
        with self.assertRaises(NotImplementedError):
            self.assert_constant(
                "X, Y = 1, 2\n",
                "X, Y = 1, 2\n",
                qualified_name="pkg.mod.X",
                value="3",
            )
