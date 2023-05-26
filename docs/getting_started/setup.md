# Detailed Setup

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
   
3. [`solc`](https://github.com/ethereum/solidity) == `v0.8.17`; `solc` must be in accessible in the `PATH`.

## Installation

To generate tests from the test "fillers", it's necessary to install the Python packages provided by `execution-spec-tests` (it's recommended to use a virtual environment for the installation):

```console
git clone https://github.com/ethereum/execution-spec-tests
cd execution-spec-tests
python3.10 -m venv ./venv/
source ./venv/bin/activate
pip install -e .[lint,docs]
```

## Verify Installation

After the installation, run this sanity check to ensure that tests can be correctly executed:
```console
pytest -v -k access_list
head fixtures/example/yul_example/yul.json
```
If everything is OK, you will see the beginning of the JSON format filled test.

## Troubleshooting

TODO