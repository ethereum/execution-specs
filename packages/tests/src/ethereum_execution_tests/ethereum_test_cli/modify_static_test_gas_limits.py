"""
Command to scan and overwrite the static tests' gas limits to new optimized
value given in the input file.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Set

import click
import yaml

from ethereum_test_base_types import (
    EthereumTestRootModel,
    HexNumber,
    ZeroPaddedHexNumber,
)
from ethereum_test_specs import StateStaticTest
from pytest_plugins.filler.static_filler import NoIntResolver


class GasLimitDict(EthereumTestRootModel):
    """Formatted JSON file with new gas limits in each test."""

    root: Dict[str, int | None]

    def unique_files(self) -> Set[Path]:
        """Return a list of unique test files."""
        files = set()
        for test in self.root:
            filename, _ = test.split("::")
            files.add(Path(filename))
        return files

    def get_tests_by_file_path(self, file: Path | str) -> Set[str]:
        """Return a list of all tests that belong to a given file path."""
        tests = set()
        for test in self.root:
            current_file, _ = test.split("::")
            if current_file == str(file):
                tests.add(test)
        return tests


class StaticTestFile(EthereumTestRootModel):
    """A static test file."""

    root: Dict[str, StateStaticTest]


def _check_fixtures(
    *,
    input_path: Path,
    max_gas_limit: int | None,
    dry_run: bool,
    verbose: bool,
) -> None:
    """
    Perform checks on fixtures in the specified directory.
    """
    # Load the test dictionary from the input JSON file
    test_dict = GasLimitDict.model_validate_json(input_path.read_text())

    # Iterate through each unique test file that needs modification
    for test_file in test_dict.unique_files():
        tests = test_dict.get_tests_by_file_path(test_file)
        test_file_contents = test_file.read_text()

        # Parse the test file based on its format (YAML or JSON)
        if test_file.suffix == ".yml" or test_file.suffix == ".yaml":
            loaded_yaml = yaml.load(
                test_file.read_text(), Loader=NoIntResolver
            )
            try:
                parsed_test_file = StaticTestFile.model_validate(loaded_yaml)
            except Exception as e:
                raise Exception(
                    f"Unable to parse file {test_file}: {json.dumps(loaded_yaml, indent=2)}"
                ) from e
        else:
            parsed_test_file = StaticTestFile.model_validate_json(
                test_file_contents
            )

        # Validate that the file contains exactly one test
        assert len(parsed_test_file.root) == 1, (
            f"File {test_file} contains more than one test."
        )
        _, parsed_test = parsed_test_file.root.popitem()

        # Skip files with multiple gas limit values
        if len(parsed_test.transaction.gas_limit) != 1:
            if dry_run or verbose:
                print(
                    f"Test file {test_file} contains more than one test (after parsing), skipping."
                )
            continue

        # Get the current gas limit and check if modification is needed
        current_gas_limit = int(parsed_test.transaction.gas_limit[0])
        if max_gas_limit is not None and current_gas_limit <= max_gas_limit:
            # Nothing to do, finished
            for test in tests:
                test_dict.root.pop(test)
            continue

        # Collect valid gas values for this test file
        gas_values: List[int] = []
        for gas_value in [test_dict.root[test] for test in tests]:
            if gas_value is None:
                if dry_run or verbose:
                    print(
                        f"Test file {test_file} contains at least one test that cannot "
                        "be updated, skipping."
                    )
                continue
            else:
                gas_values.append(gas_value)

        # Calculate the new gas limit (rounded up to nearest 100,000)
        new_gas_limit = max(gas_values)
        modified_new_gas_limit = ((new_gas_limit // 100000) + 1) * 100000
        if verbose:
            print(
                f"Changing exact new gas limit ({new_gas_limit}) to "
                f"rounded ({modified_new_gas_limit})"
            )
        new_gas_limit = modified_new_gas_limit

        # Check if the new gas limit exceeds the maximum allowed
        if max_gas_limit is not None and new_gas_limit > max_gas_limit:
            if dry_run or verbose:
                print(
                    f"New gas limit ({new_gas_limit}) exceeds max ({max_gas_limit})"
                )
            continue

        if dry_run or verbose:
            print(
                f"Test file {test_file} requires modification ({new_gas_limit})"
            )

        # Find the appropriate pattern to replace the current gas limit
        potential_types = [int, HexNumber, ZeroPaddedHexNumber]
        substitute_pattern = None
        substitute_string = None

        attempted_patterns = []

        for current_type in potential_types:
            potential_substitute_pattern = (
                rf"\b{current_type(current_gas_limit)}\b"
            )
            potential_substitute_string = f"{current_type(new_gas_limit)}"
            if (
                re.search(
                    potential_substitute_pattern,
                    test_file_contents,
                    flags=re.RegexFlag.MULTILINE,
                )
                is not None
            ):
                substitute_pattern = potential_substitute_pattern
                substitute_string = potential_substitute_string
                break

            attempted_patterns.append(potential_substitute_pattern)

        # Validate that a replacement pattern was found
        assert substitute_pattern is not None, (
            f"Current gas limit ({attempted_patterns}) not found in {test_file}"
        )
        assert substitute_string is not None

        # Perform the replacement in the test file content
        new_test_file_contents = re.sub(
            substitute_pattern, substitute_string, test_file_contents
        )

        assert test_file_contents != new_test_file_contents, (
            "Could not modify test file"
        )

        # Skip writing changes if this is a dry run
        if dry_run:
            continue

        # Write the modified content back to the test file
        test_file.write_text(new_test_file_contents)
        for test in tests:
            test_dict.root.pop(test)

    if dry_run:
        return

    # Write changes to the input file
    input_path.write_text(test_dict.model_dump_json(indent=2))


MAX_GAS_LIMIT = 16_777_216


@click.command()
@click.option(
    "--input",
    "-i",
    "input_str",
    type=click.Path(
        exists=True, file_okay=True, dir_okay=False, readable=True
    ),
    required=True,
    help="The input json file or directory containing json listing the new gas limits for the "
    "static test files files.",
)
@click.option(
    "--max-gas-limit",
    default=MAX_GAS_LIMIT,
    expose_value=True,
    help="Gas limit that triggers a test modification, and also the maximum value that a test "
    "should have after modification.",
)
@click.option(
    "--dry-run",
    "-d",
    "dry_run",
    is_flag=True,
    default=False,
    expose_value=True,
    help="Don't modify any files, simply print operations to be performed.",
)
@click.option(
    "--verbose",
    "-v",
    "verbose",
    is_flag=True,
    default=False,
    expose_value=True,
    help="Print extra information.",
)
def main(
    input_str: str, max_gas_limit: int | None, dry_run: bool, verbose: bool
) -> None:
    """
    Perform checks on fixtures in the specified directory.
    """
    input_path = Path(input_str)
    if not dry_run:
        # Always dry-run first before actually modifying
        _check_fixtures(
            input_path=input_path,
            max_gas_limit=max_gas_limit,
            dry_run=True,
            verbose=False,
        )
    _check_fixtures(
        input_path=input_path,
        max_gas_limit=max_gas_limit,
        dry_run=dry_run,
        verbose=verbose,
    )
