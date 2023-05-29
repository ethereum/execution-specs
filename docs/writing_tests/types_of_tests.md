# Types of tests

There are currently two types of tests that can be produced by a test spec:

- State Tests
- Blockchain Tests

The State tests span a single block and, ideally, a single transaction.

Examples of State tests:

- Test a single opcode behavior
- Verify opcode gas costs
- Test interactions between multiple smart contracts
- Test creation of smart contracts

The Blockchain tests span multiple blocks which may or may not contain transactions and mainly focus on the block to block effects to the Ethereum state.

- Verify system-level operations such as coinbase balance updates or withdrawals
- Verify fork transitions
- Verify blocks with invalid transactions/properties are rejected