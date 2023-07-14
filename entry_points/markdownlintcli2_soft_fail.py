"""
Lint the markdown in ./README.md and ./docs/ using the external command
markdownlint-cli2.

This script's purpose is:

1. Run the external command markdownlint-cli2 as a subprocess if it's
    installed, if not fail silently. The aim is to avoid disruption to
    external contributors who may not even be working on the docs.
2. Keep tox cross-platform by not insisting on any external commands
    (including bash).
"""

import shutil
import subprocess
import sys


def main():
    """
    Run markdownlint-cli2 as a subprocess if it's installed, if not fail silently.
    """
    markdownlint = shutil.which("markdownlint-cli2")
    if not markdownlint:
        # Note: There's an additional step in test.yaml to run markdownlint-cli2 in github actions
        print("*********  Install 'markdownlint-cli2' to enable markdown linting *********")
        sys.exit(0)

    command = ["node", str(markdownlint), "./docs/**/*.md", "./README.md"]
    sys.exit(subprocess.run(command).returncode)


if __name__ == "__main__":
    main()
