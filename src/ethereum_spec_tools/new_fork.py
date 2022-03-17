"""
Tool to create a new fork using the latest fork
"""

import argparse
import fnmatch
import os

DESCRIPTION = """
Creates the base code for a new fork by using the \
existing code from a given fork.


The command takes 4 arguments, 2 of which are optional
    from_fork: The fork name from which the code is to be duplicated \
Eg - "Tangerine Whistle"
    to_fork: The fork name of the new fork Eg - "Spurious Dragon"
    from_test(Optional): Name of the from fork within the test fixtures \
in case it is different from fork name Eg - "EIP150"
    to_test(Optional): Name of the to fork within the test fixtures \
in case it is different from fork name Eg - "EIP158"


If one wants to create the spurious dragon fork fron the tangerine whistle one
    python src/ethereum_spec_tools/new_fork.py \
--from_fork="Tangerine Whistle" \
--to_fork="Spurious Dragon" \
--from_test=EIP150 \
--to_test=EIP158

The following will have to however, be updated manually
    1. The fork number and MAINNET_FORK_BLOCK in __init__.py
    2. Any absolute package imports from other forks eg. in trie.py
    3. Package Names under setup.cfg
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
            with open(file_path) as f:
                s = f.read()
            s = s.replace(find, replace)
            with open(file_path, "w") as f:
                f.write(s)


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
        self.script_file = os.path.abspath(__file__)
        # Assumes that the root folder is 3 folders up
        self.root_folder = os.path.dirname(
            os.path.dirname(os.path.dirname(self.script_file))
        )
        self.package_folder = os.path.join(self.root_folder, "src/ethereum")
        self.optimized_package_folder = os.path.join(
            self.root_folder, "src/ethereum_optimized"
        )
        self.test_folder = os.path.join(self.root_folder, "tests")

        # Get the fork specific data for from fork
        self.from_fork = from_fork
        self.from_package = self.from_fork.replace(" ", "_").lower()
        self.from_path = os.path.join(self.package_folder, self.from_package)
        self.from_optimized_path = os.path.join(
            self.optimized_package_folder, self.from_package
        )
        self.from_test_path = os.path.join(self.test_folder, self.from_package)

        # Get the fork specific data for to fork
        self.to_fork = to_fork
        self.to_package = self.to_fork.replace(" ", "_").lower()
        self.to_path = os.path.join(self.package_folder, self.to_package)
        self.to_optimized_path = os.path.join(
            self.optimized_package_folder, self.to_package
        )
        self.to_test_path = os.path.join(self.test_folder, self.to_package)

        self.from_test_names = from_test_names
        self.to_test_names = to_test_names

    def duplicate_fork(self) -> None:
        """
        Copy the relevant files/folders from the old fork
        """
        os.system(f"cp -R {self.from_path} {self.to_path}")
        os.system(f"cp -R {self.from_optimized_path} {self.to_optimized_path}")
        os.system(f"cp -R {self.from_test_path} {self.to_test_path}")

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

        # Update optimized source code
        find_replace(
            self.to_optimized_path, self.from_fork, self.to_fork, "*.py"
        )
        find_replace(
            self.to_optimized_path, self.from_package, self.to_package, "*.py"
        )
        find_replace(
            self.to_optimized_path,
            self.from_fork.lower(),
            self.to_fork.lower(),
            "*.py",
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


if __name__ == "__main__":
    options = parser.parse_args()
    from_fork = options.from_fork
    to_fork = options.to_fork

    from_test = from_fork if options.from_test is None else options.from_test
    to_test = to_fork if options.to_test is None else options.to_test

    fork_creator = ForkCreator(from_fork, to_fork, from_test, to_test)
    fork_creator.duplicate_fork()
    fork_creator.update_new_fork_contents()
