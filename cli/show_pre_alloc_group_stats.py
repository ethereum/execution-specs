"""Script to display statistics about pre-allocation groups."""

from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple

import click
from pydantic import Field
from rich.console import Console
from rich.table import Table

from ethereum_test_base_types import CamelModel
from ethereum_test_fixtures import PreAllocGroups


def extract_test_module(test_id: str) -> str:
    """Extract test module path from test ID."""
    # Example: tests/cancun/eip4788_beacon_root/test_beacon_root_contract.py::test_beacon_root_contract_calls[fork_Cancun]  # noqa: E501
    if "::" in test_id:
        return test_id.split("::")[0]
    return "unknown"


def extract_test_function(test_id: str) -> str:
    """Extract test function name from test ID (without parameters)."""
    # Example: tests/cancun/eip4788_beacon_root/test_beacon_root_contract.py::test_beacon_root_contract_calls[fork_Cancun]  # noqa: E501
    # Returns: tests/cancun/eip4788_beacon_root/test_beacon_root_contract.py::test_beacon_root_contract_calls  # noqa: E501
    if "::" in test_id:
        parts = test_id.split("::")
        if len(parts) >= 2:
            function_part = parts[1]
            # Remove parameter brackets if present
            if "[" in function_part:
                function_part = function_part.split("[")[0]
            return f"{parts[0]}::{function_part}"
    return test_id


def calculate_size_distribution(
    test_counts: List[int],
) -> Tuple[List[Tuple[str, int]], List[Tuple[str, int, int, int]]]:
    """
    Calculate frequency distribution of group sizes with appropriate binning.

    Returns:
        - Group count distribution: [(range_label, group_count), ...]
        - Test count distribution: [(range_label, test_count, cumulative_remaining, group_count),
            ...]

    """
    if not test_counts:
        return [], []

    # Define bins based on the data characteristics
    # Using logarithmic-style bins for better distribution visibility
    bins = [
        (1, 1, "1"),
        (2, 5, "2-5"),
        (6, 10, "6-10"),
        (11, 20, "11-20"),
        (21, 50, "21-50"),
        (51, 100, "51-100"),
        (101, 200, "101-200"),
        (201, 500, "201-500"),
        (501, 1000, "501-1000"),
        (1001, float("inf"), "1000+"),
    ]

    # Calculate both distributions
    group_distribution = []
    test_distribution = []

    for min_val, max_val, label in bins:
        # Group count distribution
        groups_in_bin = [tc for tc in test_counts if min_val <= tc <= max_val]
        group_count = len(groups_in_bin)

        if group_count > 0:
            group_distribution.append((label, group_count))

            # Test count distribution with group count
            tests_in_bin = sum(groups_in_bin)
            test_distribution.append((label, tests_in_bin, 0, group_count))  # Added group_count

    # Calculate cumulative values
    # For the table sorted from largest to smallest:
    # - Row N shows: if we exclude groups of size N and smaller, what % of tests remain?
    # - Row N shows: if we include groups of size N and larger, how many groups is that?

    cumulative_remaining_tests = 0
    cumulative_groups = 0

    # Process from bottom to top
    for i in range(len(test_distribution) - 1, -1, -1):
        label, tests_in_bin, _, group_count = test_distribution[i]
        test_distribution[i] = (label, tests_in_bin, cumulative_remaining_tests, cumulative_groups)
        cumulative_remaining_tests += tests_in_bin
        cumulative_groups += group_count

    return group_distribution, test_distribution


def analyze_pre_alloc_folder(folder: Path, verbose: int = 0) -> Dict:
    """Analyze pre-allocation folder and return statistics."""
    pre_alloc_groups = PreAllocGroups.from_folder(folder, lazy_load=False)

    # Basic stats
    total_groups = len(pre_alloc_groups)
    total_tests = sum(group.test_count for group in pre_alloc_groups.values())
    total_accounts = sum(group.pre_account_count for group in pre_alloc_groups.values())

    # Group by fork
    fork_stats: Dict[str, Dict] = defaultdict(lambda: {"groups": 0, "tests": 0})
    for group in pre_alloc_groups.values():
        fork_stats[group.fork.name()]["groups"] += 1
        fork_stats[group.fork.name()]["tests"] += group.test_count

    # Group by test module
    module_stats: Dict[str, Dict] = defaultdict(lambda: {"groups": set(), "tests": 0})
    for hash_key, group in pre_alloc_groups.items():
        # Count tests per module in this group
        module_test_count: defaultdict = defaultdict(int)
        for test_id in group.test_ids:
            module = extract_test_module(test_id)
            module_test_count[module] += 1

        # Add to module stats
        for module, test_count in module_test_count.items():
            module_stats[module]["groups"].add(hash_key)
            module_stats[module]["tests"] += test_count

    # Convert sets to counts
    for module in module_stats:
        module_stats[module]["groups"] = len(module_stats[module]["groups"])

    # Per-group details
    group_details = []
    for hash_key, group in pre_alloc_groups.items():
        group_details.append(
            {
                "hash": hash_key[:8] + "...",  # Shortened hash for display
                "tests": group.test_count,
                "accounts": group.pre_account_count,
                "fork": group.fork.name(),
            }
        )

    # Calculate frequency distribution of group sizes
    group_distribution, test_distribution = calculate_size_distribution(
        [g["tests"] for g in group_details]  # type: ignore
    )

    # Analyze test functions split across multiple size-1 groups
    class SplitTestFunction(CamelModel):
        groups: int = 0
        forks: Set[str] = Field(default_factory=set)

    split_test_functions: Dict[str, SplitTestFunction] = defaultdict(lambda: SplitTestFunction())

    # Process all size-1 groups directly from pre_state
    for _hash_key, group_data in pre_alloc_groups.items():
        if group_data.test_count == 1:  # Size-1 group
            test_id = group_data.test_ids[0]
            test_function = extract_test_function(test_id)
            fork = group_data.fork.name()

            split_test_functions[test_function].groups += 1
            split_test_functions[test_function].forks.add(fork)

    # Filter to only test functions with multiple size-1 groups and calculate ratios
    split_functions = {}
    for func, split_test_function in split_test_functions.items():
        if split_test_function.groups > 1:
            fork_count = len(split_test_function.forks)
            groups_per_fork = (
                split_test_function.groups / fork_count
                if fork_count > 0
                else split_test_function.groups
            )
            split_functions[func] = {
                "total_groups": split_test_function.groups,
                "fork_count": fork_count,
                "groups_per_fork": groups_per_fork,
            }

    return {
        "total_groups": total_groups,
        "total_tests": total_tests,
        "total_accounts": total_accounts,
        "fork_stats": dict(fork_stats),
        "module_stats": dict(module_stats),
        "group_details": group_details,
        "group_distribution": group_distribution,
        "test_distribution": test_distribution,
        "split_functions": split_functions,
    }


def display_stats(stats: Dict, console: Console, verbose: int = 0):
    """Display statistics in a formatted way."""
    # Overall summary
    console.print("\n[bold cyan]Pre-Allocation Statistics Summary[/bold cyan]")
    console.print(f"Total groups: [green]{stats['total_groups']}[/green]")
    console.print(f"Total tests: [green]{stats['total_tests']}[/green]")
    console.print(f"Total accounts: [green]{stats['total_accounts']}[/green]")
    if stats.get("skipped_count", 0) > 0:
        console.print(
            f"Skipped groups: [yellow]{stats['skipped_count']}[/yellow] "
            "(use --verbose to see details)"
        )

    # Per-group details table (only with -v or -vv)
    if verbose >= 1:
        console.print("\n[bold yellow]Tests and Accounts per Group[/bold yellow]")
        group_table = Table(show_header=True, header_style="bold magenta")
        group_table.add_column("Group Hash", style="dim")
        group_table.add_column("Fork", style="cyan")
        group_table.add_column("Tests", justify="right")
        group_table.add_column("Accounts", justify="right")

        # Sort by test count (descending)
        sorted_groups = sorted(stats["group_details"], key=lambda x: -x["tests"])

        # Show all groups if -vv, otherwise top 20
        groups_to_show = sorted_groups if verbose >= 2 else sorted_groups[:20]

        for group in groups_to_show:
            group_table.add_row(
                group["hash"],
                group["fork"],
                str(group["tests"]),
                str(group["accounts"]),
            )

        if verbose < 2 and len(stats["group_details"]) > 20:
            group_table.add_row(
                "...",
                "...",
                "...",
                "...",
            )

        console.print(group_table)

    # Fork statistics table
    console.print("\n[bold yellow]Groups and Tests per Fork[/bold yellow]")
    fork_table = Table(show_header=True, header_style="bold magenta")
    fork_table.add_column("Fork", style="cyan")
    fork_table.add_column("Groups", justify="right")
    fork_table.add_column("Tests", justify="right")
    fork_table.add_column("Avg Tests/Group", justify="right")

    # Sort forks by name
    sorted_forks = sorted(stats["fork_stats"].items())

    for fork, fork_data in sorted_forks:
        avg_tests = fork_data["tests"] / fork_data["groups"] if fork_data["groups"] > 0 else 0
        fork_table.add_row(
            fork,
            str(fork_data["groups"]),
            str(fork_data["tests"]),
            f"{avg_tests:.1f}",
        )

    console.print(fork_table)

    # Group size frequency distribution table
    console.print("\n[bold yellow]Group Size Distribution[/bold yellow]")
    dist_table = Table(show_header=True, header_style="bold magenta")
    dist_table.add_column("Test Count Range", style="cyan")
    dist_table.add_column("Number of Groups", justify="right")
    dist_table.add_column("Percentage", justify="right")

    total_groups_in_dist = sum(count for _, count in stats.get("group_distribution", []))

    for size_range, count in stats.get("group_distribution", []):
        percentage = (count / total_groups_in_dist * 100) if total_groups_in_dist > 0 else 0
        dist_table.add_row(
            size_range,
            str(count),
            f"{percentage:.1f}%",
        )

    console.print(dist_table)

    # Test coverage distribution table
    console.print("\n[bold yellow]Test Coverage by Group Size[/bold yellow]")
    coverage_table = Table(show_header=True, header_style="bold magenta")
    coverage_table.add_column("Test Count Range", style="cyan")
    coverage_table.add_column("Tests in Range", justify="right")
    coverage_table.add_column("Coverage if Excluded (%)", justify="right")
    coverage_table.add_column("Cumulative Groups", justify="right")

    total_tests = stats.get("total_tests", 0)
    total_groups = stats.get("total_groups", 0)

    # Define bin order from largest to smallest for proper sorting
    bin_order = [
        "1000+",
        "501-1000",
        "201-500",
        "101-200",
        "51-100",
        "21-50",
        "11-20",
        "6-10",
        "2-5",
        "1",
    ]

    # Create a mapping for easy lookup
    test_dist_map = {item[0]: item for item in stats.get("test_distribution", [])}

    # Display in the defined order
    test_dist_sorted = [
        test_dist_map[bin_range] for bin_range in bin_order if bin_range in test_dist_map
    ]

    # Need to recalculate cumulative groups from top for display
    cumulative_groups_display = 0
    for _i, (size_range, tests_in_range, cumulative_remaining_tests, _) in enumerate(
        test_dist_sorted
    ):
        coverage_percentage = (
            (cumulative_remaining_tests / total_tests * 100) if total_tests > 0 else 0
        )

        # Find how many groups in this bin
        groups_in_bin = next(
            (count for label, count in stats.get("group_distribution", []) if label == size_range),
            0,
        )
        cumulative_groups_display += groups_in_bin

        coverage_table.add_row(
            size_range,
            str(tests_in_range),
            f"{coverage_percentage:.1f}%",
            f"{cumulative_groups_display} ({cumulative_groups_display / total_groups * 100:.1f}%)"
            if total_groups > 0
            else "0",
        )

    console.print(coverage_table)

    # Module statistics table (only with -v or -vv)
    if verbose >= 1:
        console.print("\n[bold yellow]Groups and Tests per Test Module[/bold yellow]")
        module_table = Table(show_header=True, header_style="bold magenta")
        module_table.add_column("Test Module", style="dim")
        module_table.add_column("Groups", justify="right")
        module_table.add_column("Tests", justify="right")
        module_table.add_column("Avg Tests/Group", justify="right")

        # Sort modules by group count (descending) - shows execution complexity
        sorted_modules = sorted(
            stats["module_stats"].items(),
            key=lambda x: (-x[1]["groups"], -x[1]["tests"]),  # Secondary sort by tests
        )

        # Show all modules if -vv, otherwise top 15
        modules_to_show = sorted_modules if verbose >= 2 else sorted_modules[:15]

        for module, module_data in modules_to_show:
            # Shorten module path for display
            if module.startswith("tests/"):
                module_display = module[6:]  # Remove "tests/" prefix
            else:
                module_display = module

            avg_tests = (
                module_data["tests"] / module_data["groups"] if module_data["groups"] > 0 else 0
            )
            module_table.add_row(
                module_display,
                str(module_data["groups"]),
                str(module_data["tests"]),
                f"{avg_tests:.1f}",
            )

        if verbose < 2 and len(stats["module_stats"]) > 15:
            module_table.add_row(
                "...",
                "...",
                "...",
                "...",
            )

        console.print(module_table)

    # Split test functions analysis (only show if there are any)
    if stats.get("split_functions"):
        console.print("\n[bold yellow]Test Functions Split Across Multiple Groups[/bold yellow]")
        console.print(
            "[dim]These test functions create multiple size-1 groups (due to different "
            "forks/parameters), preventing pre-allocation group optimization:[/dim]",
            highlight=False,
        )

        split_table = Table(show_header=True, header_style="bold magenta")
        split_table.add_column("Test Function", style="dim")
        split_table.add_column("Total Groups", justify="right")
        split_table.add_column("Fork Count", justify="right")
        split_table.add_column("Groups/Fork", justify="right", style="yellow")

        # Sort by groups per fork (descending) to show worst offenders first
        sorted_split = sorted(
            stats["split_functions"].items(), key=lambda x: x[1]["groups_per_fork"], reverse=True
        )

        for test_function, data in sorted_split:
            # Shorten function path for display
            display_function = test_function
            if display_function.startswith("tests/"):
                display_function = display_function[6:]  # Remove "tests/" prefix

            split_table.add_row(
                display_function,
                str(data["total_groups"]),
                str(data["fork_count"]),
                f"{data['groups_per_fork']:.1f}",
            )

        console.print(split_table)

        # Summary of optimization potential
        total_split_groups = sum(
            data["total_groups"] for data in stats["split_functions"].values()
        )
        total_split_functions = len(stats["split_functions"])

        console.print(
            f"\n[yellow]Optimization Potential:[/yellow] Excluding these {total_split_functions} "
            f"split functions would save {total_split_groups} groups"
        )

    # Verbosity hint
    console.print()
    if verbose == 0:
        console.print(
            "[dim]Hint: Use -v to see detailed group and module statistics, or -vv to see all "
            "groups and modules[/dim]"
        )
    elif verbose == 1:
        console.print(
            "[dim]Hint: Use -vv to see all groups and modules (currently showing top entries "
            "only)[/dim]"
        )


@click.command()
@click.argument(
    "pre_alloc_folder",
    type=click.Path(exists=True, path_type=Path),
    default="fixtures/blockchain_tests_engine_x/pre_alloc",
)
@click.option(
    "--verbose",
    "-v",
    count=True,
    help="Show verbose output (-v for warnings, -vv for all groups)",
)
def main(pre_alloc_folder: Path, verbose: int):
    """
    Display statistics about pre-allocation groups.

    This script analyzes a pre_alloc folder generated by the test framework's
    pre-allocation group optimization feature and displays:

    - Total number of groups, tests, and accounts
    - Number of tests and accounts per group (tabulated)
    - Number of groups and tests per fork (tabulated)
    - Number of groups and tests per test module (tabulated)

    The pre_alloc file is generated when running tests with the
    --generate-pre-alloc-groups and --use-pre-alloc-groups flags to optimize
    test execution by grouping tests with identical pre-allocation state.

    """
    console = Console()

    try:
        stats = analyze_pre_alloc_folder(pre_alloc_folder, verbose=verbose)
        display_stats(stats, console, verbose=verbose)
    except FileNotFoundError:
        console.print(f"[red]Error: Folder not found: {pre_alloc_folder}[/red]")
        raise click.Abort() from None
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise click.Abort() from None


if __name__ == "__main__":
    main()
