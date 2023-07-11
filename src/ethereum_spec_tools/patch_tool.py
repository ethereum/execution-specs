"""
Simple patching tool
"""

import argparse
import subprocess
from sys import stderr, stdout

DESCRIPTION = """
Apply the unstaged changes in SOURCE_FORK to each TARGET_FORK. If some of the
change didn't apply, '.rej' files listing the unapplied changes will be left in
TARGET_FORK.
"""

parser = argparse.ArgumentParser(description=DESCRIPTION)

parser.add_argument("source_fork", metavar="SOURCE_FORK", type=str, nargs=1)
parser.add_argument("targets", metavar="TARGET_FORK", type=str, nargs="*")
parser.add_argument(
    "--tests",
    action="store_const",
    const="tests/",
    dest="prefix",
    help="Patch the tests instead",
)

options = parser.parse_args()

source_fork_path = options.prefix + options.source_fork[0]

if options.prefix == "tests/" and "dao_fork" in options.targets:
    raise Exception("dao_fork has no tests")

git_diff = subprocess.run(
    ["git", "diff", source_fork_path], capture_output=True, text=True
)

output_lines = git_diff.stdout.splitlines(keepends=True)

for target in options.targets:
    patch = ""
    for line in output_lines:
        if line.startswith("diff --git"):
            pass
        elif line.startswith("index"):
            pass
        elif line.startswith("--- a/"):
            patch += line.replace(
                "--- a/" + options.prefix + options.source_fork[0],
                "--- " + options.prefix + target,
            )
        elif line.startswith("+++ b/"):
            patch += line.replace(
                "+++ b/" + options.prefix + options.source_fork[0],
                "+++ " + options.prefix + target,
            )
        else:
            patch += line

    subprocess.run(
        [
            "patch",
            "-p0",
            "--no-backup-if-mismatch",
        ],
        input=patch,
        text=True,
        stdout=stdout,
        stderr=stderr,
    )
