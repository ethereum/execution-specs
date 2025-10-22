# Transaction Metadata in Execute Mode

The `execute` plugin automatically adds metadata to all transactions it sends to the network. This feature was introduced to improve debugging, monitoring, and transaction tracking capabilities.

## Overview

Transaction metadata provides context about each transaction sent during test execution, making it easier to:

- Debug test failures by correlating blockchain transactions with test operations
- Monitor test execution patterns and performance
- Track transaction flow across different phases of test execution
- Identify which transactions belong to which tests and phases

## Metadata Structure

Each transaction includes a `TransactionTestMetadata` object with the following fields:

| Field | Type | Description |
|-------|------|-------------|
| `testId` | `str` | The unique identifier of the test being executed (pytest node ID) |
| `phase` | `str` | The execution phase: `setup`, `testing`, or `cleanup` |
| `action` | `str` | The specific action being performed (e.g., `deploy_contract`, `fund_eoa`) |
| `target` | `str` | The label of the account or contract being targeted |
| `txIndex` | `int` | The index of the transaction within its phase |

## Transaction Phases

### Setup Phase (`setup`)

Transactions that prepare the test environment:

- **`deploy_contract`**: Contract deployment transactions
- **`fund_eoa`**: Funding EOAs with initial balances
- **`eoa_storage_set`**: Setting storage values for EOAs
- **`fund_address`**: Funding specific addresses

### Testing Phase (`testing`)

The actual test transactions defined by the test:

- User-defined test transactions
- Blob testing transactions

### Cleanup Phase (`cleanup`)

Transactions that clean up after the test:

- **`refund_from_eoa`**: Refunding EOAs back to the sender account

## Example Metadata

```json
{
  "testId": "tests/example_test.py::test_example",
  "phase": "setup",
  "action": "deploy_contract",
  "target": "contract_label",
  "txIndex": 0
}
```

## Debugging Test Failures

When a test fails on a remote network, you can use the transaction metadata to:

1. Identify which transactions belong to the failing test
2. Determine which phase of execution failed
3. Correlate blockchain transactions with specific test operations

The ID will normally be printed in the client logs when execute is running tests against the client, but the logging level might need to be increased for some of the clients (`--sim.loglevel` when running with hive).

## Technical Notes

- Metadata is automatically handled by the execute plugin
- No additional configuration is required
- Metadata is embedded in RPC requests without affecting transaction execution
- The feature is backward compatible and doesn't change test behavior
