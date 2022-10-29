import os
import re
import shutil
import subprocess
import sys
from typing import Tuple

from ethereum_spec_tools.forks import Hardfork


def get_fork_paths(fork_name: str) -> Tuple:
    """
    Get the location of the fork represented by `fork_name`
    as well as the previous fork
    """

    if fork_name == "frontier":
        sys.exit("No fork before frontier")

    forks = Hardfork.discover()

    for i, fork in enumerate(forks):
        if fork.short_name == fork_name:
            return forks[i - 1].path[0], fork.path[0]  # type: ignore

    return None, None


def find_source_files(path: str) -> set:
    """
    Find .py files in a particular location
    """
    file_list = []
    for directory, _, filenames in os.walk(path):
        for filename in filenames:
            if filename.endswith(".py"):
                file_path = os.path.join(directory, filename)
                file_path = file_path[len(path) + 1 :]
                file_list.append(file_path)

    return set(file_list)


def process_source_code(path: str, name: str) -> None:
    """
    Clean up the source code.
    Removes comments and empty lines.
    """
    if not os.path.isfile(path):
        open(name, "a").close()
        return

    with open(path) as f:
        code = f.read()

    code = re.sub(re.compile('""".*?"""', re.DOTALL), "", code)
    code = re.sub(re.compile("#.*?\n"), "\n", code)
    code = re.sub(re.compile("\n\s*\n"), "\n", code)

    with open(name, "w") as f:
        f.write(code)


class DiffTester:
    """
    Test the diffs in source code and compare it with expected diffs.
    """

    def __init__(
        self,
        fork_name: str,
        expected_diffs_path: str,
        found_diffs_path: str = None,
    ) -> None:
        self.old_fork_path, self.new_fork_path = get_fork_paths(fork_name)
        self.expected_diffs_path = expected_diffs_path

        if found_diffs_path:
            self.found_diffs_path = found_diffs_path
        else:
            self.found_diffs_path = os.path.join(
                os.path.dirname(os.path.realpath(__file__)), "found_diffs"
            )
        os.makedirs(self.found_diffs_path, exist_ok=True)

    def create_diffs(self) -> None:
        """
        Create all the diffs of a fork wrt. the previous fork.
        This will be the found diffs that can be compared with expected in `compare_diffs`
        """
        old_fork_files = find_source_files(self.old_fork_path)
        new_fork_files = find_source_files(self.new_fork_path)

        source_files = old_fork_files | new_fork_files

        for file in source_files:
            old_source_path = os.path.join(self.old_fork_path, file)
            old_processed_path = os.path.join(self.found_diffs_path, "old.py")
            new_source_path = os.path.join(self.new_fork_path, file)
            new_processed_path = os.path.join(self.found_diffs_path, "new.py")

            process_source_code(old_source_path, old_processed_path)
            process_source_code(new_source_path, new_processed_path)

            diffs = subprocess.run(
                ["diff", old_processed_path, new_processed_path],
                capture_output=True,
                text=True,
            )
            if diffs.stdout:
                diff_file = os.path.join(
                    self.found_diffs_path, file.split(".")[0]
                )
                os.makedirs(os.path.dirname(diff_file), exist_ok=True)

                # Ignore anything other than <, > which denote deletion, insertion
                output_diff = re.sub(
                    re.compile("(^|\n)(?![<|>]).*?\n"), "\n\n", diffs.stdout
                )
                with open(diff_file, "w") as f:
                    f.write(output_diff)

            os.remove(old_processed_path)
            os.remove(new_processed_path)

    def compare_diffs(self) -> None:
        """
        Compare found diffs with expected. Clean up the folders after test
        """
        diffs = subprocess.run(
            ["diff", self.expected_diffs_path, self.found_diffs_path],
            capture_output=True,
            text=True,
        )
        shutil.rmtree(self.found_diffs_path)
        assert diffs.stdout == ""


def run_diff_test(
    fork_name: str, expected_diffs_path: str, found_diffs_path: str = None
) -> None:
    """
    Run the diff test for a particular fork.
    """
    diff_tester = DiffTester(fork_name, expected_diffs_path, found_diffs_path)
    diff_tester.create_diffs()
    diff_tester.compare_diffs()
