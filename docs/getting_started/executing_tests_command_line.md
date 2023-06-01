# Executing Tests at a Prompt

## Collection - Test Exploration

The test fillers implemented in the `./fillers` sub-directory can be listed in the console using:
```console
pytest --collect-only
```
and can be filtered (by test path, function and parameter substring):
```console
pytest --collect-only -k warm_coinbase
```
Docstrings are additionally displayed when ran verbosely:
```console
pytest --collect-only -k warm_coinbase -vv
```

## Execution


To generate all the test fixtures defined in the `./fillers` sub-directory and write them to the `./fixtures` directory, run `pytest` in the top-level directory as:
```console
pytest --output="fixtures"
```

!!! note "Test case verification"
    Note, that the test `post` conditions are tested against the output of the `evm t8n` command for transition tests, respectively `evm b11r` command for blockchain tests, during test generation.

To generate all the test fixtures in the `./fillers/eips/` sub-directory (category), for example, run:
```console
pytest fillers/eips
```

To generate all the test fixtures in the `./fillers/eips/eip3651.py` module, for example, run:
```console
pytest ./fillers/eips/eip3651.py
```

To generate specific test fixtures, such as those from the test function `test_warm_coinbase_call_out_of_gas()`, for example, run:
```console
pytest -k "test_warm_coinbase_call_out_of_gas"
```
or, additionally, only for the for Shanghai fork:
```console
pytest -k "test_warm_coinbase_call_out_of_gas and shanghai"
```

## Execution for Development Forks 

!!! note ""
    By default, test cases are not executed with upcoming Ethereum forks so that they can be readily executed against the `evm` tool from the latest `geth` release. 
    
    In order to execute test cases for an upcoming fork, ensure that the `evm` tool used supports that fork and features under test and use the `--latest-fork` flag.
    
    For example, as of May 2023, the current fork under active development is `Cancun`:
    ```console
    pytest --latest-fork Cancun
    ```

    See: [Executing Tests for Features under Development](./executing_tests_dev_fork.md).

## Useful pytest Command-Line Options

```console
pytest -vv            # More verbose output
pytest -x             # Exit instantly on first error or failed test filler:
pytest --pdb          # drop into the debugger upon error in a test filler
pytest --traces       # Collect traces of the execution information from the transition tool
pytest --evm=EVM_BIN  # Specify the evm executable to generate fillers with
```