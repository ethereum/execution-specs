"""
Spellcheck the markdown in ./README.md and ./docs/ using the pyspelling
package.

Pyspelling requires aspell as an external dependency. This script's purpose
is to:

1. Run pyspelling if aspell is installed, if not fail silently. The aim is to
    avoid disruption to external contributors who may not even be working on
    the docs.
2. Keep tox cross-platform by not insisting on any external commands (including
    bash).
"""

import os
import shutil
import sys

from pyspelling import __main__ as pyspelling_main  # type: ignore


def main():
    """
    Run pyspelling if aspell is installed, if not fail silently.
    """
    if not shutil.which("aspell"):
        print("aspell not installed, skipping spellcheck.")
        if os.environ.get("GITHUB_ACTIONS"):
            sys.exit(1)
        else:
            print("*********  Install 'aspell' and 'aspell-en' to enable spellcheck *********")
            sys.exit(0)

    sys.exit(pyspelling_main.main())


if __name__ == "__main__":
    main()
