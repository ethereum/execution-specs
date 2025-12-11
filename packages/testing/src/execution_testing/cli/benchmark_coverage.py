"""
Analyze benchmark test coverage for opcodes across different benchmark modes.

This script scans benchmark tests to determine which opcodes are covered by:
- worst-case-benchmark mode (--gas-benchmark-values): tests using benchmark_test
- fixed-opcode-count mode (--fixed-opcode-count): tests using benchmark_test + code_generator

Usage:
    uv run benchmark_coverage           # Generate markdown coverage report
    uv run benchmark_coverage --json    # Output as JSON
"""

import argparse
import ast
import json
import sys
from collections import defaultdict
from pathlib import Path

from ethereum.forks.osaka.vm.instructions import Ops


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


def get_opcode_values() -> dict[str, int]:
    """Build opcode name -> value mapping from Ops enum."""
    return {op.name: op.value for op in Ops}


# Build OPCODE_VALUES from the Ops enum
OPCODE_VALUES: dict[str, int] = get_opcode_values()

# Opcode aliases: map old/alternate names to canonical names in Ops enum
# When tests use an alias, coverage is attributed to the canonical opcode
OPCODE_ALIASES: dict[str, str] = {
    "SHA3": "KECCAK",
    "KECCAK256": "KECCAK",
    "DIFFICULTY": "PREVRANDAO",
}


def normalize_opcode(opcode: str) -> str:
    """Normalize opcode name using aliases."""
    return OPCODE_ALIASES.get(opcode, opcode)


def opcode_sort_key(opcode: str) -> tuple[int, str]:
    """Return sort key for an opcode (by opcode value, then alphabetically)."""
    if opcode in OPCODE_VALUES:
        return (OPCODE_VALUES[opcode], opcode)
    return (0x1000, opcode)  # Unknown opcodes go at the end


class BenchmarkCoverageExtractor(ast.NodeVisitor):
    """Extract benchmark test coverage information from test functions."""

    def __init__(self, source_code: str, file_path: Path):
        self.source_code = source_code
        self.file_path = file_path
        # Maps opcode -> list of (test_name, supports_fixed_opcode_count)
        self.coverage: dict[str, list[tuple[str, bool]]] = defaultdict(list)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function definitions and extract opcode coverage."""
        if not node.name.startswith("test_"):
            return

        # Check if function has benchmark_test parameter
        if not self._has_benchmark_test_param(node):
            return

        # Check if function uses code_generator
        uses_code_generator = self._uses_code_generator(node)

        # Check if target_opcode= is explicitly used in benchmark_test() call
        has_target_opcode = self._has_target_opcode(node)

        # Extract opcodes for coverage tracking
        # For fixed-opcode-count: ONLY if target_opcode= is present AND code_generator=
        # For worst-case-benchmark: from target_opcode= OR parametrized opcode
        opcodes_from_target = self._extract_opcodes_from_target_opcode(node)
        opcodes_from_parametrize = self._extract_parametrized_opcodes(node)

        test_name = node.name

        if has_target_opcode:
            # Test explicitly declares target_opcode - eligible for fixed-opcode-count
            opcodes = (
                opcodes_from_target
                if opcodes_from_target
                else opcodes_from_parametrize
            )
            supports_fixed = uses_code_generator
            for opcode in opcodes:
                self.coverage[opcode].append((test_name, supports_fixed))
        else:
            # No target_opcode= - worst-case-benchmark only (from parametrize)
            for opcode in opcodes_from_parametrize:
                self.coverage[opcode].append((test_name, False))

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

    def _has_target_opcode(self, node: ast.FunctionDef) -> bool:
        """Check if target_opcode= is used in benchmark_test() call."""
        func_start = node.lineno - 1
        func_end = node.end_lineno
        if func_end is None:
            return False
        func_source = "\n".join(
            self.source_code.splitlines()[func_start:func_end]
        )
        return "target_opcode=" in func_source

    def _extract_opcodes_from_target_opcode(
        self, node: ast.FunctionDef
    ) -> list[str]:
        """
        Extract opcodes from target_opcode= in benchmark_test() call.

        Handles:
        1. target_opcode=Op.XXX (direct opcode)
        2. target_opcode=opcode (parametrized variable)
        """
        # First try direct target_opcode=Op.XXX
        direct_opcodes = self._extract_direct_target_opcodes(node)
        if direct_opcodes:
            return direct_opcodes

        # Check if target_opcode= references a parametrized variable
        if self._has_target_opcode(node):
            return self._extract_parametrized_opcodes(node)

        return []

    def _extract_direct_target_opcodes(
        self, node: ast.FunctionDef
    ) -> list[str]:
        """Extract direct target_opcode=Op.XXX from benchmark_test() calls."""
        opcodes: list[str] = []

        for child in ast.walk(node):
            if not isinstance(child, ast.Call):
                continue

            # Look for benchmark_test(...) calls
            if (
                isinstance(child.func, ast.Name)
                and child.func.id == "benchmark_test"
            ):
                for keyword in child.keywords:
                    if keyword.arg == "target_opcode":
                        opcode = self._extract_opcode_from_expr(keyword.value)
                        if opcode:
                            opcodes.append(opcode)

        return opcodes

    def _extract_opcode_from_expr(self, expr: ast.expr) -> str | None:
        """Extract opcode name from an expression like Op.ADD."""
        if isinstance(expr, ast.Attribute):
            # Op.ADD -> "ADD"
            return expr.attr
        return None

    def _extract_parametrized_opcodes(
        self, node: ast.FunctionDef
    ) -> list[str]:
        """Extract opcodes from @pytest.mark.parametrize decorators."""
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

        Handles:
        - Op.ADD (direct)
        - pytest.param(Op.ADD, ...)
        - pytest.param((Op.ADD, x), ...)
        - (Op.ADD, x) tuple
        """
        # Direct opcode - Op.ADD
        if isinstance(node, ast.Attribute):
            return node.attr

        # pytest.param(Op.ADD, ...) or pytest.param((Op.ADD, x), ...)
        if isinstance(node, ast.Call):
            if len(node.args) > 0:
                first_arg = node.args[0]
                if isinstance(first_arg, ast.Attribute):
                    return first_arg.attr
                elif isinstance(first_arg, ast.Tuple) and first_arg.elts:
                    first_elem = first_arg.elts[0]
                    if isinstance(first_elem, ast.Attribute):
                        return first_elem.attr

        # Plain tuple - (Op.ADD, args)
        if isinstance(node, ast.Tuple) and node.elts:
            first_elem = node.elts[0]
            if isinstance(first_elem, ast.Attribute):
                return first_elem.attr

        return None


def scan_benchmark_tests(
    base_path: Path,
) -> dict[str, dict[str, list[str]]]:
    """
    Scan benchmark test files and extract opcode coverage.

    Returns:
        Dict mapping opcode -> {
            "worst_case_benchmark": [test_names...],
            "fixed_opcode_count": [test_names...]
        }
    """
    # opcode -> {"worst_case_benchmark": [...], "fixed_opcode_count": [...]}
    coverage: dict[str, dict[str, list[str]]] = defaultdict(
        lambda: {"worst_case_benchmark": [], "fixed_opcode_count": []}
    )

    test_files = [
        f
        for f in base_path.rglob("test_*.py")
        if "configs" not in str(f) and "stateful" not in str(f)
    ]

    for test_file in test_files:
        try:
            source = test_file.read_text()
            tree = ast.parse(source)

            extractor = BenchmarkCoverageExtractor(source, test_file)
            extractor.visit(tree)

            for opcode, tests in extractor.coverage.items():
                # Normalize opcode name (handle aliases like SHA3 -> KECCAK256)
                canonical_opcode = normalize_opcode(opcode)
                for test_name, uses_code_generator in tests:
                    # All benchmark tests support worst-case-benchmark mode
                    if (
                        test_name
                        not in coverage[canonical_opcode][
                            "worst_case_benchmark"
                        ]
                    ):
                        coverage[canonical_opcode][
                            "worst_case_benchmark"
                        ].append(test_name)

                    # Only tests with code_generator support fixed-opcode-count mode
                    if uses_code_generator:
                        if (
                            test_name
                            not in coverage[canonical_opcode][
                                "fixed_opcode_count"
                            ]
                        ):
                            coverage[canonical_opcode][
                                "fixed_opcode_count"
                            ].append(test_name)

        except Exception as e:
            print(
                f"Warning: Failed to parse {test_file}: {e}", file=sys.stderr
            )
            continue

    return dict(coverage)


def generate_markdown_table(coverage: dict[str, dict[str, list[str]]]) -> str:
    """Generate markdown table from coverage data."""
    lines = [
        "# Benchmark Test Coverage by Opcode",
        "",
        "| Opcode | Name | worst-case-benchmark | fixed-opcode-count |",
        "|--------|------|---------------------|-------------------|",
    ]

    # Include all known opcodes, not just those with tests
    # Exclude aliases (they're consolidated into canonical names)
    all_opcodes = (set(OPCODE_VALUES.keys()) | set(coverage.keys())) - set(
        OPCODE_ALIASES.keys()
    )
    sorted_opcodes = sorted(all_opcodes, key=opcode_sort_key)

    for opcode in sorted_opcodes:
        data = coverage.get(
            opcode, {"worst_case_benchmark": [], "fixed_opcode_count": []}
        )
        worst_case = ", ".join(sorted(data["worst_case_benchmark"])) or "-"
        fixed_opcode = ", ".join(sorted(data["fixed_opcode_count"])) or "-"
        # Get hex value, default to "?" for unknown opcodes
        hex_value = (
            f"0x{OPCODE_VALUES[opcode]:02X}"
            if opcode in OPCODE_VALUES
            else "?"
        )
        lines.append(
            f"| {hex_value} | {opcode} | {worst_case} | {fixed_opcode} |"
        )

    return "\n".join(lines) + "\n"


def generate_summary(coverage: dict[str, dict[str, list[str]]]) -> str:
    """Generate summary statistics."""
    # Exclude aliases from all_opcodes
    all_opcodes = (set(OPCODE_VALUES.keys()) | set(coverage.keys())) - set(
        OPCODE_ALIASES.keys()
    )
    total_known_opcodes = len(all_opcodes)
    opcodes_with_tests = len(coverage)
    opcodes_with_worst_case = sum(
        1 for data in coverage.values() if data["worst_case_benchmark"]
    )
    opcodes_with_fixed = sum(
        1 for data in coverage.values() if data["fixed_opcode_count"]
    )

    lines = [
        "",
        "## Summary",
        "",
        f"- Total known opcodes: {total_known_opcodes}",
        f"- Opcodes with benchmark tests: {opcodes_with_tests}",
        f"- Opcodes with worst-case-benchmark coverage: {opcodes_with_worst_case}",
        f"- Opcodes with fixed-opcode-count coverage: {opcodes_with_fixed}",
    ]

    # Opcodes with no coverage at all
    no_coverage = [
        opcode
        for opcode in all_opcodes
        if opcode not in coverage
        or not coverage[opcode]["worst_case_benchmark"]
    ]
    no_coverage.sort(key=opcode_sort_key)

    lines.extend(
        [
            "",
            "### Opcodes with no benchmark coverage:",
            "",
        ]
    )

    if no_coverage:
        for opcode in no_coverage:
            lines.append(f"- {opcode}")
    else:
        lines.append("- None (all covered)")

    # Opcodes missing fixed-opcode-count coverage
    missing_fixed = [
        opcode
        for opcode, data in coverage.items()
        if data["worst_case_benchmark"] and not data["fixed_opcode_count"]
    ]
    missing_fixed.sort(key=opcode_sort_key)

    lines.extend(
        [
            "",
            "### Opcodes missing fixed-opcode-count coverage:",
            "",
        ]
    )

    if missing_fixed:
        for opcode in missing_fixed:
            lines.append(f"- {opcode}")
    else:
        lines.append("- None (all covered)")

    return "\n".join(lines) + "\n"


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze benchmark test coverage for opcodes"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON instead of markdown",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        help="Output file path (default: stdout)",
    )
    args = parser.parse_args()

    try:
        benchmark_dir = get_benchmark_dir()
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    print(f"Scanning benchmark tests in {benchmark_dir}...", file=sys.stderr)
    coverage = scan_benchmark_tests(benchmark_dir)
    print(
        f"Found {len(coverage)} opcodes with benchmark tests", file=sys.stderr
    )

    if args.json:
        output = json.dumps(coverage, indent=2, sort_keys=True) + "\n"
    else:
        output = generate_markdown_table(coverage) + generate_summary(coverage)

    if args.output:
        Path(args.output).write_text(output)
        print(f"Output written to {args.output}", file=sys.stderr)
    else:
        print(output)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
