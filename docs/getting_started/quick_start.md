# Quick Start

## Prerequisites

The following are required to either generate or develop tests:

1. Python >= `3.10.0` < `3.11`.
   - For dists. with the `apt` package manager ensure you have python `-dev` & `-venv` packages installed.
2. [`go-ethereum`](https://github.com/ethereum/go-ethereum) `geth`'s `evm` utility must be accessible in the `PATH`, typically at the latest version. To get it:
     1. Install [the Go programming language](https://go.dev/doc/install) on your computer.
     2. Clone [the Geth repository](https://github.com/ethereum/go-ethereum).
     3. Run `make all`.
     4. Copy `build/bin/evm` to a directory on the path.
   
    **Note:** To update to a different Geth branch (for example one that supports a specific EIP) all you need to do is to change the `evm` in the path.
   
3. [`solc`](https://github.com/ethereum/solidity) >= `v0.8.17`; `solc` must be in accessible in the `PATH`.

## Installation

To generate tests from the test "fillers", it's necessary to install the Python packages provided by `execution-spec-tests` (it's recommended to use a virtual environment for the installation):

```console
git clone https://github.com/ethereum/execution-spec-tests
cd execution-spec-tests
python3.10 -m venv ./venv/
source ./venv/bin/activate
pip install -e .
```

After the installation, run this sanity check to ensure tests are generated.
If everything is OK, you will see the beginning of the JSON format filled test.

```console
tf --test-case yul
head fixtures/example/yul_example/yul.json
```

## Generating the Execution Spec Tests For Use With Clients

To generate all the tests defined in the `./fillers` sub-directory, run the `tf` command:

```console
tf --filler-path="fillers" --output="fixtures" 
```

This is equivalent to running `tf` with no arguments. The paths`fillers/` and `fixtures/` are both defaults for the respective command.

!!! note
    The test `post` conditions are tested against the output of the `geth` `evm` utility during test generation.

To generate all the tests in the `./fillers/vm` sub-directory (category), for example, run:
```console
tf --test-categories vm
```

This extends to sub-directories. To generate all specific tests within the `./fillers/vm/vm_arith/vm_add` sub-directory, run:
```console
tf --output="fixtures" --test-categories vm.vm_arith.vm_add
```

To generate all the tests in the `./fillers/*/dup.py` modules, for example, run:
```console
tf --test-module dup
```

To generate specific tests, such as `./fillers/*/*.py::test_dup`, for example, run (remove the `test_` prefix from the test case's function name):
```console
tf --test-case dup
```

To overwrite the existing set of fixtures, make sure you run the test filler with the `--force-refill` flag:
```console
tf --force-refill
```

For upcoming forks that are not already upgraded within the Ethereum network, use the `--latest-fork` flag. For example, currently (03/05/23) the next fork being developed is `Cancun`:
```console
tf --latest-fork Cancun
```


## Testing the Execution Spec Tests Framework

The Python packages provided by the execution spec tests framework have their own test suite that can be ran via `tox`:

```console
python -m venv ./venv/
source ./venv/bin/activate
pip install tox
tox -e py3
```
