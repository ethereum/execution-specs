# State Transition Tests

This tutorial teaches you to create a state transition execution specification test using the Python Opcodes minilang for writing EVM bytecode. These tests verify that a starting pre-state will reach a specified post-state after executing a single transaction. In this example, we'll create a simple contract using bytecode and then interact with it through a transaction to verify the expected state changes.

For an overview of different test types available, see [Types of Tests](../../writing_tests/types_of_tests.md).

## Pre-requisites

This tutorial will require some prior knowledge and experience with the following:

- Repository set-up, see [installation](../../getting_started/installation.md).
- Ability to run `fill`, see [Getting Started: Filling Tests](../../filling_tests/getting_started.md).
- Basic familiarity with [Python](https://docs.python.org/3/tutorial/).

## Building a State Test

The most effective method of learning how to write tests is to study a straightforward example. In this tutorial we will build a simple state test that deploys a contract with bytecode and verifies its execution.

### Complete Test Example

We'll examine a simple test that uses the Python Opcodes minilang to write EVM bytecode. This example is based on the CHAINID opcode test from `tests/istanbul/eip1344_chainid/test_chainid.py`.

Let's examine each section.

```python
"""State test tutorial demonstrating contract deployment and interaction."""
```

In Python, multi-line strings are denoted using `"""`. As a convention, a file's purpose is often described in the opening string of the file.

```python
import pytest

from ethereum_test_tools import Account, Alloc, Environment, StateTestFiller, Transaction
from ethereum_test_vm import Opcodes as Op
```

In this snippet the required constants, types and helper functions are imported from `ethereum_test_tools`. The `Opcodes` class (aliased as `Op`) provides the Python minilang for writing EVM bytecode. We will go over these as we come across them.

```python
@pytest.mark.valid_from("Istanbul")
```

In Python this kind of definition is called a [*decorator*](https://docs.python.org/3/search.html?q=decorator).
It modifies the action of the function after it.
In this case, the decorator is a custom [pytest mark](https://docs.pytest.org/en/latest/how-to/mark.html) defined by the execution-specs-test framework that specifies that the test is valid for the [Istanbul fork](https://ethereum.org/en/history/#istanbul) and all forks after it. The framework will then fill this test case for all forks in the fork range specified by the command-line arguments.

For more information about test markers and fork validity, see [Test Markers](../../writing_tests/test_markers.md).

!!! info "Filling the test"
    To fill this test for all the specified forks, we can specify pytest's `-k` flag that [filters test cases by keyword expression](https://docs.pytest.org/en/latest/how-to/usage.html#specifying-tests-selecting-tests):

    ```console
    fill -k test_state_test_example
    ```

    and to fill it for a specific fork range, we can provide the `--from` and `--until` command-line arguments:

    ```console
    fill -k test_state_test_example --from London --until Paris
    ```

```python
def test_state_test_example(state_test: StateTestFiller, pre: Alloc):
    """Test state transition using Opcodes minilang bytecode."""
```

This is the format of a [Python function](https://docs.python.org/3/tutorial/controlflow.html#defining-functions).
It starts with `def <function name>(<parameters>):`, and then has indented code for the function.
The function definition ends when there is a line that is no longer indented. As with files, by convention functions start with a string that explains what the function does.

The function parameters (`state_test` and `pre`) are [pytest fixtures](https://docs.pytest.org/en/latest/explanation/fixtures.html) provided by the execution-spec-tests framework. Pytest fixtures are a powerful dependency injection mechanism that automatically provide objects to your test functions.

**The `state_test` fixture** is a callable that you *must* include in *state test* function arguments. When called at the end of your test function with the environment, pre-state, transaction, and expected post-state, it generates the actual test fixtures. This callable is a wrapper around the `StateTest` class.

**The `pre` fixture** provides an `Alloc` object that manages the pre-state allocation for your test. It offers methods like `fund_eoa()` and `deploy_contract()` that automatically generate unique addresses and add accounts to the blockchain state that will exist before your transaction executes. The fixture handles address generation and ensures no conflicts occur.

```python
    env = Environment(number=1)
```

This line specifies that `env` is an [`Environment`][ethereum_test_types.Environment] object. In this example, we only override the block `number` to 1, leaving all other values at their defaults. It's recommended to use default values whenever possible and only specify custom values when required for your specific test scenario. (For all available fields, see the pydantic model fields in the source code of [`Environment`][ethereum_test_types.Environment] and [`EnvironmentGeneric`](https://github.com/ethereum/execution-spec-tests/blob/b4d7826bec631574a6fb95d0c58d2c8c4d6e02ca/src/ethereum_test_types/block_types.py#L76) from which `Environment` inherits.)

#### Pre State

For every test we need to define the pre-state requirements, so we are certain of what is on the "blockchain" before the transaction is executed. The `pre` fixture provides an `Alloc` object with methods to create accounts that are automatically added to the pre-state.

In this example we are using the `deploy_contract` method to deploy a contract to some address available in the pre-state.

```python
    contract_address = pre.deploy_contract(
        code=Op.PUSH1(0x03) + Op.PUSH1(0x00) + Op.SSTORE + Op.STOP
    )
```

Specifically we deploy a contract written with Opcodes minilang code that stores the value `0x03` at storage slot `0x00`. The code consists of:

- `PUSH1(0x03)`: Push the value 3 onto the stack.
- `PUSH1(0x00)`: Push the storage key 0 onto the stack.
- `SSTORE`: Store the value at the specified key.
- `STOP`: End execution.

As the return value of the `deploy_contract` method, we get the address where the contract was deployed. This address is stored in the `contract_address` variable, which will later be used as the target of our transaction.

You can also specify additional parameters for the contract if needed:

- `balance` parameter to set the contract's initial balance (though often not necessary for state test contracts)
- `storage` parameter to set initial storage values (though in this example we don't need initial storage since our contract will set it through the `SSTORE` opcode)

You can combine opcodes using the `+` operator to create more complex bytecode sequences.

Generally for execution spec tests the `SSTORE` instruction acts as a high-level assertion method to check pre to post-state changes. The test filler achieves this by verifying that the correct value is held within post-state storage, hence we can validate that the bytecode has run successfully.

Next, we need to create an account that will send the transaction to our contract:

```python
    sender = pre.fund_eoa()
```

This line creates a single externally owned account (EOA) with a default balance. You can specify a custom amount with `amount=0x0BA1A9CE0BA1A9CE` if needed.

The returned object, which includes a private key, an address, and a nonce, is stored in the `sender` variable and will later be used as the sender of the transaction.

#### Transactions

```python
    tx = Transaction(
        ty=0x2,
        sender=sender,
        to=contract_address,
        gas_limit=100_000,
    )
```

With the pre-state built, we can now create the transaction that will call our contract. Let's examine the key components of this [`Transaction`][ethereum_test_types.Transaction] (for all available fields, see the source code of [`Transaction`][ethereum_test_types.Transaction] and [`TransactionGeneric`](https://github.com/ethereum/execution-spec-tests/blob/b4d7826bec631574a6fb95d0c58d2c8c4d6e02ca/src/ethereum_test_types/transaction_types.py#L163) from which `Transaction` inherits).

- **`sender=sender`**: We use the EOA we created earlier, which already has the necessary information to sign the transaction and contains the correct `nonce`. The `nonce` is a protection mechanism to prevent replay attacks - it must equal the number of transactions sent from the sender's address, starting from zero. The framework automatically manages nonce incrementing for us.

- **`to=contract_address`**: This specifies the address of the contract we want to call, which is the contract we deployed earlier.

- **`gas_limit=100_000`**: This sets a high enough gas limit to ensure our simple contract execution doesn't run out of gas.

- **`ty=0x2`**: This specifies the transaction type (EIP-1559).

#### Post State

Now we need to define what we expect the blockchain state to look like after our transaction executes:

```python
    post = {
        contract_address: Account(
            storage={
                0x00: 0x03,
            },
        ),
    }
```

This is the post-state which is equivalent to [`expect`](https://ethereum-tests.readthedocs.io/en/latest/test_filler/state_filler.html#expect) in static tests, but without the indexes. It is similar to the pre-state, except that we do not need to specify everything, only those accounts and fields we wish to test.

In this case, we look at the storage of the contract we called and add to it what we expect to see. In this example storage cell `0x00` should be `0x03` as we stored this value using the `SSTORE` opcode in our contract bytecode.

#### Running the State Test

Finally, we execute the test by calling the state test wrapper with all our defined components:

```python
    state_test(env=env, pre=pre, post=post, tx=tx)
```

This line calls the wrapper to the `StateTest` object that provides all the objects required in order to fill the test, generate the test fixtures and write them to file (by default, `./fixtures/<blockchain,state>_tests/example/state_test_example/test_state_test_example.json`).

Note that even though we defined a `StateTest`, the `fill` command will also generate other derivative test fixtures: `BlockchainTest`, `BlockchainTestEngine`, and `BlockchainTestEngineX`. For more information about test types and when to use each, see [Test Types: Prefer StateTest for Single Transactions](../types_of_tests.md#prefer-state_test-for-single-transactions).

## Conclusion

At this point you should be able to write state transition tests within a single block.

## Next Steps

- Learn about [Adding a New Test](../../writing_tests/adding_a_new_test.md) to understand test organization and structure.
- Explore [Fork Methods](../../writing_tests/fork_methods.md) for writing tests that adapt to different Ethereum forks.
