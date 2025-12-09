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
import json
import sys
from pathlib import Path


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


def load_existing_config(config_file: Path) -> dict[str, list[int]]:
    """Load existing config from .fixed_opcode_counts.json."""
    if not config_file.exists():
        return {}

    try:
        data = json.loads(config_file.read_text())
        return data.get("scenario_configs", {})
    except (json.JSONDecodeError, KeyError):
        return {}


def categorize_patterns(
    config: dict[str, list[int]], pattern_sources: dict[str, Path]
) -> dict[str, list[str]]:
    """
    Categorize patterns by deriving category from source file name.

    Example: test_arithmetic.py -> ARITHMETIC
    """
    categories: dict[str, list[str]] = {}

    for pattern in config.keys():
        if pattern in pattern_sources:
            source_file = pattern_sources[pattern]
            file_name = source_file.stem
            if file_name.startswith("test_"):
                category = file_name[5:].upper()  # Remove "test_" prefix
            else:
                category = "OTHER"
        else:
            category = "OTHER"

        if category not in categories:
            categories[category] = []
        categories[category].append(pattern)

    return {k: sorted(v) for k, v in sorted(categories.items())}


def generate_config_json(
    config: dict[str, list[int]],
    pattern_sources: dict[str, Path],
) -> str:
    """Generate the JSON config file content."""
    categories = categorize_patterns(config, pattern_sources)

    scenario_configs: dict[str, list[int]] = {}
    for _, patterns in categories.items():
        for pattern in patterns:
            scenario_configs[pattern] = config[pattern]

    output = {"scenario_configs": scenario_configs}

    return json.dumps(output, indent=2) + "\n"


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

    existing = load_existing_config(config_file)
    print(f"Loaded {len(existing)} existing entries")

    detected_keys = set(detected.keys())
    existing_keys = set(existing.keys())
    new_patterns = sorted(detected_keys - existing_keys)
    obsolete_patterns = sorted(existing_keys - detected_keys)

    merged = detected.copy()
    for pattern, counts in existing.items():
        if pattern in detected_keys:
            merged[pattern] = counts

    print("\n" + "=" * 60)
    print(f"Detected {len(detected)} patterns in tests")
    print(f"Existing entries: {len(existing)}")

    if new_patterns:
        print(f"\n+ Found {len(new_patterns)} NEW patterns:")
        for p in new_patterns[:15]:
            print(f"    {p}")
        if len(new_patterns) > 15:
            print(f"    ... and {len(new_patterns) - 15} more")

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

    content = generate_config_json(merged, pattern_sources)
    config_file.write_text(content)
    print(f"\nUpdated {config_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
