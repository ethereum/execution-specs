# Writing Tests

## Purpose of test specs in this repository

The goal of the test specs included in this repository is to generate test vectors that can be consumed by any Execution client, and to verify that all of the clients agree on the same output after executing each test.

Consensus is the most important aspect of any blockchain network, therefore, anything that modifies the state of the blockchain must be tested by at least one test in this repository.

The tests focus on the EVM execution, therefore before being able to properly write a test, it is important to understand what the Ethereum Virtual Machine is and how it works.


## Types of tests

At the moment there are only two types of tests that can be produced by each test spec:

- State Tests
- Blockchain Tests

The State tests span a single block and, ideally, a single transaction.

Examples of State tests:

- Test a single opcode behavior
- Verify opcode gas costs
- Test interactions between multiple smart contracts
- Test creation of smart contracts

The Blockchain tests span multiple blocks which may or may not contain transactions and mainly focus on the block to block effects to the Ethereum state.

- Verify system-level operations such as coinbase balance updates or withdrawals
- Verify fork transitions
- Verify blocks with invalid transactions/properties are rejected

## Adding a New Test

All currently implemented tests can be found in the `fillers`
directory, which is composed of many subdirectories, and each one represents a
different test category.

Source files included in each category contain one or multiple test specs
represented as python functions, and each can in turn produce one or many test
vectors.

A new test can be added by either:

- Adding a new `test_` python function to an existing file in any of the
  existing category subdirectories within `fillers`.
- Creating a new source file in an existing category, and populating it with
  the new test function(s).
- Creating an entirely new category by adding a subdirectory in
  `fillers` with the appropriate source files and test functions.
    - Tests within multiple sub-directories must have a `__init__.py` file
      within each directory above it (and it own), to ensure the test is found by the test filler `tf`.

## Test Spec Generator Functions

Every test spec is a python generator function which can perform a single or
multiple `yield` operations during its runtime to each time yield a single
`StateTest`/`BlockchainTest` object.

The test vector's generator function _must_ be decorated by only one of the
following decorators:
- `test_from`
- `test_from_until`
- `test_only`

These decorators specify the forks on which the test vector is supposed to run.

They also automatically append necessary information for the
`ethereum_test_filling_tool` to process when the generator is being executed to
fill the tests.

The test vector function must take only one `str` parameter: the fork name.

## `StateTest` Object

The `StateTest` object represents a single test vector, and contains the
following attributes:

- env: Environment object which describes the global state of the blockchain
    before the test starts.
- pre: Pre-State containing the information of all Ethereum accounts that exist
    before any transaction is executed.
- post: Post-State containing the information of all Ethereum accounts that are
    created or modified after all transactions are executed.
- txs: All transactions to be executed during the test vector runtime.

## `BlockchainTest` Object

The `BlockchainTest` object represents a single test vector that evaluates the
Ethereum VM by attempting to append multiple blocks to the chain:

- pre: Pre-State containing the information of all Ethereum accounts that exist
    before any block is executed.
- post: Post-State containing the information of all Ethereum accounts that are
    created or modified after all blocks are executed.
- blocks: All blocks to be appended to the blockchain during the test.


## Pre/Post State of the Test

The `pre` and `post` states are elemental to setup and then verify the outcome
of the state test.

Both `pre` and `post` are mappings of account addresses to `account` structures (see [more info](#the-account-object)).


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

## Test Transactions

Transactions can be crafted by sending them with specific `data` or to a
specific account, which contains the code to be executed

Transactions can also create more accounts, by setting the `to` field to an 
empty string.

Transactions can be designed to fail, and a verification must be made that the
transaction fails with the specific error that matches what is expected by the
test.

## Writing code for the accounts in the test

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

## Verifying the Accounts' Post State

The state of the accounts after all blocks/transactions have been executed is
the way of verifying that the execution client actually behaves like the test
expects.

During their filling process, all tests automatically verify that the accounts
specified in their `post` property actually match what was returned by the
transition tool.

Within the `post` dictionary object, an account address can be:
- `None`: The account will not be checked for absence or existence in the
  result returned by the transition tool.
- `Account` object: The test expects that this account exist and also has
  properties equal to the properties specified by the `Account` object.
- `Account.NONEXISTENT`: The test expects that this account does not exist in
  the result returned by the transition tool, and if the account exists,
  it results in error.
  E.g. when the transaction creating a contract is expected to fail and the
  test wants to verify that the address where the contract was supposed to be
  created is indeed empty.

## The `Account` object

The `Account` object is used to specify the properties of an account to be
verified in the post state.

The python representation can be found in [src/ethereum_test_tools/common/types.py](https://github.com/ethereum/execution-spec-tests/blob/main/src/ethereum_test_tools/common/types.py).

It can verify the following properties of an account:
- `nonce`: the scalar value equal to a) the number of transactions sent by
  an Externally Owned Account, b) the amount of contracts created by a contract.
  
- `balance`: the amount of Wei (10<sup>-18</sup> Eth) the account has.

- `code`: Bytecode contained by the account. To verify that an account contains
  no code, this property needs to be set to "0x" or "".
  
  It is not recommended to verify Yul compiled code in the output account,
  because the bytecode can change from version to version.

- `storage`: Storage within the account represented as a `dict` object.
  All storage keys that are expected to be set must be specified, and if a
  key is skipped, it is implied that its expected value is zero.
  Setting this property to `{}` (empty `dict`), means that all the keys in the
  account must be unset (equal to zero).

All account's properties are optional, and they can be skipped or set to `None`,
which means that no check will be performed on that specific account property.

## Verifying correctness of the new test

A well written test performs a single verification output at a time.

A verification output can be a single storage slot, the balance of an account,
or a newly created contract.

It is not recommended to use balance changes to verify test correctness, as it
can be easily affected by gas cost changes in future EIPs.

The best way to verify a transaction/block execution outcome is to check its
storage.

A test can be written as a negative verification. E.g. a contract is not
created, or a transaction fails to execute or runs out of gas.

These verifications must be carefully crafted because it is possible to end up
having a false positive result, which means that the test passed but the
intended verification was never made.

To avoid these scenarios, it is important to have a separate verification to
check that test is effective. E.g. when a transaction is supposed to fail, it
is necessary to check that the failure error is actually the one expected by
the test.

## Failing or invalid transactions

Transactions included in a StateTest are expected to be intrinsically valid,
i.e. the account sending the transaction must have enough funds to cover the
gas costs, the max fee of the transaction must be equal or higher than the
base fee of the block, etc.

An intrinsically valid transaction can still revert during its execution.

Blocks in a BlockchainTest can contain intrinsically invalid transactions but
in this case the block is expected to be completely rejected, along with all
transactions in it, including other valid transactions.

[t8n]: https://github.com/ethereum/go-ethereum/tree/master/cmd/evm
[b11r]: https://github.com/ethereum/go-ethereum/pull/23843
[yul]: https://docs.soliditylang.org/en/latest/yul.html