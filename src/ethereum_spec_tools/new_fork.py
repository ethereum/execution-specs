"""
Tool to create a new fork using the latest fork
"""

import argparse
import fnmatch
import os
import re
from shutil import copytree
from typing import Tuple

DESCRIPTION = """
Creates the base code for a new fork by using the \
existing code from a given fork.


The ethereum-spec-new-fork command takes 4 arguments, 2 of which are optional
    from_fork: The fork name from which the code is to be duplicated \
Eg - "Tangerine Whistle"
    to_fork: The fork name of the new fork Eg - "Spurious Dragon"
    from_test(Optional): Name of the from fork within the test fixtures \
in case it is different from fork name Eg - "EIP150"
    to_test(Optional): Name of the to fork within the test fixtures \
in case it is different from fork name Eg - "EIP158"


If one wants to create the spurious dragon fork from the tangerine whistle one
    ethereum-spec-new-fork --from_fork="Tangerine Whistle" \
--to_fork="Spurious Dragon" \
--from_test=EIP150 \
--to_test=EIP158

The following will have to however, be updated manually
    1. The fork number and MAINNET_FORK_BLOCK in __init__.py
    2. Any absolute package imports from other forks eg. in trie.py
    3. Package Names under setup.cfg
    4. Add the new fork to the monkey_patch() function in \
src/ethereum_optimized/__init__.py
    5. Adjust the underline in fork/__init__.py
"""

parser = argparse.ArgumentParser(
    description=DESCRIPTION,
    formatter_class=argparse.RawDescriptionHelpFormatter,
)

parser.add_argument("--from_fork", dest="from_fork", type=str, required=True)
parser.add_argument("--to_fork", dest="to_fork", type=str, required=True)
parser.add_argument("--from_test", dest="from_test", type=str)
parser.add_argument("--to_test", dest="to_test", type=str)


def find_replace(dir: str, find: str, replace: str, file_pattern: str) -> None:
    """
    Replace the occurrance of a certain text in files with a new text
    """
    for path, _, files in os.walk(dir):
        for filename in fnmatch.filter(files, file_pattern):
            file_path = os.path.join(path, filename)
            with open(file_path, "r+b") as f:
                s = f.read()
                find_pattern = (r"\b" + re.escape(find) + r"\b").encode()
                s = re.sub(find_pattern, replace.encode(), s)
                f.seek(0)
                f.write(s)
                f.truncate()


class ForkCreator:
    """
    Object to create base code for a new fork from the previous fork.
    """

    def __init__(
        self,
        from_fork: str,
        to_fork: str,
        from_test_names: str,
        to_test_names: str,
    ):
        self.package_folder = "src/ethereum"
        self.test_folder = "tests"

        # Get the fork specific data for from fork
        (
            self.from_fork,
            self.from_package,
            self.from_path,
            self.from_test_path,
        ) = self.get_fork_paths(from_fork)

        # Get the fork specific data for to fork
        (
            self.to_fork,
            self.to_package,
            self.to_path,
            self.to_test_path,
        ) = self.get_fork_paths(to_fork)

        self.from_test_names = from_test_names
        self.to_test_names = to_test_names

    def get_fork_paths(self, fork: str) -> Tuple[str, ...]:
        """
        Get the relevant paths for all folders in a particular fork.
        """
        name = fork
        package = name.replace(" ", "_").lower()
        path = os.path.join(self.package_folder, package)
        test_path = os.path.join(self.test_folder, package)
        return (name, package, path, test_path)

    def duplicate_fork(self) -> None:
        """
        Copy the relevant files/folders from the old fork
        """
        copytree(self.from_path, self.to_path)
        copytree(self.from_test_path, self.to_test_path)

    def update_new_fork_contents(self) -> None:
        """
        Replace references to the old fork with the new ones
        The following however, will have to be updated manually
            1. The fork number and MAINNET_FORK_BLOCK in __init__.py
            2. Any absolute package imports from other forks eg. in trie.py
            3. Package Names under setup.cfg
        """
        # Update Source Code
        find_replace(self.to_path, self.from_fork, self.to_fork, "*.py")
        find_replace(self.to_path, self.from_package, self.to_package, "*.py")
        find_replace(
            self.to_path, self.from_fork.lower(), self.to_fork.lower(), "*.py"
        )

        # Update test files starting with the names used in the test fixtures
        find_replace(
            self.to_test_path, self.from_test_names, self.to_test_names, "*.py"
        )
        find_replace(self.to_test_path, self.from_fork, self.to_fork, "*.py")
        find_replace(
            self.to_test_path, self.from_package, self.to_package, "*.py"
        )
        find_replace(
            self.to_test_path,
            self.from_fork.lower(),
            self.to_fork.lower(),
            "*.py",
        )


def main() -> None:
    """
    Create the new fork
    """
    options = parser.parse_args()
    from_fork = options.from_fork
    to_fork = options.to_fork

    from_test = from_fork if options.from_test is None else options.from_test
    to_test = to_fork if options.to_test is None else options.to_test

    fork_creator = ForkCreator(from_fork, to_fork, from_test, to_test)
    fork_creator.duplicate_fork()
    fork_creator.update_new_fork_contents()

    final_help_text = """
Fork `{fork}` has been successfully created.

PLEASE REMEMBER TO UPDATE THE FOLLOWING MANUALLY:
    1. The fork number and MAINNET_FORK_BLOCK in __init__.py. \
If you are proposing a new EIP, please set MAINNET_FORK_BLOCK to None.
    2. Any absolute package imports from other forks. Eg. in trie.py
    3. Package Names under setup.cfg
    4. Add the new fork to the monkey_patch() function in \
src/ethereum_optimized/__init__.py
    5. Adjust the underline in src/{package}/__init__.py
""".format(
        fork=fork_creator.to_fork,
        package=fork_creator.to_package,
    )
    print(final_help_text)


if __name__ == "__main__":
    main()
