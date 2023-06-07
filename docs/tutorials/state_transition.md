# State Transition Tests

This tutorial teaches you to create a state transition execution specification test. These tests verify that a blockchain, starting from a defined pre-state, will reach a specified post-state after executing a set of specific transactions.

## Pre-requisites

Before proceeding with this tutorial, it is assumed that you have prior knowledge and experience with the following:

- Set up and run an execution specification test as outlined in the [quick start guide](../getting_started/quick_start.md).
- Understand how to read a [static state transition test](https://ethereum-tests.readthedocs.io/en/latest/state-transition-tutorial.html#the-source-code).
- Know the basics of [Yul](https://docs.soliditylang.org/en/latest/yul.html), which is an EVM assembly language.
- Familiarity with [Python](https://docs.python.org/3/tutorial/).

## Example Tests

The most effective method of learning how to write tests is to study a couple of straightforward examples. In this tutorial we will go over the [Yul](https://github.com/ethereum/execution-spec-tests/blob/main/fillers/example/yul_example.py#L17) state test.

### Yul Test

You can find the source code for the Yul test [here](https://github.com/ethereum/execution-spec-tests/tree/main/fillers/example/example.py).
It is the spec test equivalent of this [static test](https://github.com/ethereum/tests/blob/develop/src/GeneralStateTestsFiller/stExample/yulExampleFiller.yml). 

Lets examine each section.

```python
"""
Test Yul Source Code Examples
"""
```

In Python, multi-line strings are denoted using `"""`. As a convention, a file's purpose is often described in the opening string of the file.

```python
from ethereum_test_forks import Berlin, Fork, forks_from
from ethereum_test_tools import (
    Account,
    Environment,
    StateTestFiller,
    TestAddress,
    Transaction,
    Yul,
)
```

In this snippet the required constants, types and helper functions are imported from `ethereum_test_tools` and `ethereum_test_forks`. We will go over these as we come across them.


```python
@pytest.mark.parametrize("fork", forks_from(Berlin))
```

In Python this kind of definition is called a [*decorator*](https://docs.python.org/3/search.html?q=decorator).
It modifies the action of the function after it.
In this case, the decorator is a [pytest fixture](https://docs.pytest.org/en/latest/explanation/fixtures.html) that parametrizes the test for the [Berlin fork](https://ethereum.org/en/history/#berlin) and the forks after it.

```python
def test_yul(state_test: StateTestFiller, fork: Fork):
    """
    Test YUL compiled bytecode.
    """
```

This is the format of a [Python function](https://docs.python.org/3/tutorial/controlflow.html#defining-functions).
It starts with `def <function name>(<parameters>):`, and then has indented code for the function.
The function definition ends when there is a line that is no longer indented. As with files, by convention functions start with a string that explains what the function does.


!!! info
    To execute this test for all the specified forks, we can specify pytest's `-k` flag that [filters test cases by keyword expression](https://docs.pytest.org/en/latest/how-to/usage.html#specifying-tests-selecting-tests):
    ```python
    pytest -k test_yul
    ```
    To execute it for a specific fork, the fork name can be combined in a Python evaluatable expression using `and` in the string:
    ```python
    pytest -k "test_yul and Shanghai"
    ```

!!! note "The `state_test` function argument"
    This test defines a state test and, as such, _must_ include the `state_test` in its function arguments. This is a callable object (actually a wrapper class to the `StateTest`); we will see how it is called later.


```python
    env = Environment()
```

This line specifies that `env` is an [`Environment`](https://github.com/ethereum/execution-spec-tests/blob/main/src/ethereum_test_tools/common/types.py#L445) object, and that we just use the default parameters.
If necessary we can modify the environment to have different block gas limits, block numbers, etc.
In most tests the defaults are good enough.

For more information, [see the static test documentation](https://ethereum-tests.readthedocs.io/en/latest/test_filler/state_filler.html#env).


#### Pre State


```python
    pre = {
```

Here we define the pre-state section, the one that tells us what is on the "blockchain" before the test.
It is a [dictionary](https://docs.python.org/3/tutorial/datastructures.html#dictionaries), which is the Python term for an associative array.

```python
        "0x1000000000000000000000000000000000000000": Account(
```

The keys of the dictionary are addresses (as strings), and the values are [`Account`](https://github.com/ethereum/execution-spec-tests/blob/main/src/ethereum_test_tools/common/types.py#L264) objects.
You can read more about address fields [in the static test documentation](https://ethereum-tests.readthedocs.io/en/latest/test_filler/state_filler.html#address-fields). 

```python
            balance=0x0BA1A9CE0BA1A9CE,
```

This field is the balance: the amount of Wei that the account has. It usually doesn't matter what its value is in the case of state test contracts.

```python
            code=Yul(
```

Here we define the [Yul](https://docs.soliditylang.org/en/v0.8.17/yul.html) code for the contract. It is defined as a multi-line string and starts and ends with curly braces (`{ <yul> }`).

When running the test filler `fill`, the solidity compiler `solc` will automatically translate the Yul to EVM opcode at runtime.

!!! note
    Currently Yul and direct EVM opcode are supported in execution spec tests. LLL and Solidity may be supported in the future.


```python
                """
                {
                    function f(a, b) -> c {
                        c := add(a, b)
                    }
                    sstore(0, f(1, 2))
                    return(0, 32)
                }
                """
            ),
        ),
```

Within this example test Yul code we have a function definition, and inside it we are using the Yul `add` instruction. When compiled with `solc` it translates the instruction directly to the`ADD` opcode. For further Yul instructions [see here](https://docs.soliditylang.org/en/latest/yul.html#evm-dialect). Notice that function is utilised with the Yul `sstore` instruction, which stores the result of `add(1, 2)` to the storage address `0x00`.

Generally for execution spec tests the `sstore` instruction acts as a high-level assertion method to check pre to post-state changes. The test filler achieves this by verifying that the correct value is held within post-state storage, hence we can validate that the Yul code has run successfully.

```python
        TestAddress: Account(balance=0x0BA1A9CE0BA1A9CE),
    }
```

[`TestAddress`](https://github.com/ethereum/execution-spec-tests/blob/main/src/ethereum_test_tools/common/constants.py#L8) is an address for which the test filler has the private key.
This means that the test runner can issue a transaction as that contract.
Of course, this address also needs a balance to be able to issue transactions.

#### Transactions

```python
    tx = Transaction(
        ty=0x0,
        chain_id=0x0,
        nonce=0,
        to="0x1000000000000000000000000000000000000000",
        gas_limit=500000,
        gas_price=10,
        protected=False,
    )
```

With the pre-state specified, we can add a description for the [`Transaction`](https://github.com/ethereum/execution-spec-tests/blob/main/src/ethereum_test_tools/common/types.py#L516).
For more information, [see the static test documentation](https://ethereum-tests.readthedocs.io/en/latest/test_filler/state_filler.html#transaction)

#### Post State

```python
    post = {
        "0x1000000000000000000000000000000000000000": Account(
            storage={
                0x00: 0x03,
            },
        ),
    }
```

This is the post-state which is equivalent to [`expect`](https://ethereum-tests.readthedocs.io/en/latest/test_filler/state_filler.html#expect) in static tests, but without the indexes. It is similar to the pre-state, except that we do not need to specify everything, only those accounts and fields we wish to test.

In this case, we look at the storage of the contract we called and add to it what we expect to see. In this example storage cell `0x00` should be `0x03` as in the pre-state we essentially stored the result of the Yul instruction `add(1, 2)`.

#### State Test

```python
    state_test(env=env, pre=pre, post=post, txs=[tx])
```

This line calls the wrapper to the `StateTest` object that provides all the objects required (for example, the fork parameter) in order to fill the test, generate the test fixtures and write them to file (by default, `../out/example/yul_example/test_yul.json`).
## Conclusion

At this point you should be able to state transition tests within a single block.
