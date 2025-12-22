"""
Parser to analyze benchmark tests and maintain the opcode counts mapping.

This script uses Python's AST to analyze benchmark tests and generate/update
the scenario configs in `.fixed_opcode_counts.json`.

Usage:
    uv run benchmark_parser           # Update `.fixed_opcode_counts.json`
    uv run benchmark_parser --check   # Check for new/missing entries (CI)
"""

import argparse
import ast
import re
import sys
from pathlib import Path

from execution_testing.cli.pytest_commands.plugins.shared.benchmarking import (
    OpcodeCountsConfig,
)


def is_broader_pattern(pattern: str, detected_patterns: set[str]) -> bool:
    """
    Check if a pattern is a broader match that covers any detected patterns.

    A broader pattern like "test_bitwise.*" covers more specific patterns like
    "test_bitwise.*AND.*". These user-defined broader patterns should be preserved
    since they provide a convenient way to configure multiple tests at once.

    Returns True if the pattern matches at least one detected pattern.
    """
    try:
        regex = re.compile(pattern)
        for detected in detected_patterns:
            # Check if the broader pattern matches the detected pattern string
            # e.g., "test_bitwise.*" matches "test_bitwise.*AND.*"
            if regex.search(detected):
                return True
    except re.error:
        pass
    return False


def is_covered_by_broader(pattern: str, broader_patterns: list[str]) -> bool:
    """
    Check if a pattern is covered by any of the broader patterns.

    For example, "test_push.*PUSH16.*" is covered by "test_push.*".
    This is used to skip adding new detected patterns that are already
    covered by user-defined broader patterns.

    Returns True if the pattern is covered by at least one broader pattern.
    """
    for broader in broader_patterns:
        try:
            if re.search(broader, pattern):
                return True
        except re.error:
            continue
    return False


def get_repo_root() -> Path:
    """Get the repository root directory."""
    current = Path.cwd()
    while current != current.parent:
        if (current / "tests" / "benchmark").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find repository root")


def get_benchmark_dir() -> Path:
    """Get the benchmark tests directory."""
    return get_repo_root() / "tests" / "benchmark"


def get_config_file() -> Path:
    """Get the .fixed_opcode_counts.json config file path."""
    return get_repo_root() / ".fixed_opcode_counts.json"


class OpcodeExtractor(ast.NodeVisitor):
    """Extract opcode parametrizations from benchmark test functions."""

    def __init__(self, source_code: str):
        self.source_code = source_code
        self.patterns: list[str] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function definitions and extract opcode patterns."""
        if not node.name.startswith("test_"):
            return

        # Check if function has benchmark_test parameter
        if not self._has_benchmark_test_param(node):
            return

        # Filter for code generator usage (required for fixed-opcode-count mode)
        if not self._uses_code_generator(node):
            return

        # Extract opcode parametrizations
        test_name = node.name
        opcodes = self._extract_opcodes(node)

        if opcodes:
            # Test parametrizes on opcodes - create pattern for each
            for opcode in opcodes:
                pattern = f"{test_name}.*{opcode}.*"
                self.patterns.append(pattern)
        else:
            # Test doesn't parametrize on opcodes - use test name only
            pattern = f"{test_name}.*"
            self.patterns.append(pattern)

    def _has_benchmark_test_param(self, node: ast.FunctionDef) -> bool:
        """Check if function has benchmark_test parameter."""
        return any(arg.arg == "benchmark_test" for arg in node.args.args)

    def _uses_code_generator(self, node: ast.FunctionDef) -> bool:
        """Check if function body uses code_generator parameter."""
        func_start = node.lineno - 1
        func_end = node.end_lineno
        if func_end is None:
            return False
        func_source = "\n".join(
            self.source_code.splitlines()[func_start:func_end]
        )
        return "code_generator=" in func_source

    def _extract_opcodes(self, node: ast.FunctionDef) -> list[str]:
        """Extract opcode values from @pytest.mark.parametrize decorators."""
        opcodes: list[str] = []

        for decorator in node.decorator_list:
            if not self._is_parametrize_decorator(decorator):
                continue

            if not isinstance(decorator, ast.Call) or len(decorator.args) < 2:
                continue

            # Get parameter names (first arg)
            param_names = decorator.args[0]
            if isinstance(param_names, ast.Constant):
                param_str = str(param_names.value).lower()
            else:
                continue

            # Check if "opcode" is in parameter names
            if "opcode" not in param_str:
                continue

            # Extract opcode values from second arg (the list)
            param_values = decorator.args[1]
            opcodes.extend(self._parse_opcode_values(param_values))

        return opcodes

    def _is_parametrize_decorator(self, decorator: ast.expr) -> bool:
        """Check if decorator is @pytest.mark.parametrize."""
        if isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Attribute):
                if (
                    isinstance(decorator.func.value, ast.Attribute)
                    and decorator.func.value.attr == "mark"
                    and decorator.func.attr == "parametrize"
                ):
                    return True
        return False

    def _parse_opcode_values(self, values_node: ast.expr) -> list[str]:
        """Parse opcode values from the parametrize list."""
        opcodes: list[str] = []

        if not isinstance(values_node, (ast.List, ast.Tuple)):
            return opcodes

        for element in values_node.elts:
            opcode_name = self._extract_opcode_name(element)
            if opcode_name:
                opcodes.append(opcode_name)

        return opcodes

    def _extract_opcode_name(self, node: ast.expr) -> str | None:
        """
        Extract opcode name from various AST node types.

        Supported patterns (opcode must be first element):

        Case 1 - Direct opcode reference:
            @pytest.mark.parametrize("opcode", [Op.ADD, Op.MUL])
            Result: ["ADD", "MUL"]

        Case 2a - pytest.param with direct opcode:
            @pytest.mark.parametrize("opcode", [pytest.param(Op.ADD, id="add")])
            Result: ["ADD"]

        Case 2b - pytest.param with tuple (opcode first):
            @pytest.mark.parametrize("opcode,arg", [pytest.param((Op.ADD, 123))])
            Result: ["ADD"]

        Case 3 - Plain tuple (opcode first):
            @pytest.mark.parametrize("opcode,arg", [(Op.ADD, 123), (Op.MUL, 456)])
            Result: ["ADD", "MUL"]
        """
        # Case 1: Direct opcode - Op.ADD
        if isinstance(node, ast.Attribute):
            return node.attr

        # Case 2: pytest.param(Op.ADD, ...) or pytest.param((Op.ADD, x), ...)
        if isinstance(node, ast.Call):
            if len(node.args) > 0:
                first_arg = node.args[0]
                # Case 2a: pytest.param(Op.ADD, ...)
                if isinstance(first_arg, ast.Attribute):
                    return first_arg.attr
                # Case 2b: pytest.param((Op.ADD, x), ...)
                elif isinstance(first_arg, ast.Tuple) and first_arg.elts:
                    first_elem = first_arg.elts[0]
                    if isinstance(first_elem, ast.Attribute):
                        return first_elem.attr

        # Case 3: Plain tuple - (Op.ADD, args)
        if isinstance(node, ast.Tuple) and node.elts:
            first_elem = node.elts[0]
            if isinstance(first_elem, ast.Attribute):
                return first_elem.attr

        return None


def scan_benchmark_tests(
    base_path: Path,
) -> tuple[dict[str, list[int]], dict[str, Path]]:
    """
    Scan benchmark test files and extract opcode patterns.

    Returns:
        Tuple of (config, pattern_sources) where:
        - config: mapping of pattern -> opcode counts
        - pattern_sources: mapping of pattern -> source file path
    """
    config: dict[str, list[int]] = {}
    pattern_sources: dict[str, Path] = {}
    default_counts = [1]

    test_files = [
        f
        for f in base_path.rglob("test_*.py")
        if "configs" not in str(f) and "stateful" not in str(f)
    ]

    for test_file in test_files:
        try:
            source = test_file.read_text()
            tree = ast.parse(source)

            extractor = OpcodeExtractor(source)
            extractor.visit(tree)

            for pattern in extractor.patterns:
                if pattern not in config:
                    config[pattern] = default_counts
                    pattern_sources[pattern] = test_file
        except Exception as e:
            print(f"Warning: Failed to parse {test_file}: {e}")
            continue

    return config, pattern_sources


def load_existing_config(config_file: Path) -> OpcodeCountsConfig:
    """Load existing config from .fixed_opcode_counts.json."""
    if not config_file.exists():
        return OpcodeCountsConfig()
    return OpcodeCountsConfig.model_validate_json(config_file.read_bytes())


def categorize_patterns(
    config: dict[str, list[int]], pattern_sources: dict[str, Path]
) -> dict[str, list[str]]:
    """
    Categorize patterns by deriving category from source file name.

    For detected patterns: use source file name (e.g., test_arithmetic.py -> ARITHMETIC)
    For user-defined broader patterns: find a detected pattern it covers and use that
    source file (e.g., test_push.* covers test_push.*PUSH0.* -> use test_push.py -> PUSH)

    Categories are ordered by folder structure (instruction, precompile, scenario),
    then alphabetically within each folder.
    """
    # Track category -> (folder, patterns)
    category_info: dict[str, tuple[str, list[str]]] = {}

    for pattern in config.keys():
        category = "OTHER_CATEGORY"
        folder = "OTHER_FOLDER"  # Sort last

        if pattern in pattern_sources:
            # Detected pattern: use its source file
            source_file = pattern_sources[pattern]
            file_name = source_file.stem
            folder = source_file.parent.name
            if file_name.startswith("test_"):
                category = file_name[5:].upper()
        else:
            # User-defined pattern: find a detected pattern it covers
            try:
                regex = re.compile(pattern)
                for detected, source_file in pattern_sources.items():
                    if regex.search(detected):
                        file_name = source_file.stem
                        folder = source_file.parent.name
                        if file_name.startswith("test_"):
                            category = file_name[5:].upper()
                        break
            except re.error:
                pass

        if category not in category_info:
            category_info[category] = (folder, [])
        category_info[category][1].append(pattern)

    # Sort by folder first, then by category name within each folder
    sorted_categories = sorted(
        category_info.items(),
        key=lambda item: (item[1][0], item[0]),  # (folder, category_name)
    )

    return {k: sorted(patterns) for k, (_, patterns) in sorted_categories}


def generate_config_json(
    config: dict[str, list[int]],
    pattern_sources: dict[str, Path],
    default_counts: list[int],
) -> OpcodeCountsConfig:
    """Generate the JSON config file content."""
    categories = categorize_patterns(config, pattern_sources)

    scenario_configs: dict[str, list[int]] = {}
    output = OpcodeCountsConfig(scenario_configs=scenario_configs)
    for _, patterns in categories.items():
        for pattern in patterns:
            output.scenario_configs[pattern] = config[pattern]

    return OpcodeCountsConfig(
        scenario_configs=scenario_configs,
        default_counts=default_counts,
    )


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze benchmark tests and maintain opcode count mapping"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check for new/missing entries (CI mode, exits 1 if out of sync)",
    )
    args = parser.parse_args()

    try:
        benchmark_dir = get_benchmark_dir()
        config_file = get_config_file()
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    print(f"Scanning benchmark tests in {benchmark_dir}...")
    detected, pattern_sources = scan_benchmark_tests(benchmark_dir)
    print(f"Detected {len(detected)} opcode patterns")

    existing_file = load_existing_config(config_file)
    existing = existing_file.scenario_configs
    print(f"Loaded {len(existing)} existing entries")

    detected_keys = set(detected.keys())
    existing_keys = set(existing.keys())
    potentially_obsolete = existing_keys - detected_keys

    # Separate broader patterns (user-defined, cover detected patterns) from truly obsolete
    broader_patterns: list[str] = []
    obsolete_patterns: list[str] = []
    for pattern in potentially_obsolete:
        if is_broader_pattern(pattern, detected_keys):
            broader_patterns.append(pattern)
        else:
            obsolete_patterns.append(pattern)
    broader_patterns = sorted(broader_patterns)
    obsolete_patterns = sorted(obsolete_patterns)

    # Filter new patterns: skip those already covered by broader patterns
    all_new_patterns = detected_keys - existing_keys
    new_patterns: list[str] = []
    skipped_patterns: list[str] = []
    for pattern in sorted(all_new_patterns):
        if is_covered_by_broader(pattern, broader_patterns):
            skipped_patterns.append(pattern)
        else:
            new_patterns.append(pattern)

    # Merge: start with detected, preserve existing counts, and keep broader patterns
    # But skip detected patterns that are covered by broader patterns (unless in existing)
    merged: dict[str, list[int]] = {}
    for pattern, counts in detected.items():
        if pattern in existing_keys:
            # Preserve existing counts for patterns that were already in config
            merged[pattern] = existing[pattern]
        elif not is_covered_by_broader(pattern, broader_patterns):
            # Add new detected patterns only if not covered by broader patterns
            merged[pattern] = counts
    # Add broader patterns
    for pattern in broader_patterns:
        merged[pattern] = existing[pattern]

    print("\n" + "=" * 60)
    print(f"Detected {len(detected)} patterns in tests")
    print(f"Existing entries: {len(existing)}")

    if new_patterns:
        print(f"\n+ Found {len(new_patterns)} NEW patterns:")
        for p in new_patterns[:15]:
            print(f"    {p}")
        if len(new_patterns) > 15:
            print(f"    ... and {len(new_patterns) - 15} more")

    if skipped_patterns:
        print(
            f"\n  Skipped {len(skipped_patterns)} patterns "
            "(covered by broader patterns)"
        )

    if broader_patterns:
        print(
            f"\n~ Preserving {len(broader_patterns)} BROADER patterns (user-defined):"
        )
        for p in broader_patterns[:15]:
            print(f"    {p}")
        if len(broader_patterns) > 15:
            print(f"    ... and {len(broader_patterns) - 15} more")

    if obsolete_patterns:
        print(f"\n- Found {len(obsolete_patterns)} OBSOLETE patterns:")
        for p in obsolete_patterns[:15]:
            print(f"    {p}")
        if len(obsolete_patterns) > 15:
            print(f"    ... and {len(obsolete_patterns) - 15} more")

    if not new_patterns and not obsolete_patterns:
        print("\nConfiguration is up to date!")

    print("=" * 60)

    if args.check:
        if new_patterns or obsolete_patterns:
            print("\nRun 'uv run benchmark_parser' (without --check) to sync.")
            return 1
        return 0

    for pattern in obsolete_patterns:
        print(f"Removing obsolete: {pattern}")
        if pattern in merged:
            del merged[pattern]

    content = generate_config_json(
        merged, pattern_sources, existing_file.default_counts
    )
    config_file.write_text(
        content.model_dump_json(exclude_defaults=True, indent=2)
    )
    print(f"\nUpdated {config_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
