# Evaluation Tests

The `evaluate` command runs tests against the specification without producing fixtures. An evaluation test runs blocks of transactions through the transition tool as many times as it needs, and checks the results with plain Python assertions. The outcome of the test is the result.

!!! note "When to use `evaluate`"
    Use `fill` to produce fixtures that clients consume. Use `evaluate` to answer a question about how the specification behaves for a given input, where the inputs of one run depend on the results of previous runs, or where the result is a pass or fail rather than a fixture.

## Writing an Evaluation Test

`evaluate` collects functions named `eval_*` in files named `eval_*.py`, so `fill` never collects them, and `evaluate` never collects `test_*` functions. Evaluation tests use the same `pre` fixture and fork markers as other tests, plus the `spec` fixture, a `SpecRunner` for the test's fork:

```python
import pytest

from execution_testing import Alloc, Op, SpecRunner, Transaction


@pytest.mark.valid_from("Cancun")
def eval_store_value(spec: SpecRunner, pre: Alloc) -> None:
    """Check that the contract stores its input plus one."""
    contract = pre.deploy_contract(
        code=Op.SSTORE(0, Op.ADD(Op.CALLDATALOAD(0), 1)) + Op.STOP
    )
    tx = Transaction(to=contract, gas_limit=100_000, sender=pre.fund_eoa())
    for value in range(3):
        run = spec.run(pre=pre, txs=[tx.copy(data=value.to_bytes(32))])
        assert run.tx(tx).successful
        assert run.storage(contract, 0) == value + 1
    spec.record(runs=3)
```

### Running the Specification

`spec.run(pre=..., txs=[...])` executes the transactions in one block on top of `pre`. `spec.run(pre=..., blocks=[...])` executes several blocks. Blocks form a chain on top of a genesis block, so block numbers are consecutive; if the first block sets `number=N`, the genesis is block `N - 1`.

A run checks what the blocks expect, as `fill` does: a transaction or block that the specification rejects, and that is not expected to fail (`error=` / `exception=`), raises an exception, and so does a block whose `expected_post_state` or `expected_block_access_list` does not match.

Every run starts from the `pre` it is given, so runs are independent of each other. Creating a `Transaction` from a sender increments the sender's nonce, so create each transaction once and vary it with `tx.copy(...)`.

`spec.run(..., traces=True)` collects the execution traces of the run's transactions (see [Inspecting Traces](#inspecting-traces)). Only the run decides whether it collects traces, so `evaluate` has no `--traces` option: a test that reads traces asks for them, and passes or fails the same way however it is run.

The returned `SpecRun` provides:

| Attribute               | Content                                                                  |
| ----------------------- | ------------------------------------------------------------------------ |
| `tx(tx)`                | The outcome of transaction `tx` (see below).                             |
| `block(block)`          | The outcome of `block`, one of the blocks passed with `blocks=`.         |
| `txs`                   | The outcome of every transaction of the run, in order.                   |
| `successful` / `failed` | Whether every block is valid and every transaction succeeded.            |
| `post`                  | The state after the last valid block.                                    |
| `storage(address, k)`   | The value of storage slot `k` of `address` after the run.                |
| `receipts`              | The receipts of all transactions, in order.                              |
| `logs(address)`         | The logs of all transactions, optionally of one address.                 |
| `traces`                | The raw traces of each block, when the run collected traces.             |
| `blocks` / `results`    | The built blocks and the transition tool result of each block.           |

### Checking Transactions and Blocks

`run.tx(tx)` returns the outcome of a transaction the test passed to the run. The transition tool runs copies of the transactions it is given (signed, with a gas limit), so the transaction is found by its sender and nonce: `tx` can be the object the test created. It raises `KeyError` when no transaction of the run has that sender and nonce, and `ValueError` when several do, for example when a transaction of an invalid block is sent again in a later block; use `run.block(block).txs` then.

| Attribute               | Content                                                                    |
| ----------------------- | -------------------------------------------------------------------------- |
| `successful` / `failed` | Whether the transaction ran and succeeded (raises before Byzantium).       |
| `rejected`              | Whether the transaction was rejected, so it never ran.                     |
| `receipt`               | The receipt of the transaction (`None` when it was rejected).              |
| `logs`                  | The logs the transaction emitted.                                          |
| `trace`                 | The trace of the transaction (`None` when it was rejected).                |
| `error`                 | The `TraceError` that stopped the transaction, or `None`.                  |
| `tx`                    | The transaction as the transition tool ran it.                             |

`run.block(block)` returns the outcome of a block: `successful` / `failed` (the block is valid and all its transactions succeeded), `txs` (the outcome of each of its transactions) and `built` (the block as the transition tool built it).

The examples below also import `Conditional`, `Hash` and `TraceError` from `execution_testing`.

```python
@pytest.mark.valid_from("Cancun")
def eval_revert(spec: SpecRunner, pre: Alloc) -> None:
    """Check that a reverting call does not emit the log of its caller."""
    reverter = pre.deploy_contract(code=Op.REVERT(0, 0))
    emitter = pre.deploy_contract(code=Op.LOG1(0, 0, 0xAA) + Op.STOP)
    sender = pre.fund_eoa()
    revert_tx = Transaction(to=reverter, gas_limit=100_000, sender=sender)
    log_tx = Transaction(to=emitter, gas_limit=100_000, sender=sender)
    run = spec.run(pre=pre, txs=[revert_tx, log_tx], traces=True)
    assert run.tx(revert_tx).error == TraceError.REVERT
    assert run.tx(revert_tx).logs == []
    assert [log.topics[0] for log in run.tx(log_tx).logs] == [Hash(0xAA)]
    assert run.failed
```

### Inspecting Traces

`run.tx(tx).trace` and `run.tx(tx).error` read the trace of the transaction, so they raise unless the run collected traces (`spec.run(..., traces=True)`).

A `Trace` holds the trace lines of a transaction, or of one call frame of it. A frame is one execution of one call: it starts when execution enters a depth from the depth above, and holds the lines that run at that depth until the call returns. The lines of the calls it makes belong to frames of their own, and two calls to the same contract are two frames. Depths follow EIP-3155: the top frame of a transaction is at depth 1.

| Attribute             | Content                                                                         |
| --------------------- | ------------------------------------------------------------------------------- |
| `ops`                 | The opcodes that ran, in order, as `Op` values.                                 |
| `op in trace`         | Whether opcode `op` ran (`Op.SSTORE in trace`).                                 |
| `count(op)`           | The number of times opcode `op` ran.                                            |
| `len(trace)`          | The number of trace lines.                                                      |
| `at_depth(n)`         | The frames at depth `n`, in the order they started.                             |
| `at_address(address)` | The frames that executed at `address`, in the order they started.               |
| `addresses`           | The addresses that frames executed at, in the order they first did.            |
| `error`               | The `TraceError` that stopped the frame or transaction, or `None`.              |
| `failed_at`           | The opcode that stopped the frame, or the top frame of a transaction, or `None`. |
| `depth` / `address`   | The depth and address of a frame (`None` for the trace of a transaction).       |
| `lines`               | The raw trace lines.                                                            |

`at_depth` and `at_address` return frames, which are `Trace` objects as well, so they can be inspected the same way. A frame is its own only frame: `frame.at_depth(frame.depth)` is `[frame]`.

The address of a frame is the address it executed at, whose storage it can change:

- A `CALL` or `STATICCALL` frame executes at the address it called.
- A `DELEGATECALL` or `CALLCODE` frame executes at its caller's address, so the address of the code it ran does not appear in `at_address` or `addresses`.
- A frame that ran initcode (a `CREATE`, a `CREATE2` or a contract-creating transaction) executes at the address it created. A `CREATE` or `CREATE2` that failed has no address.

```python
@pytest.mark.valid_from("Cancun")
def eval_second_call_reverts(spec: SpecRunner, pre: Alloc) -> None:
    """Check that only the second of two calls to a contract reverts."""
    callee = pre.deploy_contract(
        code=Conditional(
            condition=Op.EQ(Op.CALLDATALOAD(0), 2),
            if_true=Op.REVERT(0, 0),
            if_false=Op.SSTORE(0, 1),
        )
        + Op.STOP
    )
    caller = pre.deploy_contract(
        code=Op.MSTORE(0, 1)
        + Op.POP(Op.CALL(gas=100_000, address=callee, args_size=32))
        + Op.MSTORE(0, 2)
        + Op.POP(Op.CALL(gas=100_000, address=callee, args_size=32))
        + Op.STOP
    )
    tx = Transaction(to=caller, gas_limit=500_000, sender=pre.fund_eoa())
    run = spec.run(pre=pre, txs=[tx], traces=True)
    trace = run.tx(tx).trace
    assert trace.addresses == [caller, callee]
    first, second = trace.at_address(callee)
    assert first.error is None
    assert second.error == TraceError.REVERT
    assert second.failed_at == Op.REVERT
    assert trace.error is None  # The caller does not fail.
```

#### Errors

`error` is a member of the `TraceError` enum, never a string, so a test compares it with a member: `trace.error == TraceError.OUT_OF_GAS`. The members are `REVERT`, `OUT_OF_GAS`, `STACK_UNDERFLOW`, `STACK_OVERFLOW`, `STACK_DEPTH_LIMIT`, `INVALID_OPCODE`, `INVALID_JUMP_DESTINATION`, `WRITE_IN_STATIC_CONTEXT`, `OUT_OF_BOUNDS_READ`, `INVALID_PARAMETER`, `INVALID_CONTRACT_PREFIX`, `ADDRESS_COLLISION` and `KZG_PROOF`.

A frame failed when its last line raised: a frame whose call failed but that went on to complete has no error. `failed_at` of a transaction is that of its top frame, so it is `None` when only a call the transaction made failed.

!!! note "What traces do not show"
    The transition tool does not trace precompiles, so a call to a precompile has no frame: its result is on the caller's stack. A byte that is not an opcode has no `Op`: it is left out of `ops`, and `failed_at` is `None` when a frame stopped at it, with `error` set to `TraceError.INVALID_OPCODE`.

### Recording Values

`spec.record(key=value, ...)` attaches values to the result of the test. They are shown in the "evaluation results" section of the terminal summary and written to the JSON report.

Recorded values are converted to built-in types as they are recorded: integers such as `HexNumber` or `Uint` to `int`, values that convert to bytes such as `Address`, `Hash` or `Bytecode` to hex strings, enums to their value, pydantic models to their JSON form, and lists, tuples, sets and dictionaries element by element. A value that cannot be converted fails the test at the call that records it.

## Running Evaluation Tests

```console
uv run evaluate tests/ --until Amsterdam
uv run evaluate tests/ --fork Prague --eval-report results.json
```

`evaluate` accepts the fork selection options of `fill` (`--fork`, `--from`, `--until`), the transition tool options (`--evm-bin`, `--evm-dump-dir`) and pytest options such as `-n` and `-k`.

### The JSON Report

`--eval-report` writes a JSON file with the version of the report format, the environment of the run and the result of each test:

```json
{
  "version": 1,
  "env": {
    "t8n": "2.18.0",
    "commit": "a1b2c3d4..."
  },
  "results": [
    {
      "test": "tests/cancun/eval_calldata.py::eval_calldata_gas[Cancun-32]",
      "outcome": "passed",
      "fork": "Cancun",
      "params": {"size": 32},
      "runs": 1,
      "records": {"gas_used": 21512}
    }
  ]
}
```

Each result holds the outcome, fork, parameters, number of runs and recorded values of a test, and the failure message of a failed test. A test whose setup failed, for example because a fixture raised, is reported with the outcome `error`. `params` holds the parameters of the test other than its fork, converted as recorded values are; a parameter that cannot be converted is left out.
