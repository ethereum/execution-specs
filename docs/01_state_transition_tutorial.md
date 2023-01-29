# Writing State Transition Execution Spec Tests

In this tutorial you learn how to write state transition execution spec test.
This kind of test checks that if the blockchain is at a specific pre-state, and receives certain transactions, it gets to a specified post-state.


## Prerequisites

It is assumed you know or have done several things:

- Setup and run an execution spec test, [as explained here](../README.md#quick-start).
- Understand how to read a [static state transition test](https://ethereum-tests.readthedocs.io/en/latest/state-transition-tutorial.html#the-source-code).
- Know the basics of [Yul](https://docs.soliditylang.org/en/latest/yul.html), which is an EVM assembly language.
- Know the basics of [Python](https://docs.python.org/3/tutorial/).

## Sample tests

The best way to learn how to write tests is to go through a couple of simple examples.

### Yul Test

The source code for this test is [here](../fillers/example/example.py).
This is the spec test version of [this static test](https://github.com/ethereum/tests/blob/develop/src/GeneralStateTestsFiller/stExample/yulExampleFiller.yml).

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
It modifies the action of the function after it.
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
For most tests the defaults are good enough, but if you need to change them [see here for the class definition](../src/ethereum_test_tools/common/types.py#L445).
For more informration, [see the static test documentation](https://ethereum-tests.readthedocs.io/en/latest/test_filler/state_filler.html#env)

```python
    pre = {
```

Here we define the pre-state section, the one that tells us what is on the "blockchain" before the test.
It is a [dictionary](https://docs.python.org/3/tutorial/datastructures.html#dictionaries), which is the Python term for an associative array.
The keys of the dictionary are addresses (as strings), and the values are [`Account` objects](../src/ethereum_test_tools/common/types.py#L264).
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

Here we specify the [`Transaction`](../src/ethereum_test_tools/common/types.py#L516).
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

### Bad Opcode Test

The source code for this test is [here](../fillers/vm/opcode_tests.py).
We will only go over the parts that are new.

We use [Python string templates](https://docs.python.org/3/library/string.html#template-strings), so we need to import that library.

```python
from string import Template
```

In this test we need a couple of addresses, so we create them here.
Python lets us specify `<string>*<number>` when we need a string repeated multiple times, which makes for more readable code that `0x00...000c0de`.

```python
    codeAddr = "0x" + "0"*(40-4) + "c0de"
    goatAddr = "0x" + "0"*(40-4) + "60A7"
```

We create `env` and `tx` first because they are constant.
This function will `yield` multiple tests, but always with the same `env` and `tx` values.

```python
    env = Environment()

    tx = Transaction(
           .
           .
           .
        )
```

Here we create two post states.
We will use whichever one is appropriate to the test we create.

```python
    postValid = {
       codeAddr: Account(
         storage={0x00: 1},
       ),
    }

    postInvalid = {
       codeAddr: Account(
         storage={0x00: 0},
       ),
    }
```

Here we define a function (`opcValid`) inside another function.
Python supports this, and it has two advantages:

- Avoid namespace pollution by restricting the function to where it is needed.
- Functions defined inside other functions can use the parameters and local variables of those functions.
  In this case, we need to use `fork`.

```python
    # Check if an Opcode is valid
    def opcValid(opc):
        """
        Return whether opc will be evaluated as valid by the test or not.
        Note that some opcodes are evaluated as invalid because the way they act
        """
```

This is the syntax for Python comments, `# <rest of the line>`. 

```python
        # PUSH0 is only valid Shanghai and later
```

Opcode 0x5F (`PUSH0`) is only valid starting with the Shangai fork.
We don't know what will be the fork names after Shanghai, so it is easiest to specify that prior to Shanghai it is invalid.
We don't need to worry about forks prior to London because the decorator for this test says it is only valid from London.

Python has a [set data structure](https://docs.python.org/3/tutorial/datastructures.html#sets).
We use this structure when the order of the values is irrelevant, and we just want to be able to check if something is a member or not.

Note that [`if` statements](https://docs.python.org/3/tutorial/controlflow.html#if-statements) are also followed by a colon (`:`) and the code inside them indented.
That is the general Python syntax.

```python
        if fork in {"london", "merge"} and opc==0x5F:
```

Boolean values in Python are either `True` or `False`.

```python
            return False
```

The way this test works is it runs an opcode and then does a [`SSTORE`](https://www.evm.codes/#55?fork=merge).
Opcodes that terminate execution, such as [`STOP`](https://www.evm.codes/#00?fork=merge) and [`RETURN`](https://www.evm.codes/#f3?fork=merge) also cause the `SSTORE` not to happen, so they must be treated as invalid.
The same is true for [`JUMP`](https://www.evm.codes/#56?fork=merge)

```python
        # Valid opcodes, but they are terminal, and so cause
        # the SSTORE not to happen
        if opc in {0x00, 0xF3, 0xFD, 0xFF}:
            return False


        # Jumps. If you jump to a random location, you skip the SSTORE
        if opc in {0x56}:
            return False
```

Next we return `True` for supported opcodes.

```python
        # Opcodes that aren't part of a range
        # 0x20 - SHA3
        # 0xFA - STATICCALL
        if opc in {0x20, 0xFA}:
            return True

```

In Python, as in math, you can use `a < b < c` for `a < b and b < c`.


```python
        # Arithmetic opcodes
        if 0x01 <= opc <= 0x0b:
            return True

        .
        .
        .
```

The last part of the function returns `False`.
If we got here, then this is not a valid opcode.

```python
        return False
        # End of opcValid
```

Because this is the end of the function, the next code line is unindented (compared to the function definition code).

This is a [`for` loop](https://docs.python.org/3/tutorial/controlflow.html#for-statements).
For loops iterate over a sequnce, and the [`range`](https://docs.python.org/3/tutorial/controlflow.html#the-range-function) function, in this case, gives us the range 0..255.
As with functions and `if` statements, the `for` loop has a colon and includes the indented code.

```python
    # For every possible opcode
    for opc in range(256):
```

We have two post states. 
One, `postValid`, has the value of `1` in storage location `0`.
The other, `postInvalid` has the value of `0` in storage location `0`.
But `SELFDESTRUCT` destroys the contract so there is no longer an account at that address. 
Neither is valid, so we just skip that test case.

```python
        # We can't check SELFDESTRUCT using this technique
        if opc in {0xFF}:
           continue
```

The need the opcode in hexacedimal. 
The function [`hex`](https://docs.python.org/3/library/functions.html#hex) gives us the hexadecimal number in hex.
However, it also gives us a `0x` prefix, which we don't want, so we use a [slice](https://www.w3schools.com/python/gloss_python_string_slice.asp) to remove the first two characters.

```python
        opcHex = hex(opc)[2:]
```

The purpose of this `print` so to help debugging.
It is currently commented out.

```python
        # print(fork, opcHex)
```

We need `opcHex` to be two characters.
If the length is only one, prepend a zero.

```python
        if len(opcHex) == 1:
          opcHex = "0" + opcHex
```

This is a [`Template` string](https://docs.python.org/3/library/string.html#template-strings).
This means we'll be able to substitute template variables (`${<var name>}`) with values to produce the actual code.

```python
        yulCode = Template("""
        {
```

We start with a call `0x00...0060A7` (a.k.a. `goatAddr`) so we'll have some return data.
Otherwise, [`RETURNDATACOPY`](https://www.evm.codes/#3e?fork=merge) will fail and appear like it is not an opcode.

```python
           pop(call(gas(), 0x60A7, 0, 0,0, 0,0))

           // fails on opcodes with >20 inputs
           // (currently dup16, at 17 inputs, is the
           // one that goes deepest)
           //
           // Follow with 32 NOPs (0x5B) to handle PUSH, which has an immediate
           // operand
```

Opcodes can have two types of operands:

- Immediate operands, which are part of the bytecode.
  For example, `6001` is [`PUSH1`](https://www.evm.codes/#60?fork=merge) with the value `0x01`.
- Implied operands (a.k.a. stack operands), which come from the stack.

This [`verbatim`](https://docs.soliditylang.org/en/v0.8.17/yul.html#verbatim) code provides both operand types.
The code, `${opcode}${nop32}` is the opcode we are testing, followed by 32 copies of 0x5B.
When `0x5B` is not used as an operand, it is [`JUMPDEST`](https://www.evm.codes/#5b?fork=merge) and does nothing.

The syntax `${<name>}` 
```python
           verbatim_20i_0o(hex"${opcode}${nop32}",
```

The opcode string is followed by the input parameters (in this case, twenty of them).
These can be Yul expressions, but for the sake of simplicity here we just use constant values.

```python
              0x00, 0x00, 0x00, 0xFF, 0xFF,
              0xFF, 0xFF, 0xFF, 0xFF, 0xFF,
              0xFF, 0xFF, 0xFF, 0xFF, 0xFF,
              0xFF, 0xFF, 0xFF, 0xFF, 0xFF)
```

If the opcode terminates the smart contract execution (as invalid opcodes do), we don't get here.
If we do get here, write to storage cell 0 to record that fact.

Note the syntax `let <var> := <value>`. This is how you specify variables in Yul.

```python
           // We only get here is the opcode is legit (and it doesn't terminate
           // execution like STOP and RETURN)
           let zero := 0
           let one := 1
           sstore(zero, one)
        }
```

Replace `opcode` with the one byte hex code, and `nop32` with 32 copies of `5b` (for NOP).


```python
        """).substitute(opcode=opcHex, nop32="5b"*32)
        pre = {
           TestAddress: Account(balance=0x0BA1A9CE0BA1A9CE),
           codeAddr: Account(
		balance=0,
		nonce=1,
		code=Yul(yulCode)
           ),
```

This is the account for `0x00..0060A7`. 
It just returns data (all zeros).

```python
           goatAddr: Account(
                balance=0,
                nonce=1,
                code=Yul("{ return(0,0x100) }"),
           )
        }
```

Every time the `for` loop gets here, it [`yield`s](https://docs.python.org/3/reference/expressions.html#yieldexpr) a separate test. 
Over the entire for loop, is yields 255 different tests.

```python
        yield StateTest(env=env,
                        pre=pre,
                        txs=[tx],
```

The Python format for the [ternary operation](https://en.wikipedia.org/wiki/Ternary_conditional_operator) is a bit different from C-like languages.
In C like languages the syntax is `<condition> ? <yes value> : <no value>`.
In Python it is `<yes value> if <condition> else <no value>`. 


```python
                        post= postValid if opcValid(opc) else postInvalid)
```

## Conclusion

At this point you should be able to write exec spec tests for state transitions within a single block.
