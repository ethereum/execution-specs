# Testing Tools

This repository provides tools and libraries for generating cross-client
Ethereum tests.

## Quick Start

Relies on Python `3.10.0`, `geth` `v1.10.13`, `solc` `v0.8.5` or later. 

```console
$ git clone https://github.com/lightclient/testing-tools
$ cd testing-tools
$ pip install -e .
$ tf --output="fixtures"
```

## Overview 

### `ethereum_test`

The `ethereum_test` package provides primitives and helpers to allow developers
to easily test the consensus logic of Ethereum clients. 

### `ethereum_test_filler`

The `ethereum_test_filler` pacakge is a CLI application that recursively searches
a given directory for Python modules that export test filler functions generated
using `ethereum_test`. It then processes the fillers using the transition tool
and the block builder tool, and writes the resulting fixture to file.

### `evm_block_builder`

This is a wrapper around the [block builder][b11r] (b11r) tool.

### `evm_transition_tool`

This is a wrapper around the [transaction][t8n] (t8n) tool.

### `ethereum_tests`

Contains all the Ethereum consensus tests available in this repository.

## Writing Tests

### Adding a New Test

All currently implemented tests can be found in the `src/ethereum_tests`
directory, which is composed of many subdirectories, and each one represents a
different test category.

Source files included in each category contain one or multiple test functions,
and each can in turn create one or many test vectors.

A new test can be added by either:

- Adding a new `test_` function to an existing file in any of the existing
  category subdirectories within `src/ethereum_tests`.
- Creating a new source file in an existing category, and populating it with
  the new test function(s).
- Creating an entirely new category by adding a subdirectory in
  `src/ethereum_tests` with the appropriate source files and test functions.

### Test Generator Functions

Every test function is a generator which can perform a single or multiple
`yield` operations during its runtime to each time yield a single `StateTest` 
object.

The test vector's generator function _must_ be decorated by only one of the
following decorators:
- test_from
- test_from_until
- test_only

These decorators specify the forks on which the test vector is supposed to run.

They also automatically append necessary information for the
`ethereum_test_filler` to process when the generator is being executed to fill
the tests.

The test vector function must take only one `str` parameter: the fork name.

### `StateTest` Object

The `StateTest` object represents a single test vector, and contains the
following attributes:

- env: Environment object which describes the global state of the blockchain
    before the test starts.
- pre: Pre-State containing the information of all Ethereum accounts that exist
    before any transaction is executed.
- post: Post-State containing the information of all Ethereum accounts that are
    created or modified after all transactions are executed.
- txs: All transactions to be executed during the test vector runtime.


### Pre/Post State of the Test

The `pre` and `post` states are elemental to setup and then verify the outcome
of the state test.

Both `pre` and `post` are mappings of account addresses to `account` structures:
```
class Account:
    nonce: int
    balance: int
    code: Union[bytes, str, Code]
    storage: Storage
```

A single test vector can contain as many accounts in the `pre` and `post` states
as required, and they can be also filled dynamically.

`storage` of an account is a key/value dictionary, and its values are
integers within range of `[0, 2**256 - 1]`.

`txs` are the steps which transform the pre-state into the post-state and
must perform specific actions within the accounts (smart contracts) that result
in verifiable changes to the balance, nonce, and/or storage in each of them.

`post` is compared against the outcome of the client after the execution
of each transaction, and any differences are considered a failure

When designing a test, all the changes must be ideally saved into the contract's
storage to be able to verify them in the post-state.

### Test Transactions

Transactions can be crafted by sending them with specific `data` or to a
specific account, which contains the code to be executed

Transactions can also create more accounts, by setting the `to` field to an 
empty string.

Transactions can be designed to fail, and a verification must be made that the
transaction fails with the specific error that matches what is expected by the
test.

### Writing code for the accounts in the test

Account bytecode can be embedded in the test accounts by adding it to the `code`
field of the `account` object, or the `data` field of the `tx` object if the
bytecode is meant to be treated as init code or call data.

The code can be in either of the following formats:
- `bytes` object, representing the raw opcodes in binary format
- `str`, representing an hexadecimal format of the opcodes
- `Code` compilable object

Currently supported built-in compilable objects are:

- `Yul` object containing [Yul source code][yul]

`Code` objects can be concatenated together by using the `+` operator.

### Verifying correctness of the new test

A well written test performs a single verification output at a time.

A verification output can be a single storage slot, the balance of an account,
or a newly created contract.

A test can be written as a negative verification. E.g. a contract is not
created, or a transaction fails to execute or runs out of gas.

These verifications must be carefully crafted because it is possible to end up
having a false positive result, which means that the test passed but the
intended verification was never made.

To avoid these scenarios, it is important to have a separate verification to
check that test is effective. E.g. when a transaction is supposed to fail, it
is necessary to check that the failure error is actually the one expected by
the test.

[t8n]: https://github.com/ethereum/go-ethereum/tree/master/cmd/evm
[b11r]: https://github.com/ethereum/go-ethereum/pull/23843
[yul]: https://docs.soliditylang.org/en/latest/yul.html
