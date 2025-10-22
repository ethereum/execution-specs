# A Guide to Porting Original Ethereum Tests to EEST

## Background

EEST is the successor to [ethereum/tests](https://github.com/ethereum/tests) (aka "original tests"), a repository that defined EVM test cases from the [Frontier](https://ethereum.org/en/history/#frontier) phase up to and including [The Merge](https://ethereum.org/en/history/#paris). These test cases are specified as YAML (and occasionally JSON) files in the [`./src/`](https://github.com/ethereum/tests/tree/develop/src) sub-directory. JSON test fixtures, which are fully-populated tests that can be executed against clients, are generated using [ethereum/retesteth](https://github.com/ethereum/retesteth). These JSON artifacts are regenerated when needed and added to the repository, typically in the [`tests/static/state_tests`](https://github.com/ethereum/execution-spec-tests/tree/main/tests/static/state_tests) sub-directory.

From [Shanghai](https://ethereum.org/en/history/#shapella) onward, new test cases — especially for new features introduced in hard forks—are defined in Python within EEST. While the existing test cases remain important for client testing, porting ethereum/tests to EEST will help maintain and generate tests for newer forks. This also ensures feature parity, as client teams will only need to obtain test fixture releases from one source.

While automating the conversion of the remaining YAML (or JSON) test cases to Python is possible, manually porting individual test cases offers several benefits:

- Reducing the number of test cases by combining multiple YAML (or JSON) cases into a single Python test function using parametrization.
- Potentially improving coverage by parametrizing the Python version.
- Producing higher quality code and documentation, which are typically clearer than an automated conversion.
- Ensuring better organization of tests within the `./tests` folder of execution-spec-tests by fork and EIP.

## Porting an original test

1. Select one or more test cases from `./tests/static/state_tests/` to port and create an issue in this repository AND comment on [this tracker issue.](https://github.com/ethereum/execution-spec-tests/issues/972)

2. [Add a new test](../writing_tests/index.md) in the appropriate fork folder, following the guidelines for [choosing a test type.](../writing_tests/types_of_tests.md#deciding-on-a-test-type)

3. Submit a PR with the ported tests:

     1. Add the list of ported files using python marker to the head of your python test.

        Example:

        ```python
         @pytest.mark.ported_from(
        [
            "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stCreateTest/CREATE_ContractSuicideDuringInit_ThenStoreThenReturnFiller.json",
            "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stCreateTest/CREATE_ContractSuicideDuringInit_WithValueFiller.json",
        ],
        pr=["https://github.com/ethereum/execution-spec-tests/pull/1871"],
        # coverage_missed_reason="Converting solidity code result in following opcode not being used:",
        ```

        Replace test names with your chosen tests and PR number.

        Uncomment coverage_missed_reason when all the missed coverage lines are approved, usually some opcodes end up not used after translating test logic from lllc, yul.

        But sometimes missed coverage line could hint that you forgot to account important test logic.

        If no coverage is missed, you are good!

     2. Remove the ported files from .tests/static/state_tests in your PR

> See also: 📄 [Getting started with EEST.](../getting_started/repository_overview.md)

## Filling tests

EEST uses pytest to run tests against [EELS (an EVM implementation for testing)](https://github.com/ethereum/execution-specs). This process is known as "filling" and verifies the assertions in your tests. You can use the fill CLI for this. For example, see how to fill the `PUSH` opcode.

```shell
uv run fill tests/frontier/opcodes/test_push.py
```

See also: 📄 [Documentation for the `fill` command.](../filling_tests/filling_tests_command_line.md)

> If the tests can't currently be filled, please explain the issue (feel free to also [open a Discussion](https://github.com/ethereum/execution-spec-tests/discussions/new?category=general)).

## Debugging tests

By default, EVM logs are stored in the `logs` folder at the repository root. You can check the `output` folder to review transaction results. If needed, review a previous PR that ported tests (e.g., [the PR porting the `PUSH` opcode](https://github.com/ethereum/execution-spec-tests/pull/975), and [other port PRs](https://github.com/ethereum/execution-spec-tests/pulls?q=is%3Apr+label%3Aport)).

## Test coverage

It's crucial that ported tests maintain coverage parity with _original tests_. This ensures that no critical functions are left untested and prevents the introduction of bugs. A CI workflow automatically checks for coverage.

If coverage action fails (See: 📄 [An example of a failing test coverage](https://github.com/ethereum/execution-spec-tests/actions/runs/13037332959/job/36370897481)), it's recommended to run the coverage action locally (see: 📄 [How to run GitHub actions locally](../dev/test_actions_locally.md)), which should generate a `evmtest_coverage` directory:

```console
❯ tree evmtest_coverage  -L 2
evmtest_coverage
└── coverage
    ├── BASE
    ├── BASE_TESTS
    ├── coverage_BASE.lcov
    ├── coverage_PATCH.lcov
    ├── DIFF
    ├── difflog.txt
    ├── PATCH
    └── PATCH_TESTS
```

Here `BASE`is _original tests_, `PATCH` is the ported test, and `DIFF` is the coverage difference on EVMONE. Open `evmtest_coverage/coverage/DIFF/index.html` in browser:

![Annotated coverage](../img/annotated-coverage.jpg)

| Label |                                   Description                                   |
| ----- | :-----------------------------------------------------------------------------: |
| `LBC` |    **Lost base coverage:** Code that was tested before, but is untested now.    |
| `UBC` |  **Uncovered baseline code:** Code that was untested before and untested now.   |
| `GBC` | **Gained baseline coverage:** Code that was untested before, but is tested now. |
| `CBC` |    **Covered baseline code:** Code that was tested before and is tested now.    |

Follow the hyperlinks for lost base coverage (`LBC`) to address coverage gaps. Here is an example coverage loss:

![Missing original coverage](../img/original-coverage-loss.png)

> Lost line coverage from a coverage report. In this case, caused by a missing invocation of `CALLDATALOAD`.

!!! note "Expected coverage loss"

    EEST uses [pytest](https://docs.pytest.org/en/stable/), a popular Python testing framework, to help orchestrate testing Ethereum specifications, while _original tests_ relied on large, static contracts and the EVM to handle much of the execution. This difference can lead to coverage gaps. EEST favors dynamic contract creation for each test vector, while _original tests_ preferred a single static contract with multiple test vectors determined by transaction input data.

    It's important to note that coverage helps identify missing test paths. If you believe the coverage loss is due to differences in "setup" code between frameworks and doesn't impact the feature you're testing, explain this in your PR. A team member can help with the review.

    For example, review the [discussion in this PR] to see an example of why and how coverage loss can occur.(https://github.com/ethereum/execution-spec-tests/pull/975#issuecomment-2528792289)

## Resolving Coverage Gaps from Yul Compilation

When porting tests from ethereum/tests, you may encounter coverage gaps that are false positives. This commonly occurs because:

- **Original tests** often used Yul to define smart contracts, and solc compilation introduces additional opcodes that aren't specifically under test
- **EEST ports** use the explicit EEST Opcode mini-language, which is more precise in opcode definition

If coverage analysis shows missing opcodes that were only present due to Yul compilation artifacts (not the actual feature being tested), this can be resolved during PR review by adding the `coverage_missed_reason` parameter:

```python
@pytest.mark.ported_from(
    ["path/to/original_test.json"],
    coverage_missed_reason="Missing opcodes are Yul compilation artifacts, not part of tested feature"
)
```

!!! note "Add coverage_missed_reason only after PR review"
    Only add `coverage_missed_reason` after PR review determines the coverage gap is acceptable, never preemptively. This helps maintain test coverage integrity while accounting for legitimate differences between Yul-based and EEST opcode-based implementations.
