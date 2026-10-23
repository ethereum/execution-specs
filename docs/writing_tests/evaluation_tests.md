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
        assert int(run.receipts[0].status) == 1
        assert run.storage(contract, 0) == value + 1
    spec.record(runs=3)
```

### Running the Specification

`spec.run(pre=..., txs=[...])` executes the transactions in one block on top of `pre`. `spec.run(pre=..., blocks=[...])` executes several blocks. Blocks form a chain on top of a genesis block, so block numbers are consecutive; if the first block sets `number=N`, the genesis is block `N - 1`. A transaction or block that the specification rejects, and that is not expected to fail (`error=` / `exception=`), raises an exception.

Every run starts from the `pre` it is given, so runs are independent of each other. Creating a `Transaction` from a sender increments the sender's nonce, so create each transaction once and vary it with `tx.copy(...)`.

The returned `SpecRun` provides:

| Attribute              | Content                                                          |
| ---------------------- | ---------------------------------------------------------------- |
| `post`                 | The state after the last valid block.                            |
| `receipts`             | The receipts of all transactions, in order.                      |
| `logs(address)`        | The logs of all transactions, optionally of one address.         |
| `storage(address, k)`  | The value of storage slot `k` of `address` after the run.        |
| `traces`               | The traces of each block, when run with `--traces`.              |
| `blocks` / `results`   | The built blocks and the transition tool result of each block.   |

### Recording Values

`spec.record(key=value, ...)` attaches values to the result of the test. They are shown in the "evaluation results" section of the terminal summary and written to the JSON report.

## Running Evaluation Tests

```console
uv run evaluate tests/ --until Amsterdam
uv run evaluate tests/ --fork Prague --eval-report results.json
```

`evaluate` accepts the fork selection options of `fill` (`--fork`, `--from`, `--until`), the transition tool options (`--evm-bin`, `--traces`, `--evm-dump-dir`) and pytest options such as `-n` and `-k`. `--eval-report` writes the outcome, fork, number of runs, recorded values and failure message of each test to a JSON file.
