# Writing Execution Spec Tests

In this tutorial you learn how to write an execution spec test.

## Prerequisites

It is assumed you have know or have several things:

- Setup and run an execution spec test, [as explained here](README.md#quick-start).
- Understand how to read a [static state transition test](https://ethereum-tests.readthedocs.io/en/latest/state-transition-tutorial.html#the-source-code).
- Know the basics of [Yul](https://docs.soliditylang.org/en/latest/yul.html), which is an EVM assembly language.
- Know the basics of [Python](https://docs.python.org/3/tutorial/).

## Sample tests

We will start by going through a couple of tests in the repository line by line.

### example.py

The source code for this test is [here](fillers/example/example.py).
This is the spec_test version of [this static test](https://github.com/ethereum/tests/blob/develop/src/GeneralStateTestsFiller/stExample/yulExampleFiller.yml).

```python
"""
Test Yul Source Code Examples
"""
```

Python uses `"""` to start and end multi-line strings.
By convention, we start a file with a string that explains what the file does.


```python
from ethereum_test_tools import (
    Account,
    Environment,
    StateTest,
    TestAddress,
    Transaction,
    Yul,
    test_from,
)
```

Import the relevant packages from `ethereum_test_tools`.
We will go over these packages as we come across them.


```python
@test_from("berlin")
```

In Python this kind of definition is called a [*decorator*](https://docs.python.org/3/search.html?q=decorator).
It modifies the function of the function after it.
In this case, it specifies to the test running code that the following function is only a valid test for the [Berlin fork](https://ethereum.org/en/history/#berlin) and the forks after it.

```python
def test_yul(fork):
    """
    Test YUL compiled bytecode.
    """
```

This is the format of a [Python function](https://docs.python.org/3/tutorial/controlflow.html#defining-functions).
It starts with `def <function name>(<parameters>):`, and then has indented code for the function.
The function definition ends when there is a line that is no longer indented.

The name `test_yul` means that to run the test you just call it `yul`:

```sh
tf --test-case yul --output fixtures
```

As with files, by convention functions start with a string that explains what the function does.


```python
    env = Environment()
```

This line specifies that `env` is an `Environment` object, and that we just use the default parameters.
If necessary we can modify the environment to have different block gas limits, block numbers, etc.
For most tests the defaults are good enough, but if you need to change them [see here for the class definition](src/ethereum_test_tools/common/types.py#L445).
For more informration, [see the static test documentation](https://ethereum-tests.readthedocs.io/en/latest/test_filler/state_filler.html#env)

```python
    pre = {
```

Here we define the pre-state section, the one that tells us what is on the "blockchain" before the test.
It is a [dictionary](https://docs.python.org/3/tutorial/datastructures.html#dictionaries), which is the Python term for an associative array.
The keys of the dictionary are addresses (as strings), and the values are [`Account` objects](src/ethereum_test_tools/common/types.py#L264).
You can read most about address fields [in the static test documentation](https://ethereum-tests.readthedocs.io/en/latest/test_filler/state_filler.html#address-fields), but note that LLL and Solidity are not supported in spec tests yet.

```python
        "0x1000000000000000000000000000000000000000": Account(
```

This field is the balance, the amount of Wei that the account has.
This usually doesn't matter in the case of contracts.

```python
            balance=0x0BA1A9CE0BA1A9CE,
```

Here we define the [Yul](https://docs.soliditylang.org/en/v0.8.17/yul.html) code for the contract.
The system will automatically translate it to EVM machine language for us.

```python
            code=Yul(
```

The Yul code is provided as a multi-line string.
The Yul code has to start and end with brackets (`{ <yul> }`).

```python
                """
            {
```

This is a Yul function definition.
Notice that to call an opcode, such as `ADD`, we use the opcode's name in lowercase as a function.
For a list of all the opcodes, [see here](https://www.evm.codes/?fork=merge).

```python
                function f(a, b) -> c {
                    c := add(a, b)
                }
```

Store the result of `add(1,2)` in storage cell 0.
This is the typical way for execution tests to provide their results.
As you will see a bit later, the test runner looks at the contract storage to see if the test is successful.

```python
                sstore(0, f(1, 2))
                return(0, 32)
            }
            """
            ),
        ),
```

[`TestAddress`](https://github.com/ethereum/execution-spec-tests/blob/main/src/ethereum_test_tools/common/constants.py#L8) is an address for which the test runner has the private key.
This means that the test runner can issue a transaction as that contract.
Of course, this contract also needs a balance to be able to issue transactions.


```python
        TestAddress: Account(balance=0x0BA1A9CE0BA1A9CE),
    }
```

Here we specify the [`Transaction`](src/ethereum_test_tools/common/types.py#L516).
For more informration, [see the static test documentation](https://ethereum-tests.readthedocs.io/en/latest/test_filler/state_filler.html#transaction)

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

This is the post-state (equivalent to [`expect`](https://ethereum-tests.readthedocs.io/en/latest/test_filler/state_filler.html#expect) in static tests, but without the indexes).
It is similar to the pre-state, except that we do not need to specify everything, only those accounts and fields we wish to test.
In this case, we look at the storage of the contract we called to see that storage cell 0 is indeed 3 (`add(1,2)`).

```python
    post = {
        "0x1000000000000000000000000000000000000000": Account(
            storage={
                0x00: 0x03,
            },
        ),
    }
```

This line produces the actual state test and returns it. 
It is `yield`, rather than `return`, because a single function can return multiple test cases as you'll see in the next example.

```python
    yield StateTest(env=env, pre=pre, post=post, txs=[tx])
```
