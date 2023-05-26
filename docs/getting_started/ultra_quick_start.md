# Ultra Quick Start

The following requires a Python 3.10 installation.

1. Ensure go-ethereum's [`evm` tool is in your path](setup.md#prerequisites).
2. Ensure [solc 0.8.17 is in your path](setup.md#prerequisites).
3. Clone repo, [install execution-spec-test packages and dependencies](setup.md#installation):
   ```console
   git clone https://github.com/ethereum/execution-spec-tests
   cd execution-spec-tests
   python3 -m venv ./venv/
   source ./venv/bin/activate
   pip install -e .[lint,docs]
   ```
4. [Verify installation](setup.md#verify-installation):
    1. Explore test cases:
       ```console
       pytest --collect-only
       ```
    2. Execute test cases (verbosely) that contain the strings "access_list" and "Berlin":
       ```console
       pytest -v -k "access_list and Berlin"
       ```
5. Implement tests cases in an appropriate `fillers/` sub-directory and Python module...
6. _Optional:_ To execute tests for an upcoming fork, enable it via `--latest-fork FORK`:
   ```console
   pytest -v -k 4844 --latest-fork=Cancun
   ```
7. [Run checks](./verifying_changes.md) (lint, spell-check, type-check, tests, docs):
   ```console
   tox -e fillers
   ```
   If `tox` congratulates you, Github actions CI/CD should pass upon pushing to remote.

## Next Steps 

Become a [command-line test power-user](./executing_tests_command_line.md).

Optionally, learn how to configure VS Code for test execution and debugging:

- [Configure VS Code](./setup_vs_code.md) to auto-format and lint your Python code.
- Learn how to [execute tests in VS Code's debugger](./executing_tests_vs_code.md).

Take a deep dive in to test writing:

- Tutorial: [Writing a State Test](../tutorials/state_transition.md).
- Tutorial: [Writing a Blockchain Test](../tutorials/blockchain.md).