"""Script to display statistics about pre-allocation groups."""

import hashlib
import json
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

import click
from rich.console import Console
from rich.table import Table


def extract_test_module(test_id: str) -> str:
    """Extract test module path from test ID."""
    # Example:
    # tests/cancun/eip4788_beacon_root/test_beacon_root_contract.py::
    #     test_beacon_root_contract_calls[fork_Cancun]
    if "::" in test_id:
        return test_id.split("::")[0]
    return "unknown"


def extract_test_function(test_id: str) -> str:
    """Extract test function name from test ID (without parameters)."""
    # Example:
    # tests/cancun/eip4788_beacon_root/test_beacon_root_contract.py::
    #     test_beacon_root_contract_calls[fork_Cancun]
    #  Returns:
    # tests/cancun/eip4788_beacon_root/test_beacon_root_contract.py::
    #     test_beacon_root_contract_calls
    if "::" in test_id:
        parts = test_id.split("::")
        if len(parts) >= 2:
            function_part = parts[1]
            # Remove parameter brackets if present
            if "[" in function_part:
                function_part = function_part.split("[")[0]
            return f"{parts[0]}::{function_part}"
    return test_id


def _stable_json_hash(value: Any) -> str:
    """Return a stable short hash for a JSON-compatible value."""
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:16]


def _limited(items: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
    """Return up to ``limit`` items, or all items if limit is zero."""
    if limit <= 0:
        return items
    return items[:limit]


def _parse_chain_id(value: Any) -> int:
    """Parse a chain ID serialized as an int or a hex string."""
    if isinstance(value, str):
        return int(value, 16)
    return int(value)


def _environment_hash(data: Dict[str, Any]) -> str:
    """
    Return a stable hash of a group's genesis-relevant execution context.

    Older pre-alloc group files store the grouping ``environment`` directly;
    newer files store only the derived ``genesis`` header. For the latter,
    the pre-state dependent fields (``stateRoot`` and the block ``hash``)
    are removed before hashing so that groups which could share a genesis
    after merging hash identically.
    """
    if "environment" in data:
        return _stable_json_hash(data["environment"])
    genesis = dict(data.get("genesis", {}))
    genesis.pop("stateRoot", None)
    genesis.pop("hash", None)
    return _stable_json_hash(genesis)


@dataclass(frozen=True)
class GroupRecord:
    """Lightweight representation of one pre-allocation group file."""

    hash: str
    path: str
    tests: int
    accounts: int
    fork: str
    chain_id: int
    group_salt: str | None
    environment_hash: str
    test_ids: List[str]

    @property
    def candidate_bucket_key(self) -> str:
        """Return the coarse key used to find potentially packable groups."""
        salt = self.group_salt or ""
        return f"{self.fork}|{self.chain_id}|{salt}|{self.environment_hash}"

    @property
    def modules(self) -> List[str]:
        """Return test modules used by this group."""
        return sorted(
            {extract_test_module(test_id) for test_id in self.test_ids}
        )

    @property
    def functions(self) -> List[str]:
        """Return test functions used by this group."""
        return sorted(
            {extract_test_function(test_id) for test_id in self.test_ids}
        )

    def as_dict(self, *, include_test_ids: bool) -> Dict[str, Any]:
        """Return a JSON-friendly group record."""
        result: Dict[str, Any] = {
            "hash": self.hash,
            "short_hash": self.hash[:10],
            "path": self.path,
            "tests": self.tests,
            "accounts": self.accounts,
            "fork": self.fork,
            "chain_id": self.chain_id,
            "group_salt": self.group_salt,
            "environment_hash": self.environment_hash,
            "candidate_bucket_key": self.candidate_bucket_key,
            "modules": self.modules,
            "functions": self.functions,
        }
        if include_test_ids:
            result["test_ids"] = self.test_ids
        return result


def _read_group_record(file: Path) -> GroupRecord:
    """Read one pre-allocation group file without validating full fixtures."""
    data = json.loads(file.read_text())
    test_ids = data.get("testIds", [])
    pre = data.get("pre", {})
    fork = data.get("network", "unknown")
    if not isinstance(fork, str):
        fork = str(fork)

    return GroupRecord(
        hash=file.stem,
        path=str(file),
        tests=len(test_ids) if test_ids else data.get("testCount", 0),
        accounts=len(pre) if pre else data.get("preAccountCount", 0),
        fork=fork,
        chain_id=_parse_chain_id(data.get("chainId", 1)),
        group_salt=data.get("groupSalt"),
        environment_hash=_environment_hash(data),
        test_ids=test_ids,
    )


def _filter_group_records(
    records: List[GroupRecord],
    *,
    match_test_id_substrings: Tuple[str, ...],
    match_test_id_regexes: Tuple[str, ...],
    exclude_test_id_substrings: Tuple[str, ...],
    exclude_test_id_regexes: Tuple[str, ...],
) -> Tuple[List[GroupRecord], Dict[str, Any]]:
    """Match and remove test IDs from records, dropping empty groups."""
    match_regexes = [re.compile(pattern) for pattern in match_test_id_regexes]
    exclude_regexes = [
        re.compile(pattern) for pattern in exclude_test_id_regexes
    ]
    has_match_filters = bool(match_test_id_substrings or match_regexes)

    def matches(test_id: str) -> bool:
        if not has_match_filters:
            return True
        return any(
            substring in test_id for substring in match_test_id_substrings
        ) or any(regex.search(test_id) is not None for regex in match_regexes)

    def excluded(test_id: str) -> bool:
        return any(
            substring in test_id for substring in exclude_test_id_substrings
        ) or any(
            regex.search(test_id) is not None for regex in exclude_regexes
        )

    filtered_records = []
    matched_test_ids = []
    excluded_test_ids = []
    unmatched_test_ids = []
    dropped_group_hashes = []
    groups_with_matches = 0
    groups_with_excludes = 0

    for record in records:
        kept_test_ids = []
        record_matched = []
        record_excluded = []
        record_unmatched = []
        for test_id in record.test_ids:
            if not matches(test_id):
                record_unmatched.append(test_id)
            elif excluded(test_id):
                record_excluded.append(test_id)
            else:
                record_matched.append(test_id)
                kept_test_ids.append(test_id)

        if record_matched:
            groups_with_matches += 1
            matched_test_ids.extend(record_matched)
        if record_excluded:
            groups_with_excludes += 1
            excluded_test_ids.extend(record_excluded)
        unmatched_test_ids.extend(record_unmatched)

        if (
            not record_excluded
            and not record_unmatched
            and len(kept_test_ids) == len(record.test_ids)
        ):
            filtered_records.append(record)
            continue

        if not kept_test_ids:
            dropped_group_hashes.append(record.hash)
            continue

        filtered_records.append(
            GroupRecord(
                hash=record.hash,
                path=record.path,
                tests=len(kept_test_ids),
                accounts=record.accounts,
                fork=record.fork,
                chain_id=record.chain_id,
                group_salt=record.group_salt,
                environment_hash=record.environment_hash,
                test_ids=kept_test_ids,
            )
        )

    return filtered_records, {
        "match_test_id_substrings": list(match_test_id_substrings),
        "match_test_id_regexes": list(match_test_id_regexes),
        "exclude_test_id_substrings": list(exclude_test_id_substrings),
        "exclude_test_id_regexes": list(exclude_test_id_regexes),
        "matched_tests": len(matched_test_ids),
        "unmatched_tests": len(unmatched_test_ids),
        "excluded_tests": len(excluded_test_ids),
        "groups_with_matches": groups_with_matches,
        "groups_with_exclusions": groups_with_excludes,
        "dropped_groups": len(dropped_group_hashes),
        "dropped_group_hashes": dropped_group_hashes,
        "matched_test_ids": matched_test_ids,
        "excluded_test_ids": excluded_test_ids,
    }


def calculate_size_distribution(
    test_counts: List[int],
) -> Tuple[List[Tuple[str, int]], List[Tuple[str, int, int, int]]]:
    """
    Calculate frequency distribution of group sizes with appropriate binning.

    Returns:
      Group count distribution: [(range_label, group_count), ...]
      Test count distribution:  [(range_label, test_count,
                                  cumulative_remaining,
                                  group_count), ...]

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
            test_distribution.append((label, tests_in_bin, 0, group_count))

    # Calculate cumulative values for the table sorted from largest to
    # smallest:
    #   Row N shows: if we exclude groups of size N and smaller, what
    #                percent of tests remain?
    #   Row N shows: if we include groups of size N and
    #                larger, how many groups is that?

    cumulative_remaining_tests = 0
    cumulative_groups = 0

    # Process from bottom to top
    for i in range(len(test_distribution) - 1, -1, -1):
        label, tests_in_bin, _, group_count = test_distribution[i]
        test_distribution[i] = (
            label,
            tests_in_bin,
            cumulative_remaining_tests,
            cumulative_groups,
        )
        cumulative_remaining_tests += tests_in_bin
        cumulative_groups += group_count

    return group_distribution, test_distribution


def _summary_by_key(
    groups: List[GroupRecord],
    *,
    key_name: str,
    key_getter: Any,
    include_test_ids: bool,
) -> List[Dict[str, Any]]:
    """Build a ranked summary for modules or test functions."""
    grouped: Dict[str, List[GroupRecord]] = defaultdict(list)
    for group in groups:
        for key in key_getter(group):
            grouped[key].append(group)

    summaries = []
    for key, key_groups in grouped.items():
        test_ids = sorted(
            {test_id for group in key_groups for test_id in group.test_ids}
        )
        summary: Dict[str, Any] = {
            key_name: key,
            "groups": len(key_groups),
            "tests": sum(group.tests for group in key_groups),
            "singleton_groups": sum(
                1 for group in key_groups if group.tests == 1
            ),
            "forks": sorted({group.fork for group in key_groups}),
            "environment_count": len(
                {group.environment_hash for group in key_groups}
            ),
            "group_hashes": sorted(group.hash for group in key_groups),
        }
        if include_test_ids:
            summary["test_ids"] = test_ids
        summaries.append(summary)

    return sorted(
        summaries,
        key=lambda item: (
            -item["singleton_groups"],
            -item["groups"],
            -item["tests"],
            item[key_name],
        ),
    )


def _candidate_bucket_summaries(
    groups: List[GroupRecord],
    *,
    low_test_count: int,
    include_test_ids: bool,
) -> List[Dict[str, Any]]:
    """Return ranked buckets where low-count groups share a genesis key."""
    all_buckets: Dict[str, List[GroupRecord]] = defaultdict(list)
    for group in groups:
        all_buckets[group.candidate_bucket_key].append(group)

    candidates = []
    for bucket_key, bucket_groups in all_buckets.items():
        low_groups = [
            group for group in bucket_groups if group.tests <= low_test_count
        ]
        if not low_groups or len(bucket_groups) <= 1:
            continue

        first_group = bucket_groups[0]
        bucket_group_hashes = sorted(group.hash for group in bucket_groups)
        low_group_hashes = sorted(group.hash for group in low_groups)
        summary: Dict[str, Any] = {
            "bucket_key": bucket_key,
            "fork": first_group.fork,
            "chain_id": first_group.chain_id,
            "group_salt": first_group.group_salt,
            "environment_hash": first_group.environment_hash,
            "groups": len(bucket_groups),
            "tests": sum(group.tests for group in bucket_groups),
            "accounts": sum(group.accounts for group in bucket_groups),
            "low_groups": len(low_groups),
            "low_tests": sum(group.tests for group in low_groups),
            "singleton_groups": sum(
                1 for group in low_groups if group.tests == 1
            ),
            "larger_groups": sum(
                1 for group in bucket_groups if group.tests > low_test_count
            ),
            "max_group_tests": max(group.tests for group in bucket_groups),
            "group_hashes": bucket_group_hashes,
            "low_group_hashes": low_group_hashes,
            "modules": sorted(
                {module for group in low_groups for module in group.modules}
            ),
            "functions": sorted(
                {
                    function
                    for group in low_groups
                    for function in group.functions
                }
            ),
        }
        if include_test_ids:
            summary["test_ids"] = sorted(
                {test_id for group in low_groups for test_id in group.test_ids}
            )
        candidates.append(summary)

    return sorted(
        candidates,
        key=lambda item: (
            -item["singleton_groups"],
            -item["low_groups"],
            -item["low_tests"],
            -item["groups"],
            item["bucket_key"],
        ),
    )


def analyze_pre_alloc_folder(
    folder: Path,
    *,
    low_test_count: int = 5,
    limit: int = 50,
    include_test_ids: bool = False,
    include_group_details: bool = True,
    compact: bool = False,
    match_test_id_substrings: Tuple[str, ...] = (),
    match_test_id_regexes: Tuple[str, ...] = (),
    exclude_test_id_substrings: Tuple[str, ...] = (),
    exclude_test_id_regexes: Tuple[str, ...] = (),
) -> Dict[str, Any]:
    """Analyze pre-allocation folder and return statistics."""
    group_files = sorted(folder.glob("*.json"))
    records = [_read_group_record(file) for file in group_files]
    records, filter_stats = _filter_group_records(
        records,
        match_test_id_substrings=match_test_id_substrings,
        match_test_id_regexes=match_test_id_regexes,
        exclude_test_id_substrings=exclude_test_id_substrings,
        exclude_test_id_regexes=exclude_test_id_regexes,
    )

    # Basic stats
    total_groups = len(records)
    total_tests = sum(group.tests for group in records)
    total_accounts = sum(group.accounts for group in records)

    # Group by fork
    fork_stats: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {"groups": 0, "tests": 0, "low_groups": 0}
    )
    for group in records:
        fork_stats[group.fork]["groups"] += 1
        fork_stats[group.fork]["tests"] += group.tests
        if group.tests <= low_test_count:
            fork_stats[group.fork]["low_groups"] += 1

    # Group by test module
    module_stats: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {"groups": set(), "tests": 0, "low_groups": 0}
    )
    for group in records:
        # Count tests per module in this group
        module_test_count: defaultdict[str, int] = defaultdict(int)
        for test_id in group.test_ids:
            module = extract_test_module(test_id)
            module_test_count[module] += 1

        # Add to module stats
        for module, test_count in module_test_count.items():
            module_stats[module]["groups"].add(group.hash)
            module_stats[module]["tests"] += test_count
            if group.tests <= low_test_count:
                module_stats[module]["low_groups"] += 1

    # Convert sets to counts
    for module in module_stats:
        module_stats[module]["groups"] = len(module_stats[module]["groups"])

    # Per-group details
    group_details = (
        [group.as_dict(include_test_ids=include_test_ids) for group in records]
        if include_group_details
        else []
    )

    # Calculate frequency distribution of group sizes
    group_distribution, test_distribution = calculate_size_distribution(
        [group.tests for group in records]
    )

    # Analyze test functions split across multiple size-1 groups
    split_test_functions: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {"groups": 0, "forks": set()}
    )
    for group in records:
        if group.tests == 1:
            test_id = group.test_ids[0] if group.test_ids else group.hash
            test_function = extract_test_function(test_id)
            split_test_functions[test_function]["groups"] += 1
            split_test_functions[test_function]["forks"].add(group.fork)

    split_functions = {}
    for func, split_test_function in split_test_functions.items():
        if split_test_function["groups"] > 1:
            fork_count = len(split_test_function["forks"])
            groups_per_fork = (
                split_test_function["groups"] / fork_count
                if fork_count > 0
                else split_test_function["groups"]
            )
            split_functions[func] = {
                "total_groups": split_test_function["groups"],
                "fork_count": fork_count,
                "groups_per_fork": groups_per_fork,
                "forks": sorted(split_test_function["forks"]),
            }

    low_groups = sorted(
        [
            group.as_dict(include_test_ids=include_test_ids)
            for group in records
            if group.tests <= low_test_count
        ],
        key=lambda item: (
            item["tests"],
            -item["accounts"],
            item["fork"],
            item["hash"],
        ),
    )
    low_group_records = [
        group for group in records if group.tests <= low_test_count
    ]
    candidate_buckets = _candidate_bucket_summaries(
        records,
        low_test_count=low_test_count,
        include_test_ids=include_test_ids,
    )
    test_function_candidates = _summary_by_key(
        low_group_records,
        key_name="test_function",
        key_getter=lambda group: group.functions,
        include_test_ids=include_test_ids,
    )
    module_candidates = _summary_by_key(
        low_group_records,
        key_name="module",
        key_getter=lambda group: group.modules,
        include_test_ids=include_test_ids,
    )

    if compact:
        module_stats_output: Dict[str, Dict[str, Any]] = {}
        split_functions_output: Dict[str, Dict[str, Any]] = {}
        group_details_output: List[Dict[str, Any]] = []
    else:
        module_stats_output = dict(module_stats)
        split_functions_output = split_functions
        group_details_output = group_details

    return {
        "pre_alloc_folder": str(folder),
        "parameters": {
            "low_test_count": low_test_count,
            "limit": limit,
            "include_test_ids": include_test_ids,
            "include_group_details": include_group_details,
            "compact": compact,
            "match_test_id_substrings": list(match_test_id_substrings),
            "match_test_id_regexes": list(match_test_id_regexes),
            "exclude_test_id_substrings": list(exclude_test_id_substrings),
            "exclude_test_id_regexes": list(exclude_test_id_regexes),
        },
        "total_groups": total_groups,
        "total_tests": total_tests,
        "total_accounts": total_accounts,
        "low_group_count": len(low_groups),
        "singleton_group_count": sum(
            1 for group in records if group.tests == 1
        ),
        "fork_stats": dict(fork_stats),
        "module_stats": module_stats_output,
        "group_details": group_details_output,
        "group_distribution": group_distribution,
        "test_distribution": test_distribution,
        "split_functions": split_functions_output,
        "filters": filter_stats,
        "optimization": {
            "low_test_count": low_test_count,
            "low_groups_total": len(low_groups),
            "candidate_buckets_total": len(candidate_buckets),
            "test_function_candidates_total": len(test_function_candidates),
            "module_candidates_total": len(module_candidates),
            "low_groups": _limited(low_groups, limit),
            "candidate_buckets": _limited(candidate_buckets, limit),
            "test_function_candidates": _limited(
                test_function_candidates, limit
            ),
            "module_candidates": _limited(module_candidates, limit),
        },
    }


def display_stats(
    stats: Dict[str, Any],
    console: Console,
    verbose: int = 0,
) -> None:
    """Display statistics in a formatted way."""
    # Overall summary
    console.print("\n[bold cyan]Pre-Allocation Statistics Summary[/bold cyan]")
    console.print(f"Total groups: [green]{stats['total_groups']}[/green]")
    console.print(f"Total tests: [green]{stats['total_tests']}[/green]")
    console.print(f"Total accounts: [green]{stats['total_accounts']}[/green]")
    console.print(
        f"Singleton groups: [yellow]{stats['singleton_group_count']}[/yellow]"
    )
    console.print(
        "Low-count groups "
        f"(<= {stats['parameters']['low_test_count']} tests): "
        f"[yellow]{stats['low_group_count']}[/yellow]"
    )
    filters = stats.get("filters", {})
    if filters.get("match_test_id_substrings") or filters.get(
        "match_test_id_regexes"
    ):
        console.print(
            f"Matched tests: [yellow]{filters['matched_tests']}[/yellow] "
            f"in [yellow]{filters['groups_with_matches']}[/yellow] groups"
        )
    if filters.get("excluded_tests", 0) > 0:
        console.print(
            f"Excluded tests: [yellow]{filters['excluded_tests']}[/yellow] "
            f"from [yellow]{filters['groups_with_exclusions']}[/yellow] "
            "groups"
        )
    # Per-group details table (only with -v or -vv)
    if verbose >= 1 and stats["group_details"]:
        console.print(
            "\n[bold yellow]Tests and Accounts per Group[/bold yellow]"
        )
        group_table = Table(show_header=True, header_style="bold magenta")
        group_table.add_column("Group Hash", style="dim")
        group_table.add_column("Fork", style="cyan")
        group_table.add_column("Tests", justify="right")
        group_table.add_column("Accounts", justify="right")
        group_table.add_column("Environment", style="dim")

        # Sort by test count (descending)
        sorted_groups = sorted(
            stats["group_details"], key=lambda x: -x["tests"]
        )

        # Show all groups if -vv, otherwise top 20
        groups_to_show = sorted_groups if verbose >= 2 else sorted_groups[:20]

        for group in groups_to_show:
            group_table.add_row(
                group["short_hash"],
                group["fork"],
                str(group["tests"]),
                str(group["accounts"]),
                group["environment_hash"],
            )

        if verbose < 2 and len(stats["group_details"]) > 20:
            group_table.add_row(
                "...",
                "...",
                "...",
                "...",
                "...",
            )

        console.print(group_table)
    elif verbose >= 1 and stats["total_groups"] > 0:
        console.print(
            "\n[dim]Per-group details omitted "
            "(use --include-group-details to show them).[/dim]"
        )

    # Fork statistics table
    console.print("\n[bold yellow]Groups and Tests per Fork[/bold yellow]")
    fork_table = Table(show_header=True, header_style="bold magenta")
    fork_table.add_column("Fork", style="cyan")
    fork_table.add_column("Groups", justify="right")
    fork_table.add_column("Tests", justify="right")
    fork_table.add_column("Low Groups", justify="right")
    fork_table.add_column("Avg Tests/Group", justify="right")

    # Sort forks by name
    sorted_forks = sorted(stats["fork_stats"].items())

    for fork, fork_data in sorted_forks:
        avg_tests = (
            fork_data["tests"] / fork_data["groups"]
            if fork_data["groups"] > 0
            else 0
        )
        fork_table.add_row(
            fork,
            str(fork_data["groups"]),
            str(fork_data["tests"]),
            str(fork_data["low_groups"]),
            f"{avg_tests:.1f}",
        )

    console.print(fork_table)

    # Group size frequency distribution table
    console.print("\n[bold yellow]Group Size Distribution[/bold yellow]")
    dist_table = Table(show_header=True, header_style="bold magenta")
    dist_table.add_column("Test Count Range", style="cyan")
    dist_table.add_column("Number of Groups", justify="right")
    dist_table.add_column("Percentage", justify="right")

    total_groups_in_dist = sum(
        count for _, count in stats.get("group_distribution", [])
    )

    for size_range, count in stats.get("group_distribution", []):
        percentage = (
            (count / total_groups_in_dist * 100)
            if total_groups_in_dist > 0
            else 0
        )
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
    test_dist_map = {
        item[0]: item for item in stats.get("test_distribution", [])
    }

    # Display in the defined order
    test_dist_sorted = [
        test_dist_map[bin_range]
        for bin_range in bin_order
        if bin_range in test_dist_map
    ]

    # Need to recalculate cumulative groups from top for display
    cumulative_groups_display = 0
    for _i, (
        size_range,
        tests_in_range,
        cumulative_remaining_tests,
        _,
    ) in enumerate(test_dist_sorted):
        coverage_percentage = (
            (cumulative_remaining_tests / total_tests * 100)
            if total_tests > 0
            else 0
        )

        # Find how many groups in this bin
        groups_in_bin = next(
            (
                count
                for label, count in stats.get("group_distribution", [])
                if label == size_range
            ),
            0,
        )
        cumulative_groups_display += groups_in_bin

        cumul_pct = cumulative_groups_display / total_groups * 100
        cumulative_str = (
            f"{cumulative_groups_display} ({cumul_pct:.1f}%)"
            if total_groups > 0
            else "0"
        )
        coverage_table.add_row(
            size_range,
            str(tests_in_range),
            f"{coverage_percentage:.1f}%",
            cumulative_str,
        )

    console.print(coverage_table)

    # Candidate buckets table
    optimization = stats.get("optimization", {})
    candidate_buckets = optimization.get("candidate_buckets", [])
    if candidate_buckets:
        console.print(
            "\n[bold yellow]Low-Count Groups Sharing a Genesis "
            "Key[/bold yellow]"
        )
        console.print(
            "[dim]Buckets rank low-count groups that already share fork, "
            "chain id, group salt, and environment. These are useful starting "
            "points for checking whether reserved-address or pre-allocation "
            "constraints can be relaxed.[/dim]",
            highlight=False,
        )
        bucket_table = Table(show_header=True, header_style="bold magenta")
        bucket_table.add_column("Fork", style="cyan")
        bucket_table.add_column("Env", style="dim")
        bucket_table.add_column("Groups", justify="right")
        bucket_table.add_column("Low", justify="right")
        bucket_table.add_column("Singleton", justify="right")
        bucket_table.add_column("Tests", justify="right")
        bucket_table.add_column("Top Module", style="dim")

        for bucket in candidate_buckets:
            bucket_table.add_row(
                bucket["fork"],
                bucket["environment_hash"],
                str(bucket["groups"]),
                str(bucket["low_groups"]),
                str(bucket["singleton_groups"]),
                str(bucket["tests"]),
                bucket["modules"][0] if bucket["modules"] else "",
            )

        console.print(bucket_table)
        if optimization.get("candidate_buckets_total", 0) > len(
            candidate_buckets
        ):
            console.print(
                f"[dim]Showing {len(candidate_buckets)} of "
                f"{optimization['candidate_buckets_total']} candidate "
                "buckets; "
                "use --limit 0 to include all in JSON output.[/dim]"
            )

    # Module statistics table (only with -v or -vv; empty with --compact)
    if verbose >= 1 and stats["module_stats"]:
        console.print(
            "\n[bold yellow]Groups and Tests per Test Module[/bold yellow]"
        )
        module_table = Table(show_header=True, header_style="bold magenta")
        module_table.add_column("Test Module", style="dim")
        module_table.add_column("Groups", justify="right")
        module_table.add_column("Tests", justify="right")
        module_table.add_column("Low Groups", justify="right")
        module_table.add_column("Avg Tests/Group", justify="right")

        # Sort modules by group count (descending) - shows execution complexity
        sorted_modules = sorted(
            stats["module_stats"].items(),
            # Secondary sort by tests
            key=lambda x: (-x[1]["groups"], -x[1]["tests"]),
        )

        # Show all modules if -vv, otherwise top 15
        modules_to_show = (
            sorted_modules if verbose >= 2 else sorted_modules[:15]
        )

        for module, module_data in modules_to_show:
            # Shorten module path for display
            if module.startswith("tests/"):
                module_display = module[6:]  # Remove "tests/" prefix
            else:
                module_display = module

            avg_tests = (
                module_data["tests"] / module_data["groups"]
                if module_data["groups"] > 0
                else 0
            )
            module_table.add_row(
                module_display,
                str(module_data["groups"]),
                str(module_data["tests"]),
                str(module_data["low_groups"]),
                f"{avg_tests:.1f}",
            )

        if verbose < 2 and len(stats["module_stats"]) > 15:
            module_table.add_row(
                "...",
                "...",
                "...",
                "...",
                "...",
            )

        console.print(module_table)

    # Split test functions analysis (only show if there are any)
    if stats.get("split_functions"):
        console.print(
            "\n[bold yellow]Test Functions Split Across Multiple "
            "Singleton Groups[/bold yellow]"
        )
        console.print(
            "[dim]These test functions create multiple size-1 groups, often "
            "due to different forks or parameters.[/dim]",
            highlight=False,
        )

        split_table = Table(show_header=True, header_style="bold magenta")
        split_table.add_column("Test Function", style="dim")
        split_table.add_column("Total Groups", justify="right")
        split_table.add_column("Fork Count", justify="right")
        split_table.add_column("Groups/Fork", justify="right", style="yellow")

        # Sort by groups per fork (descending) to show worst offenders first
        sorted_split = sorted(
            stats["split_functions"].items(),
            key=lambda x: x[1]["groups_per_fork"],
            reverse=True,
        )

        for test_function, data in sorted_split:
            # Shorten function path for display
            display_function = test_function
            if display_function.startswith("tests/"):
                display_function = display_function[6:]  # Remove "tests/"

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
            f"\n[yellow]Optimization Potential:[/yellow] Excluding these "
            f"{total_split_functions} split functions would remove "
            f"{total_split_groups} singleton groups from the pool"
        )

    # Verbosity hint
    console.print()
    if verbose == 0:
        console.print(
            "[dim]Hint: Use -v to see detailed group and module statistics, "
            "--output json for programmatic analysis, or --limit 0 for all "
            "candidate rows[/dim]"
        )
    elif verbose == 1:
        console.print(
            "[dim]Hint: Use -vv to see all groups and modules (currently "
            "showing top entries only)[/dim]"
        )


@click.command(
    epilog=(
        "Agent/programmatic example: groupstats PRE_ALLOC_FOLDER --output "
        "json --compact --exclude-group-details --low-test-count 1 "
        "--limit 20\n\n"
        'For JSON output, inspect the "optimization" object first. '
        '"candidate_buckets" ranks low-count groups sharing fork, chain ID, '
        "group salt, and environment. Then use "
        '"test_function_candidates", "module_candidates", and "low_groups" '
        "to identify specific tests or modules to optimize. Add "
        "--include-test-ids when exact pytest node IDs are needed. Use "
        "--match-test-id or --match-test-id-regex to focus the analysis on "
        "one side of a comparison. Use --exclude-test-id or "
        "--exclude-test-id-regex to remove known-noisy tests before "
        "recomputing stats. Use --limit 0 only when the caller can handle "
        "large JSON payloads."
    )
)
@click.argument(
    "pre_alloc_folder",
    type=click.Path(exists=True, path_type=Path),
    default="fixtures/blockchain_tests_engine_x/pre_alloc",
)
@click.option(
    "--verbose",
    "-v",
    count=True,
    help="Show verbose output (-v for top groups/modules, -vv for all groups)",
)
@click.option(
    "--output",
    "output_mode",
    type=click.Choice(["rich", "json"]),
    default="rich",
    show_default=True,
    help="Output format.",
)
@click.option(
    "--low-test-count",
    type=click.IntRange(min=1),
    default=5,
    show_default=True,
    help="Treat groups with this many tests or fewer as optimization targets.",
)
@click.option(
    "--limit",
    type=click.IntRange(min=0),
    default=50,
    show_default=True,
    help="Limit optimization result lists; use 0 for all rows.",
)
@click.option(
    "--include-test-ids/--exclude-test-ids",
    default=False,
    show_default=True,
    help="Include full test IDs in group and optimization records.",
)
@click.option(
    "--include-group-details/--exclude-group-details",
    default=True,
    show_default=True,
    help="Include the per-group detail list in JSON and verbose rich output.",
)
@click.option(
    "--compact",
    is_flag=True,
    help=(
        "Omit verbose top-level maps from JSON output; keeps summaries and "
        "bounded optimization lists."
    ),
)
@click.option(
    "--match-test-id",
    "match_test_id_substrings",
    multiple=True,
    help=(
        "Keep only test IDs containing this substring before computing stats. "
        "Can be used multiple times."
    ),
)
@click.option(
    "--match-test-id-regex",
    "match_test_id_regexes",
    multiple=True,
    help=(
        "Keep only test IDs matching this regular expression before "
        "computing stats. Can be used multiple times."
    ),
)
@click.option(
    "--exclude-test-id",
    "exclude_test_id_substrings",
    multiple=True,
    help=(
        "Exclude test IDs containing this substring before computing stats. "
        "Can be used multiple times."
    ),
)
@click.option(
    "--exclude-test-id-regex",
    "exclude_test_id_regexes",
    multiple=True,
    help=(
        "Exclude test IDs matching this regular expression before computing "
        "stats. Can be used multiple times."
    ),
)
def main(
    pre_alloc_folder: Path,
    verbose: int,
    output_mode: str,
    low_test_count: int,
    limit: int,
    include_test_ids: bool,
    include_group_details: bool,
    compact: bool,
    match_test_id_substrings: Tuple[str, ...],
    match_test_id_regexes: Tuple[str, ...],
    exclude_test_id_substrings: Tuple[str, ...],
    exclude_test_id_regexes: Tuple[str, ...],
) -> None:
    """
    Display statistics about pre-allocation groups.

    This script analyzes a pre_alloc folder generated by the test framework's
    pre-allocation group optimization feature.

    The pre_alloc file is generated when running tests with the
    --generate-pre-alloc-groups and --use-pre-alloc-groups flags to optimize
    test execution by grouping tests with identical pre-allocation state.
    """
    console = Console()

    try:
        stats = analyze_pre_alloc_folder(
            pre_alloc_folder,
            low_test_count=low_test_count,
            limit=limit,
            include_test_ids=include_test_ids,
            include_group_details=include_group_details,
            compact=compact,
            match_test_id_substrings=match_test_id_substrings,
            match_test_id_regexes=match_test_id_regexes,
            exclude_test_id_substrings=exclude_test_id_substrings,
            exclude_test_id_regexes=exclude_test_id_regexes,
        )
        if output_mode == "json":
            click.echo(json.dumps(stats, sort_keys=True, indent=2))
        else:
            display_stats(stats, console, verbose=verbose)
    except FileNotFoundError:
        message = f"Error: Folder not found: {pre_alloc_folder}"
        if output_mode == "json":
            click.echo(message, err=True)
        else:
            console.print(f"[red]{message}[/red]")
        raise click.Abort() from None
    except Exception as e:
        message = f"Error: {e}"
        if output_mode == "json":
            click.echo(message, err=True)
        else:
            console.print(f"[red]{message}[/red]")
        raise click.Abort() from None


if __name__ == "__main__":
    main()
