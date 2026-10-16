"""
Unscheduled features built on top of the newest fork.

A feature is a single EIP, or a set of EIPs, that is not scheduled for any
fork yet, kept in `src/ethereum/unscheduled/<feature>/` as only the changes it
makes to a fork:

- `feature.toml` names the EIPs and the feature's owners, and lists the files
  and definitions that the feature removes from the fork. It may also pin the
  feature to a `base` fork, which is otherwise the newest fork.
- Every Python file mirrors a path in the fork package. A path that the fork
  does not have is added as is. A path that it does have is an overlay: its
  top-level definitions replace the fork's definitions of the same name, new
  definitions are added in the overlay's order, and its imports are added
  where the fork lacks them.
- `base.lock` records a hash of every fork definition that the feature
  replaces. When the fork changes one of them, the feature refuses to build
  until its owners review the change and refresh the lock.

Nothing generated is committed. The feature's fork is built on demand from its
base fork into a temporary directory, so changes to the fork never have to
touch the feature.
"""

import argparse
import ast
import hashlib
import json
import os
import random
import subprocess
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from shutil import copyfile, copytree, ignore_patterns
from tempfile import TemporaryDirectory
from typing import Dict, Final, Iterator, List, Sequence, Set, Tuple

import libcst as cst
from libcst.helpers import get_full_name_for_node_or_raise
from typing_extensions import override

import ethereum

from .forks import Hardfork, TemporaryHardfork
from .new_fork.builder import ForkBuilder, _source_file_for

UNSCHEDULED_PATH: Final[Path] = Path(ethereum.__file__).parent / "unscheduled"
"""
Directory holding one subdirectory per feature.
"""

PYPROJECT: Final[Path] = Path(__file__).parents[2] / "pyproject.toml"
"""
Configuration of the repository's linters, available in a source checkout.
"""

MANIFEST: Final[str] = "feature.toml"
LOCK: Final[str] = "base.lock"


class FeatureError(Exception):
    """
    A feature cannot be applied to the fork.
    """


class FeatureDriftError(FeatureError):
    """
    The fork changed a definition that a feature replaces.
    """


@dataclass(frozen=True)
class Feature:
    """
    An unscheduled feature, read from its directory.
    """

    name: str
    path: Path
    eips: Tuple[int, ...]
    owners: Tuple[str, ...]
    removals: Tuple[str, ...]
    base: str | None

    @classmethod
    def discover(cls, root: Path = UNSCHEDULED_PATH) -> List["Feature"]:
        """
        Find every feature under `root`.
        """
        if not root.is_dir():
            return []
        return [
            cls.load(path)
            for path in sorted(root.iterdir())
            if (path / MANIFEST).is_file()
        ]

    @classmethod
    def load(cls, path: Path) -> "Feature":
        """
        Read the feature in the directory `path`.
        """
        manifest = tomllib.loads((path / MANIFEST).read_text())
        return cls(
            name=path.name,
            path=path,
            eips=tuple(int(eip) for eip in manifest["eips"]),
            owners=tuple(manifest["owners"]),
            removals=tuple(manifest.get("remove", ())),
            base=manifest.get("base"),
        )

    @classmethod
    def by_name(cls, name: str) -> "Feature":
        """
        Return the feature with the given snake case `name`.
        """
        for feature in cls.discover():
            if feature.name == name:
                return feature
        raise ValueError(f"unknown feature `{name}`")

    def base_fork(self) -> Hardfork:
        """
        Return the fork that the feature is pinned to, or else the newest
        fork.
        """
        if self.base is None:
            return Hardfork.discover()[-1]
        return Hardfork.by_short_name(self.base)

    @property
    def title_case_name(self) -> str:
        """
        Name of the feature as the testing framework spells it.
        """
        return self.name.replace("_", " ").title().replace(" ", "")

    def sources(self) -> Iterator[Path]:
        """
        Yield the feature's Python files, relative to its directory.
        """
        for path in sorted(self.path.rglob("*.py")):
            yield path.relative_to(self.path)

    def recorded_hashes(self) -> Dict[str, str]:
        """
        Return the hashes stored in the feature's lock file.
        """
        lock = self.path / LOCK
        if not lock.is_file():
            return {}
        return json.loads(lock.read_text())

    def replaced_hashes(self, template: Hardfork) -> Dict[str, str]:
        """
        Hash every definition of `template` that the feature replaces.
        """
        root = _fork_root(template)
        hashes = {}
        for relative in self.sources():
            base = root / relative
            if not base.is_file():
                continue
            base_definitions = _ast_definitions(base.read_text())
            overlay = _ast_definitions((self.path / relative).read_text())
            module = _module_name(relative)
            for name in overlay:
                if name in base_definitions:
                    key = f"{module}.{name}" if module else name
                    hashes[key] = _hash_definition(base_definitions[name])
        return dict(sorted(hashes.items()))

    def check_lock(self, template: Hardfork) -> None:
        """
        Raise `FeatureDriftError` if `template` changed a definition that the
        feature replaces since the lock was last refreshed.
        """
        current = self.replaced_hashes(template)
        recorded = self.recorded_hashes()
        if current == recorded:
            return
        changed = sorted(
            name
            for name in current.keys() | recorded.keys()
            if current.get(name) != recorded.get(name)
        )
        eips = ", ".join(f"EIP-{eip}" for eip in self.eips)
        raise FeatureDriftError(
            f"feature `{self.name}` ({eips}, owned by "
            f"{', '.join(self.owners)}) replaces definitions that changed "
            f"in `{template.short_name}`: {', '.join(changed)}. Carry the "
            "fork's changes into the feature if they apply, then run "
            f"`uv run ethereum-spec-unscheduled {self.name} --update-lock`."
        )

    def write_lock(self, template: Hardfork) -> None:
        """
        Record the hashes of the definitions that the feature replaces.
        """
        hashes = self.replaced_hashes(template)
        (self.path / LOCK).write_text(json.dumps(hashes, indent=4) + "\n")

    def apply(self, package: Path) -> None:
        """
        Change the fork in `package` into this feature's fork.
        """
        for removal in self.removals:
            _remove(package, removal)
        for relative in self.sources():
            source = self.path / relative
            target = package / relative
            if target.is_file():
                target.write_text(
                    _overlay(target.read_text(), source.read_text())
                )
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                copyfile(source, target)

    def build(
        self,
        template: Hardfork | None = None,
        module_name: str | None = None,
    ) -> TemporaryHardfork:
        """
        Build the feature's fork on top of `template` (by default its base
        fork) in a temporary directory.
        """
        if template is None:
            template = self.base_fork()
        if module_name is None:
            module_name = f"{self.name}{random.randrange(1_000_000_000)}"

        self.check_lock(template)

        maybe_directory: TemporaryDirectory | None = TemporaryDirectory()
        try:
            assert maybe_directory is not None
            directory: TemporaryDirectory = maybe_directory

            builder = FeatureBuilder(self, template.short_name, module_name)
            builder.output = Path(directory.name)
            builder.build()

            forks = Hardfork.discover([directory.name])
            if len(forks) != 1 or forks[0].short_name != module_name:
                raise FeatureError(f"failed to build feature `{self.name}`")

            value = TemporaryHardfork(forks[0].mod, directory)
            maybe_directory = None
            return value
        finally:
            if maybe_directory is not None:
                maybe_directory.cleanup()


def check(feature: Feature, template: Hardfork) -> bool:
    """
    Build `feature` on `template` as a fork inside a copy of the `ethereum`
    package, then check it like any other fork: pyflakes, mypy and the
    specification linter. Needs a source checkout with the development
    dependencies installed.

    Return whether every check passed.
    """
    feature.check_lock(template)
    with TemporaryDirectory() as directory:
        package = Path(directory) / "ethereum"
        copytree(
            Path(ethereum.__file__).parent,
            package,
            ignore=ignore_patterns("__pycache__", "unscheduled"),
        )
        builder = FeatureBuilder(feature, template.short_name, feature.name)
        builder.output = package / "forks"
        builder.build()
        fork = str(package / "forks" / feature.name)

        # Put the copy ahead of the installed `ethereum` package.
        environment = {
            **os.environ,
            "MYPYPATH": directory,
            "PYTHONPATH": directory,
        }
        commands = [
            ["ruff", "check", "--no-cache", "--isolated", "--select=F,E9"],
            [
                "mypy",
                f"--config-file={PYPROJECT}",
                f"--cache-dir={directory}/.mypy_cache",
                "--follow-imports=silent",
            ],
        ]
        passed = True
        for command in commands:
            completed = subprocess.run(
                [sys.executable, "-m", *command, fork], env=environment
            )
            passed &= completed.returncode == 0
        lint = _spec_lint.__name__
        script = (
            "import sys\n"
            f"from {__name__} import {lint}\n"
            f"sys.exit({lint}({feature.name!r}, {template.short_name!r}))"
        )
        completed = subprocess.run(
            [sys.executable, "-c", script], env=environment
        )
        passed &= completed.returncode == 0
        return passed


def _spec_lint(name: str, base: str) -> int:
    """
    Run the specification lints on the built feature fork `name` as the fork
    that follows `base`, and print what they find. Expects the copy of
    `ethereum` holding the feature fork first on the path.

    Only the feature fork is linted, placed right after its base among all
    the scheduled forks. Linting the later forks too would make the feature
    the predecessor of the fork after its base, and dropping them would hide
    imports from forks newer than the base.

    Return 1 if anything was found, else 0.
    """
    from .lint import Linter

    forks = Hardfork.discover()
    feature = next(fork for fork in forks if fork.short_name == name)
    forks.remove(feature)
    position = 1 + next(
        index for index, fork in enumerate(forks) if fork.short_name == base
    )
    forks.insert(position, feature)

    found = 0
    for lint in Linter.discover_lints():
        for diagnostic in lint.lint(forks, position):
            print(f"{name} - {type(lint).__name__}: {diagnostic.message}")
            found += 1
    return 1 if found else 0


class FeatureBuilder(ForkBuilder):
    """
    Builds a feature's fork: a copy of the template fork with the feature's
    changes applied.
    """

    feature: Final[Feature]

    def __init__(
        self, feature: Feature, template_fork: str, new_fork: str
    ) -> None:
        super().__init__(template_fork, new_fork)
        self.feature = feature

    @override
    def _transform(self, package: Path) -> None:
        self.feature.apply(package)


def _fork_root(fork: Hardfork) -> Path:
    if fork.path is None:
        raise FeatureError(f"fork `{fork.short_name}` has no path")
    return Path(fork.path)


def _module_name(relative: Path) -> str:
    """
    Return the dotted name, within the fork, of the module at `relative`.
    """
    parts = list(relative.with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _ast_definitions(source: str) -> Dict[str, ast.stmt]:
    """
    Map each name defined at the top level of `source` to its definition.
    """
    definitions: Dict[str, ast.stmt] = {}
    for node in ast.parse(source).body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            definitions[node.name] = node
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    definitions[target.id] = node
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name):
                definitions[node.target.id] = node
    return definitions


def _hash_definition(node: ast.stmt) -> str:
    """
    Hash the code of a definition, ignoring docstrings, comments and layout.

    Docstrings (including the ones that follow class attributes) mention the
    fork by name, so leaving them out keeps the hash stable when the feature
    moves onto a newer fork.
    """
    for child in ast.walk(node):
        for field in ("body", "orelse", "finalbody"):
            statements = getattr(child, field, None)
            if not isinstance(statements, list):
                continue
            kept = [
                statement
                for statement in statements
                if not (
                    isinstance(statement, ast.Expr)
                    and isinstance(statement.value, ast.Constant)
                    and isinstance(statement.value.value, str)
                )
            ]
            if kept != statements:
                setattr(child, field, kept or [ast.Pass()])
    return hashlib.sha256(ast.dump(node).encode()).hexdigest()


def _is_docstring(statement: cst.CSTNode) -> bool:
    return (
        isinstance(statement, cst.SimpleStatementLine)
        and len(statement.body) == 1
        and isinstance(statement.body[0], cst.Expr)
        and isinstance(
            statement.body[0].value,
            (cst.SimpleString, cst.ConcatenatedString),
        )
    )


def _is_import(statement: cst.CSTNode) -> bool:
    return isinstance(statement, cst.SimpleStatementLine) and any(
        isinstance(small, (cst.Import, cst.ImportFrom))
        for small in statement.body
    )


def _defined_names(statement: cst.CSTNode) -> Set[str]:
    """
    Return the names that `statement` defines, not counting imports.
    """
    if isinstance(statement, (cst.FunctionDef, cst.ClassDef)):
        return {statement.name.value}
    names = set()
    if isinstance(statement, cst.SimpleStatementLine):
        for small in statement.body:
            if isinstance(small, cst.Assign):
                for target in small.targets:
                    if isinstance(target.target, cst.Name):
                        names.add(target.target.value)
            elif isinstance(small, cst.AnnAssign):
                if isinstance(small.target, cst.Name):
                    names.add(small.target.value)
    return names


def _imported_name(alias: cst.ImportAlias) -> str:
    return (alias.evaluated_alias or alias.evaluated_name).split(".")[0]


def _import_sources(statement: cst.CSTNode) -> Dict[str, str]:
    """
    Map each name that the imports in `statement` bind to where it comes
    from, such as `ethereum.state:Account` or `..vm:Evm`.
    """
    sources = {}
    if isinstance(statement, cst.SimpleStatementLine):
        for small in statement.body:
            if isinstance(small, cst.Import):
                for alias in small.names:
                    sources[_imported_name(alias)] = alias.evaluated_name
            elif isinstance(small, cst.ImportFrom):
                if isinstance(small.names, cst.ImportStar):
                    raise FeatureError("star imports are not supported")
                module = "." * len(small.relative)
                if small.module is not None:
                    module += get_full_name_for_node_or_raise(small.module)
                for alias in small.names:
                    sources[_imported_name(alias)] = (
                        f"{module}:{alias.evaluated_name}"
                    )
    return sources


def _imported_names(statement: cst.CSTNode) -> Set[str]:
    return set(_import_sources(statement))


Unit = Tuple[Set[str], List[cst.BaseStatement]]


def _units(body: Sequence[cst.BaseStatement]) -> List[Unit]:
    """
    Group `body` into definitions, each with the docstrings that follow it.
    """
    units: List[Unit] = []
    for statement in body:
        if _is_docstring(statement) and units and units[-1][0]:
            units[-1][1].append(statement)
        else:
            units.append((_defined_names(statement), [statement]))
    return units


def _flatten(units: List[Unit]) -> List[cst.BaseStatement]:
    return [statement for _, statements in units for statement in statements]


def _overlay(target_source: str, overlay_source: str) -> str:
    """
    Apply the overlay in `overlay_source` to the module in `target_source`.
    """
    target = cst.parse_module(target_source)
    overlay = list(cst.parse_module(overlay_source).body)
    body: List[cst.BaseStatement] = list(target.body)

    if overlay and _is_docstring(overlay[0]):
        if body and _is_docstring(body[0]):
            body[0] = overlay[0]
        else:
            if body:
                body[0] = _with_blank_lines(body[0], 1)
            body.insert(0, overlay[0])
        overlay = overlay[1:]

    imports = [statement for statement in overlay if _is_import(statement)]
    definitions = [s for s in overlay if not _is_import(s)]

    units = _units(body)
    # New definitions wait for the next definition that the overlay replaces
    # and go right before it (or at the end of the module), so the built
    # module keeps the overlay's order: a replaced definition can use a new
    # one defined above it in the overlay.
    pending: List[Unit] = []
    for names, statements in _units(definitions):
        if not names:
            raise FeatureError(
                "overlays may only hold imports and definitions, found: "
                + target.code_for_node(statements[0]).strip()
            )
        index = next(
            (
                i
                for i, (target_names, _) in enumerate(units)
                if names & target_names
            ),
            None,
        )
        if index is None:
            statements = [_with_blank_lines(statements[0], 2), *statements[1:]]
            pending.append((names, statements))
            continue
        target_names, target_statements = units[index]
        if names != target_names:
            raise FeatureError(
                f"cannot replace {sorted(target_names)} with {sorted(names)}"
            )
        # Keep the fork's spacing and comments above the definition.
        statements = [
            statements[0].with_changes(
                leading_lines=_leading_lines(target_statements[0])
            ),
            *statements[1:],
        ]
        units[index : index + 1] = [*pending, (names, statements)]
        pending = []
    units.extend(pending)
    body = _flatten(units)
    if body:
        body[0] = _with_blank_lines(body[0], 0)

    # Where each name the module binds comes from (`None` if defined here).
    bound: Dict[str, str | None] = {}
    for statement in body:
        bound.update(dict.fromkeys(_defined_names(statement)))
        bound.update(_import_sources(statement))
    # Add missing imports after the last import, or after the docstring.
    last_import = max(
        (index for index, s in enumerate(body) if _is_import(s)),
        default=0 if body and _is_docstring(body[0]) else -1,
    )
    for statement in imports:
        missing = _imports_missing(statement, bound)
        if missing is not None:
            last_import += 1
            body.insert(last_import, missing)
            bound.update(_import_sources(missing))

    return target.with_changes(body=body).code


def _leading_lines(statement: cst.BaseStatement) -> Sequence[cst.EmptyLine]:
    assert isinstance(
        statement, (cst.SimpleStatementLine, cst.BaseCompoundStatement)
    )
    return statement.leading_lines


def _with_blank_lines(
    statement: cst.BaseStatement, count: int
) -> cst.BaseStatement:
    """
    Put exactly `count` blank lines above `statement`, keeping its comments.
    """
    comments = [
        line for line in _leading_lines(statement) if line.comment is not None
    ]
    return statement.with_changes(
        leading_lines=[*(cst.EmptyLine() for _ in range(count)), *comments]
    )


def _imports_missing(
    statement: cst.BaseStatement, bound: Dict[str, str | None]
) -> cst.SimpleStatementLine | None:
    """
    Return the part of the import `statement` that binds names not in
    `bound`, or `None` if it binds nothing new.

    Raise `FeatureError` if the fork already binds one of the names to
    something else, since the overlay would silently use the fork's.
    """
    assert isinstance(statement, cst.SimpleStatementLine)
    sources = _import_sources(statement)
    for name, source in sources.items():
        if name in bound and bound[name] != source:
            raise FeatureError(
                f"overlay imports `{name}` from `{source}`, but the fork "
                f"binds it from `{bound[name] or 'its own definition'}`"
            )
    (node,) = statement.body
    assert isinstance(node, (cst.Import, cst.ImportFrom))
    assert not isinstance(node.names, cst.ImportStar)
    aliases = [
        alias.with_changes(comma=cst.MaybeSentinel.DEFAULT)
        for alias in node.names
        if _imported_name(alias) not in bound
    ]
    if not aliases:
        return None
    if isinstance(node, cst.ImportFrom):
        node = node.with_changes(names=aliases, lpar=None, rpar=None)
    else:
        node = node.with_changes(names=aliases)
    return statement.with_changes(body=[node], leading_lines=[])


def _remove(package: Path, removal: str) -> None:
    """
    Remove a file (`a/b.py`) or a definition (`a.b.NAME` or
    `a.b.Class.NAME`) from the fork in `package`.
    """
    if removal.endswith(".py"):
        path = package / removal
        if not path.is_file():
            raise FeatureError(f"cannot remove missing file `{removal}`")
        path.unlink()
        return

    source = _source_file_for(package, removal)
    module = _module_name(source.relative_to(package))
    if module:
        chain = removal.removeprefix(f"{module}.").split(".")
    else:
        chain = removal.split(".")

    tree = cst.parse_module(source.read_text())
    if len(chain) == 1:
        body = _without(tree.body, chain[0], removal)
        body = _without_export(body, chain[0])
    elif len(chain) == 2:
        body = list(tree.body)
        for index, statement in enumerate(body):
            if (
                isinstance(statement, cst.ClassDef)
                and statement.name.value == chain[0]
            ):
                block = statement.body
                assert isinstance(block, cst.IndentedBlock)
                inner = _without(block.body, chain[1], removal)
                body[index] = statement.with_changes(
                    body=block.with_changes(body=inner)
                )
                break
        else:
            raise FeatureError(f"cannot remove missing `{removal}`")
    else:
        raise FeatureError(f"cannot remove nested `{removal}`")

    source.write_text(tree.with_changes(body=body).code)


def _without(
    body: Sequence[cst.BaseStatement], name: str, removal: str
) -> List[cst.BaseStatement]:
    """
    Return `body` without the definition or import of `name`.
    """
    units = _units(body)
    for index, (names, statements) in enumerate(units):
        if name in names:
            if names != {name}:
                raise FeatureError(f"`{removal}` shares its statement")
            del units[index]
            # Keep the spacing that came before the removed definition.
            if index < len(units):
                following = units[index][1]
                if not _leading_lines(following[0]):
                    following[0] = following[0].with_changes(
                        leading_lines=_leading_lines(statements[0])
                    )
            return _flatten(units)

    result = _flatten(units)
    for index, statement in enumerate(result):
        if name not in _imported_names(statement):
            continue
        assert isinstance(statement, cst.SimpleStatementLine)
        (node,) = statement.body
        assert isinstance(node, (cst.Import, cst.ImportFrom))
        assert not isinstance(node.names, cst.ImportStar)
        aliases = [a for a in node.names if _imported_name(a) != name]
        if not aliases:
            del result[index]
        else:
            if isinstance(node, cst.ImportFrom) and node.lpar is None:
                aliases[-1] = aliases[-1].with_changes(
                    comma=cst.MaybeSentinel.DEFAULT
                )
            result[index] = statement.with_changes(
                body=[node.with_changes(names=aliases)]
            )
        return result

    raise FeatureError(f"cannot remove missing `{removal}`")


def _without_export(
    body: List[cst.BaseStatement], name: str
) -> List[cst.BaseStatement]:
    """
    Drop `name` from the module's `__all__`, if it is listed there.
    """
    for index, statement in enumerate(body):
        if "__all__" not in _defined_names(statement):
            continue
        assert isinstance(statement, cst.SimpleStatementLine)
        (node,) = statement.body
        assert isinstance(node, (cst.Assign, cst.AnnAssign))
        value = node.value
        if not isinstance(value, (cst.Tuple, cst.List)):
            raise FeatureError("`__all__` must be a tuple or a list")
        elements = [
            element
            for element in value.elements
            if not (
                isinstance(element.value, cst.SimpleString)
                and element.value.evaluated_value == name
            )
        ]
        body[index] = statement.with_changes(
            body=[
                node.with_changes(value=value.with_changes(elements=elements))
            ]
        )
    return body


def main() -> None:
    """
    Build a feature's fork for reading, or refresh the feature's lock.
    """
    parser = argparse.ArgumentParser(
        description="Build or check an unscheduled feature."
    )
    parser.add_argument("feature", help="snake case name of the feature")
    parser.add_argument(
        "--base",
        help="fork to build on (defaults to the feature's base fork)",
    )
    parser.add_argument(
        "--update-lock",
        action="store_true",
        help="record the fork definitions the feature replaces as reviewed",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="write the feature's full fork into this directory",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="lint and type check the feature's full fork",
    )
    options = parser.parse_args()

    feature = Feature.by_name(options.feature)
    if options.base is None:
        template = feature.base_fork()
    else:
        template = Hardfork.by_short_name(options.base)

    if options.update_lock:
        feature.write_lock(template)

    if options.check:
        if not check(feature, template):
            sys.exit(f"feature `{feature.name}` failed its checks")
        print(f"feature `{feature.name}` passed its checks")
    elif options.output is not None:
        feature.check_lock(template)
        builder = FeatureBuilder(feature, template.short_name, feature.name)
        builder.output = options.output
        builder.force = True
        builder.build()
    elif not options.update_lock:
        with feature.build(template):
            pass
        print(f"feature `{feature.name}` builds on `{template.short_name}`")
