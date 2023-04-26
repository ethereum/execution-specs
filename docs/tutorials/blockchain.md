# Blockchain Tests

This tutorial teaches you to create a blockchain execution specification test. These tests verify that a blockchain, starting from a defined pre-state, will process given blocks and arrive at a defined post-state.


## Pre-requisites

Before proceeding with this tutorial, it is assumed that you have prior knowledge and experience with the following:

- Set up and run an execution specification test as outlined in the [quick start guide](../getting_started/quick_start.md).
- Understand how to read a [blockchain test](https://ethereum-tests.readthedocs.io/en/latest/test_filler/blockchain_filler.html).
- Know the basics of [Yul](https://docs.soliditylang.org/en/latest/yul.html), which is an EVM assembly language.
- Familiarity with [Python](https://docs.python.org/3/tutorial/).
- Understand how to write an execution spec [state transition test](./state_transition.md).


## Example Tests

In this tutorial we will go over [test_block_number] in `block_example.py`(https://github.com/ethereum/execution-spec-tests/tree/main/fillers/example/block_example.py#L19).

It is assumed you have already gone through the state transition test tutorial. Only new concepts will be discussed.


### Smart Contract

A smart contract is defined that is called by each transaction in the test. It stores a pointer to storage at `storage[0]`. When it is called storage cell `0` gets the current block [number](https://www.evm.codes/#43?fork=merge), and the pointer is incremented to the next value.


```python
contract_addr: Account(
    balance=1000000000000000000000,
    code=Yul(
        """
        {
            let next_slot := sload(0)
            sstore(next_slot, number())
            sstore(0, add(next_slot, 1))
        }
        """
    ),
    storage={
        0x00: 0x01,
    },
),
```


### Transaction Generator

The transactions used in this test are nearly identical. Their only different is the `nonce` value which needs to be incremented. 

```python
def tx_generator():
    nonce = 0  # Initial value
    while True:
        tx = Transaction(
            ty=0x0,
            chain_id=0x0,
            nonce=nonce,
            to=contractAddr,
            gas_limit=500000,
            gas_price=10,
        )
        nonce = nonce + 1
        yield tx

tx_generator = tx_generator()
```

This looks like an infinite loop but it isn't because this is a [generator function](https://wiki.python.org/moin/Generators). When generator encounters the `yield` keyword it returns the value and stops execution, keeping a copy of all the local variables, until it is called again. Hence infinite loops inside a generator are not a problem as long as they include `yield`. This code section is responsible for creating the `Transaction` object and incrementing the `nonce`.


Every time the function `tx_generator()` is called, it returns a new generator with a `nonce` of zero. To increment the `nonce` we need to use the *same* generator. We assign this generator to `tx_generator`.


### Blocks

Each integer in the `tx_per_block` array is the number of transactions in a block. The genesis block is block 0 (no transactions). It follows that we have 2 transactions in block 1, 0 in block two, 4 in block 3, ..., and 50 in block 9.

```python
tx_per_block = [2, 0, 4, 8, 0, 0, 20, 1, 50]
```

The code section that creates the blocks is a bit complex in this test. For some simpler definitions of Block creation you can browse tests within [`withdrawals.py`](https://github.com/ethereum/execution-spec-tests/blob/main/fillers/withdrawals/withdrawals.py).

```python
blocks = map(
    lambda len: Block(
        txs=list(map(lambda x: next(tx_generator), range(len)))
    ),
    tx_per_block,
)
```

We use [`lambda` notation](https://www.w3schools.com/python/python_lambda.asp) to specify short functions. In this case, the function doesn't actually care about its input, it just returns the next transaction from the generator.

```python
lambda x: next(tx_generator)
```

Python uses [`range(n)`](https://www.w3schools.com/python/ref_func_range.asp) to create a list of numbers from `0` to `n-1`. Among other things, it's a simple way to create a list of `n` values.

```python
range(len)
```

The [`map` function](https://www.w3schools.com/python/ref_func_map.asp) runs the function (the first parameter) on every element of the list (the second parameter). Putting together what we know, it means that it runs `next(tx_generator)` `len` times, giving us `len` transactions. We then use [`list`](https://www.w3schools.com/python/python_lists.asp) to turn the transactions into a list that we can provide as the `txs` parameter to the `Block` constructor.

```python
list(map(lambda x: next(tx_generator), range(len)))
```

The outer `lambda` function takes an integer, `len`, and creates a `Block` object with `len` transactions. This function is then run on every value of `tx_per_block` to generate the blocks.

```python
blocks = map(
    lambda len: Block(
        txs=list of len transactions
    ),
    tx_per_block,
)
```

For example, if we had `tx_per_block = [0,2,4]`, we'd get this result:

```python
blocks = [
    Blocks(txs=[]),
    Blocks(txs=[next(tx_generator), next(tx_generator)]),
    Blocks(txs=[next(tx_generator), next(tx_generator), next(tx_generator), next(tx_generator)])        
]
```


### Post State

Recall that storage slot 0 retains the value of the next slot that the block number is written into. It starts at one and is incremented after each transaction. Hence it's the total number of transactions plus 1.

```python
storage = {0: sum(tx_per_block) + 1}
```

For every block and transaction within the block, we write the block number and increment the next slot number in storage slot 0. As Python lists are 0 indexed, we must increment the block number by 1.

```python
next_slot = 1
for blocknum in range(len(tx_per_block)):
    for _ in range(tx_per_block[blocknum]):
        storage[next_slot] = blocknum + 1
        next_slot = next_slot + 1
``` 

Now that the expeced storage values are calculated, the post state can be defined and yielded within the `BlockchainTest`, synonymous to the state test example.

```python
post = {contract_addr: Account(storage=storage)}

yield BlockchainTest(
    genesis_environment=env,
    pre=pre,
    blocks=blocks,
    post=post,
)
```

Note that because of the `yield` we could have multiple tests under the same name.

## Conclusion

At this point you should be able to write blockchain tests.
