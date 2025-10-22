# Types of tests

There are currently three types of tests that can be produced by a test spec:

1. State Tests
2. Blockchain Tests
3. Transaction Tests

## State Tests

### Purpose

Tests the effects of individual transactions (ideally a single one) that span a single block in a controlled environment.

### Use cases

- Test a single opcode behavior.
- Verify opcode gas costs.
- Test interactions between multiple smart contracts.
- Test creation of smart contracts.

!!! info

    The fill function will automatically generate a `blockchain_test` fixture from `state_tests`, consisting of one block and one transaction.

## Blockchain Tests

### Purpose

Blockchain tests span multiple blocks which may or may not contain transactions and mainly focus on the block to block effects to the Ethereum state.

### Use cases

- Verify system-level operations such as coinbase balance updates or withdrawals.
- Verify fork transitions.
- Verify blocks with invalid transactions/properties are rejected.

### Fork Transition Tests

There is a special type of blockchain test that is used to test a fork transition. It's not executed for all possible forks, rather it targets exactly the blocks at the point of transition from one evm implementation to the next. This type of test must be marked with the `valid_at_transition_to` marker, for example:

```python
@pytest.mark.valid_at_transition_to("Cancun")
def test_blob_type_tx_pre_fork(
    blockchain_test: BlockchainTestFiller,
    pre: Dict,
    env: Environment,
    blocks: List[Block],
):
    """
    Reject blocks with blobs before blobs fork
    """
```

## Transaction Tests

### Purpose

Test correct transaction rejection/acceptance of a serialized transaction (currently RLP only).

### Use cases

- Verify that a badly formatted transaction is correctly rejected by the client.
- Verify that a transaction with an invalid value in one of its fields is correctly rejected by the client.

!!! info

    Using the `execute` command, transaction tests can be sent to clients in a live network using the `eth_sendRawTransaction` endpoint.

## Deciding on a test type

### Prefer `state_test` for single transactions

Whenever possible, use `state_test` to examine individual transactions. This method is more straightforward and less prone to external influences that can occur during block building.

This provides more targeted testing since it does not invoke the client's block-building machinery. This reduces the risk of encountering false positives, particularly in exception scenarios (e.g., see issue [#343: "Zero max_fee_per_blob_gas test is ineffective"](https://github.com/ethereum/execution-spec-tests/issues/343)).

Moreover, the `fill` command automatically additionally generates a `blockchain_test` for every `state_test` by wrapping the `state_test`'s transaction in a block.
