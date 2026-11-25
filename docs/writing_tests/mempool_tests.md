# Mempool Tests (Draft)

Mempool tests check whether a client admits a single transaction to an empty transaction pool and broadcasts it. They produce [Mempool Test](../running_tests/test_formats/mempool_test.md) fixtures through the `mempool_test` filler.

## Where the tests live

Mempool tests live in `tests/mempool/`, apart from the consensus tests, and mirror their fork and EIP layout (for example `tests/mempool/bogota/eip8141_frame_transactions/`). The admission rules' limits look like protocol limits, so keeping the trees apart stops them from being read as consensus rules.

The framework enforces the split: tests under `tests/mempool/` can only use `mempool_test`, and `mempool_test` cannot be used anywhere else.

- Admission rule constants and rule IDs are defined in the mempool tree (the EIP directory's `spec.py`), never in a consensus `spec.py`. Rule IDs are unique within their rule set, so they name the transaction type and the check, for example `FRAME_TRANSACTION_VALIDATION_PREFIX_BANNED_OPCODE`.
- Mempool tests may import consensus test helpers. Consensus tests never import from `tests/mempool/`.

Run them with `fill tests/mempool/`.

## Writing a test

```python
@pytest.mark.parametrize(
    "storage_owner", ["sender", "callee"], ids=["sender", "callee"]
)
def test_sload_in_validation_prefix(
    mempool_test: MempoolTestFiller,
    pre: Alloc,
    storage_owner: str,
) -> None:
    """Refuse a validation prefix that reads storage outside the sender."""
    if storage_owner == "sender":
        sender = pre.deploy_contract(
            code=Op.POP(Op.SLOAD(0)) + APPROVE_ALL, balance=10**18
        )
    elif storage_owner == "callee":
        callee = pre.deploy_contract(code=Op.POP(Op.SLOAD(0)) + Op.STOP)
        sender = pre.deploy_contract(
            code=Op.POP(Op.CALL(gas=Op.GAS, address=callee)) + APPROVE_ALL,
            balance=10**18,
        )
    else:
        raise ValueError(f"unknown storage owner: {storage_owner}")

    mempool_test(
        pre=pre,
        tx=Transaction(sender=sender, nonce=1, frames=[Frame.verify()]),
        broadcast=storage_owner == "sender",
        rules=[MempoolRule.STORAGE_OUTSIDE_SENDER],
    )
```

`mempool_test` takes:

- `pre`: the state at the chain head.
- `tx`: the transaction under test. Set its `error` to the `TransactionException` the specification raises for it in the next block, if any.
- `env`: the next block's environment (optional). The framework derives the head from it.
- `broadcast`: whether the client must broadcast the transaction. A transaction with an `error` is never broadcast.
- `rules`: IDs of the admission rules the test exercises, from the EIP directory's `MempoolRule`. A valid transaction that is not broadcast must name the rules it breaks.
- `mempool_ruleset`: the versioned name of the admission rule set the expectation assumes. Optional: the `mempool_ruleset` fixture in `tests/mempool/conftest.py` provides it (`public-mempool-v1`). A tree for another rule set overrides the fixture in its own `conftest.py`. A test can also pass it, or parametrize `mempool_ruleset` to fill once per rule set; the test function then takes `mempool_ruleset` as an argument.

## What the fill checks

When filling, the framework runs the transaction against the specification for the next block, and fails the fill unless the result matches the expectation:

| Expectation | The specification must |
| --- | --- |
| `broadcast=True` | accept the transaction |
| `broadcast=False` with `tx.error` set | raise `tx.error` |
| `broadcast=False` without `tx.error` | accept the transaction |

A test therefore cannot mistake a consensus rule for a mempool rule. Whether the transaction actually breaks the rules it names is not checked: those fixtures have `author` as their `_info.mempool.expectationSource`.

## Expectations the specification cannot check

For a refusal by a mempool rule, the fill only proves that the transaction is valid. To keep the test from refusing the transaction for an unrelated reason:

- For every refused transaction, also test the same transaction without the rule violation, expecting it to be broadcast, like `sender` and `callee` above. A client that broadcasts the fixed transaction but refuses the original can only be refusing it for that rule. A client that refuses both points at a test bug.
- Break only the rule under test, and name it in `rules`. When the transaction cannot avoid breaking several rules, name all of them and say why in a comment.
