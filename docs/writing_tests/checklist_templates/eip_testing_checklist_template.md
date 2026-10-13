<!-- markdownlint-disable MD001 (MD001=heading-increment) -->
# EIP Execution Layer Testing Checklist Template

Depending on the changes introduced by an EIP, the following template is the minimum baseline to guarantee test coverage of the Execution Layer features. Copy it for each EIP and fill in the Status and Tests columns.

## General

#### Code coverage

| Description                                                                                                                                                                                               | Status | Tests |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ | ----- |
| Run produced tests against [EELS](https://github.com/ethereum/execution-specs) and verify that branch coverage of new added lines for the EIP is 100%, with only exceptions being unreachable code lines. |        |       |
| Run coverage on the test code itself (as a basic logic sanity check), i.e., `uv run fill --cov tests`.                                                                                                    |        |       |
| Document any lines missed in coverage reports and explain why they are acceptable (e.g., unreachable code, general infrastructure not related to the EIP).                                                |        |       |
| Optional - Run against a second client and verify sufficient code coverage over new code added for the EIP.                                                                                               |        |       |

#### Fuzzing

Fuzzing is recommended to be performed on EIPs that introduce new cryptography primitives.

See [holiman/goevmlab](https://github.com/holiman/goevmlab) for an example of a fuzzing framework for the EVM.

## New Opcode

The EIP introduces one or more new opcodes to the EVM.

### Test Vectors

#### Memory expansion

If the opcode execution can expand the memory size, either by writing to memory or reading from an offset that exceeds current memory, or interaction of both parameters (size of zero should never result in memory expansion, regardless of offset value).

| Description                                                      | Status | Tests |
| ---------------------------------------------------------------- | ------ | ----- |
| Zero bytes expansion with zero-offset.                           |        |       |
| Zero bytes expansion with 2\*\*256-1 offset.                     |        |       |
| Single byte expansion.                                           |        |       |
| 31 bytes expansion.                                              |        |       |
| 32 bytes expansion.                                              |        |       |
| 33 bytes expansion.                                              |        |       |
| 64 bytes expansion.                                              |        |       |
| `2**32-1` bytes expansion.                                       |        |       |
| 2\*\*32 bytes expansion.                                         |        |       |
| 2\*\*64-1 bytes expansion.                                       |        |       |
| 2\*\*64 bytes expansion.                                         |        |       |
| 2\*\*256-1 bytes expansion (Should always result in Out-of-gas). |        |       |

#### Stack

##### Stack Overflow

If the opcode pushes one or more items to the stack, and the opcode pushes more elements than it pops, verify that the opcode execution results in exceptional abort when pushing elements to the stack would result in the stack having more than 1024 elements.

| Description     | Status | Tests |
| --------------- | ------ | ----- |
| Stack Overflow. |        |       |

##### Stack Underflow

If the opcode pops one or more items to the stack, or it has a minimum stack height of one or more (e.g. `DUPN` requires a minimum amount of elements in the stack even when it does not pop any element from it), verify that the opcode execution results in exceptional abort then stack has 1 less item than the minimum stack height expected.

| Description      | Status | Tests |
| ---------------- | ------ | ----- |
| Stack Underflow. |        |       |

##### Stack Complex Operations

If opcode performs stack operations more complex than simple pop/push (e.g. the opcode has a data portion that specifies a variable to access a specific stack element), perform the following test combinations.

| Description                                              | Status | Tests |
| -------------------------------------------------------- | ------ | ----- |
| Operation on an empty stack (Potential stack-underflow). |        |       |
| Operation on a stack with an odd height.                 |        |       |
| Operation on a stack with an even height.                |        |       |

##### Stack Manipulation With Data Portion Variables

If the opcode contains variables in its data portion, for each variable `n` of the opcode that accesses the nth stack item, test `n` being.

| Description        | Status | Tests |
| ------------------ | ------ | ----- |
| Top stack item.    |        |       |
| Bottom stack item. |        |       |
| Middle stack item. |        |       |

#### Execution context

Evaluate opcode's behavior in different execution contexts.

##### `CALL`

Verify opcode operation in a subcall frame originated from a `CALL` opcode.

| Description | Status | Tests |
| ----------- | ------ | ----- |
| `CALL`.     |        |       |

##### `STATICCALL`

Verify opcode operation in a subcall frame originated from a `STATICCALL` opcode.

| Description                                                                                                                                                                                                                                                                              | Status | Tests |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ | ----- |
| `STATICCALL`.                                                                                                                                                                                                                                                                            |        |       |
| Verify exceptional abort if the opcode attempts to modify the code, storage or balance of an account.                                                                                                                                                                                    |        |       |
| If the opcode is completely banned from static contexts, verify that even when its inputs would not cause any account modification, the opcode still results in exceptional abort of the execution (e.g. `PAY` with zero value, or `SSTORE` to the value it already has in the storage). |        |       |
| Verify sub-calls using other opcodes (e.g. `CALL`, `DELEGATECALL`, etc) also results in the same exceptional abort behavior.                                                                                                                                                             |        |       |

##### `DELEGATECALL`

Verify opcode operation in a subcall frame originated from a `DELEGATECALL` opcode.

| Description                                                                                                                                                                   | Status | Tests |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ | ----- |
| `DELEGATECALL`.                                                                                                                                                               |        |       |
| If the opcode modifies the storage of the account currently executing it, verify that only the account that is delegating execution is the one that has its storage modified. |        |       |
| If the opcode modifies the balance of the account currently executing it, verify that only the account that is delegating execution is the one that has its balance modified. |        |       |
| If the opcode modifies the code of the account currently executing it, verify that only the account that is delegating execution is the one that has its code modified.       |        |       |

##### `CALLCODE`

Verify opcode operation in a subcall frame originated from a `CALLCODE` opcode.

| Description | Status | Tests |
| ----------- | ------ | ----- |
| `CALLCODE`. |        |       |

##### Initcode

Verify opcode behaves as expected when running during the initcode phase of contract creation.

| Description                                                                                  | Status | Tests |
| -------------------------------------------------------------------------------------------- | ------ | ----- |
| Initcode operation.                                                                          |        |       |
| Initcode of a contract creating transaction.                                                 |        |       |
| Initcode of a contract creating opcode (including itself if opcode creates a contract).      |        |       |
| Initcode re-entry: using the same initcode and same address (e.g. CREATE2->REVERT->CREATE2). |        |       |

##### Set-code Delegated Account

Verify opcode operations are applied to the set-code account and do not affect the address that is the target of the delegation.

| Description                 | Status | Tests |
| --------------------------- | ------ | ----- |
| Set-code delegated account. |        |       |

##### Transaction Context

If opcode changes behavior depending on particular transaction properties, test using multiple values for each property.

| Description                           | Status | Tests |
| ------------------------------------- | ------ | ----- |
| Transaction-context dependent opcode. |        |       |

##### Block Context

If opcode changes behavior depending on particular block properties, test using multiple values for each property.

| Description                     | Status | Tests |
| ------------------------------- | ------ | ----- |
| Block-context dependent opcode. |        |       |

#### Return data

Verify proper return data buffer overwriting if the opcode is meant to interact with it, otherwise verify that the return data buffer is unaffected.

| Description                            | Status | Tests |
| -------------------------------------- | ------ | ----- |
| Return buffer at current call context. |        |       |
| Return buffer at parent call context.  |        |       |

#### Gas Usage

##### Normal Operation

Verify gas usage affectation of each stack argument or memory input consumed by the opcode.

| Description                 | Status | Tests |
| --------------------------- | ------ | ----- |
| Normal operation gas usage. |        |       |

##### Memory Expansion

Verify that the memory expansion correctly follows the gas calculation.

| Description       | Status | Tests |
| ----------------- | ------ | ----- |
| Memory expansion. |        |       |

##### Extra Gas

Verify that attempting to execute the opcode when gas available is 1 more than the required gas results in exceptional abort.

| Description                             | Status | Tests |
| --------------------------------------- | ------ | ----- |
| extra gas should not fail the execution |        |       |

##### Out-Of-Gas

Verify that attempting to execute the opcode when gas available is 1 less than the required gas results in exceptional abort.

| Description                         | Status | Tests |
| ----------------------------------- | ------ | ----- |
| Out-of-gas due to opcode inputs.    |        |       |
| Out-of-gas due to memory expansion. |        |       |

##### Order-of-operations

If the opcode requires different gas stipends for other operations (e.g. contract creation, cold/warm account access), create one case for each operation (ideally independent of each other) and the listed cases for each.

| Description                                                        | Status | Tests |
| ------------------------------------------------------------------ | ------ | ----- |
| Success using the exact amount of gas required for the stipend.    |        |       |
| OOG with a 1-gas-difference from the gas required for the stipend. |        |       |

#### Terminating opcode

If an opcode is terminating, meaning it results in the current call context to end execution.

| Description                 | Status | Tests |
| --------------------------- | ------ | ----- |
| Top-level call termination. |        |       |
| Sub-level call termination. |        |       |
| Initcode termination.       |        |       |

#### Aborting/Reverting opcode

If the terminating opcode is meant to rollback the executing call frame, verify the listed events are properly rolled back.

| Description         | Status | Tests |
| ------------------- | ------ | ----- |
| Balance changes.    |        |       |
| Storage changes.    |        |       |
| Contract creations. |        |       |
| Nonce increments.   |        |       |
| Log events.         |        |       |

#### Out-of-bounds checks

If the opcode has out-of-bounds conditions in its parameters/inputs.

| Description                       | Status | Tests |
| --------------------------------- | ------ | ----- |
| Max value for each parameter.     |        |       |
| Max value + 1 for each parameter. |        |       |

#### Exceptional Abort

If the opcode has conditions, either inputs or execution context states, that should cause exceptional abort and are different than out-of-gas or stack overflow or underflow.

| Description                   | Status | Tests |
| ----------------------------- | ------ | ----- |
| Exceptional abort conditions. |        |       |

#### Data portion

If an opcode has a data portion, meaning the `N` bytes following the opcode in the contract bytecode are skipped from execution.

| Description                                                                      | Status | Tests |
| -------------------------------------------------------------------------------- | ------ | ----- |
| All zeros data portion.                                                          |        |       |
| Max value data portion (`2**N-1` where `N` is the bit size of the data portion). |        |       |
| Jump into the data portion.                                                      |        |       |

#### Contract creation

If the opcode execution results in the creation of a new contract in the state.

##### Correct Creation

Verify contract is created at the expected address given multiple inputs.

| Description          | Status | Tests |
| -------------------- | ------ | ----- |
| Address calculation. |        |       |

##### Creation Failure

The contract creation fails given the listed conditions.

| Description                                                                                       | Status | Tests |
| ------------------------------------------------------------------------------------------------- | ------ | ----- |
| Out-of-gas when available gas is less than minimum contract creation stipend.                     |        |       |
| Opcode has a value parameter and the caller does not have enough funds.                           |        |       |
| Creation would result in an address collision with an existing contract or EOA-delegated address. |        |       |

##### Recursive Contract Creation

Opcode is used to attempt to recreate a contract that is currently mid-creation by a previous call of the same opcode.

| Description                                   | Status | Tests |
| --------------------------------------------- | ------ | ----- |
| Recursive contract creation using the opcode. |        |       |

#### Fork transition

| Description                                                                                                                               | Status | Tests |
| ----------------------------------------------------------------------------------------------------------------------------------------- | ------ | ----- |
| Exceptional abort if executed before its activation fork/after its deactivation fork.                                                     |        |       |
| Verify correct opcode behavior at transition block, in the case of opcodes which behavior depends on current or parent block information. |        |       |

### Framework Changes

- Add opcode to `packages/testing/src/execution_testing/vm/opcode.py`
- Add opcode to relevant methods in the fork where the EIP is introduced in `packages/testing/src/execution_testing/forks/forks/forks.py`

## New Precompile

The EIP introduces one or more new precompiles.

### Test Vectors

#### Call contexts

Evaluate precompile behavior when called using different call opcodes or called from different execution contexts.

##### `CALL`

Verify precompile operation when called using the `CALL` opcode.

| Description | Status | Tests |
| ----------- | ------ | ----- |
| `CALL`.     |        |       |

##### `DELEGATECALL`

Verify precompile operation when called using the `DELEGATECALL` opcode.

| Description     | Status | Tests |
| --------------- | ------ | ----- |
| `DELEGATECALL`. |        |       |

##### `STATICCALL`

Verify precompile operation when called using the `STATICCALL` opcode.

If the precompile is stateful, meaning calling it affects its storage, this call must result in exceptional abort.

| Description   | Status | Tests |
| ------------- | ------ | ----- |
| `STATICCALL`. |        |       |

##### `CALLCODE`

Verify precompile operation when called using the `CALLCODE` opcode.

| Description | Status | Tests |
| ----------- | ------ | ----- |
| `CALLCODE`. |        |       |

##### Transaction Entry-point

Verify precompile behavior when it's used as `tx.to`.

| Description                            | Status | Tests |
| -------------------------------------- | ------ | ----- |
| Precompile as transaction entry-point. |        |       |

##### Initcode call

Verify calling the opcode during initcode execution of a new contract.

| Description                                                                        | Status | Tests |
| ---------------------------------------------------------------------------------- | ------ | ----- |
| Call from Initcode initiated from a CREATE/CREATE2 opcode.                         |        |       |
| Call from Initcode initiated from a contract-creating transaction (`tx.to==None`). |        |       |

##### Precompile as Set-code Delegated Address

Test setting the precompile as a set-code delegated address, and verify no precompile logic is executed.

| Description                 | Status | Tests |
| --------------------------- | ------ | ----- |
| Set code delegated address. |        |       |

#### Inputs

| Description                                                                                                                                                                                                          | Status | Tests |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ | ----- |
| Verify combinations of valid inputs to the precompile.                                                                                                                                                               |        |       |
| Verify all boundary values given the precompile functionality.                                                                                                                                                       |        |       |
| If precompile performs cryptographic operations, verify behavior on all inputs that have special cryptographic properties (e.g. infinity points as inputs, or input values that result in infinity points returned). |        |       |
| Verify all zeros input.                                                                                                                                                                                              |        |       |
| Verify 2^N-1 where N is a single or multiple valid bit-lengths.                                                                                                                                                      |        |       |
| Verify combinations of invalid inputs to the precompile.                                                                                                                                                             |        |       |
| Inputs that fail specific mathematical or cryptographic validity checks.                                                                                                                                             |        |       |
| Inputs that are malformed/corrupted.                                                                                                                                                                                 |        |       |

#### Value Transfer

##### Minimum Fee Precompile

If the precompile requires a minimum value (fee) to execute, either constant or depending on a formula.

| Description                                                      | Status | Tests |
| ---------------------------------------------------------------- | ------ | ----- |
| Calls with the required value amount minus one, expect failure.  |        |       |
| Calls with the exact required amount, expect success.            |        |       |
| Calls with extra value than the required amount, expect success. |        |       |

##### No-Fee Precompile

If the precompile does not require any minimum value (fee) to execute.

| Description                                                                                 | Status | Tests |
| ------------------------------------------------------------------------------------------- | ------ | ----- |
| Sending non-zero value does not cause an exception (unless otherwise specified by the EIP). |        |       |

#### Out-of-bounds checks

If the precompile has out-of-bounds conditions in its inputs.

| Description                   | Status | Tests |
| ----------------------------- | ------ | ----- |
| Max value for each input.     |        |       |
| Max value + 1 for each input. |        |       |

#### Input Lengths

Verify different combinations of input lengths to the precompile, ensuring the correct minimum fee (if any) is provided.

##### Zero-length Input

Regardless of the input requirements for the precompile.

| Description           | Status | Tests |
| --------------------- | ------ | ----- |
| Zero-length calldata. |        |       |

##### Static Required Input Length

If the precompile has a static required input length.

| Description                                                                                        | Status | Tests |
| -------------------------------------------------------------------------------------------------- | ------ | ----- |
| Correct static-length calldata.                                                                    |        |       |
| Calldata too short, where the value represents a correct but truncated input to the precompile.    |        |       |
| Calldata too long, where the value represents a correct input to the precompile with padded zeros. |        |       |

##### Dynamic Required Input Length

If the precompile has a variable required input-length based on a formula, test all listed scenarios given different input lengths.

| Description                                                                                        | Status | Tests |
| -------------------------------------------------------------------------------------------------- | ------ | ----- |
| Verify correct precompile execution for valid lengths.                                             |        |       |
| Calldata too short, where the value represents a correct but truncated input to the precompile.    |        |       |
| Calldata too long, where the value represents a correct input to the precompile with padded zeros. |        |       |

#### Gas usage

##### Constant Gas Cost

If the precompile always charges the same gas cost regardless of input conditions.

| Description                                                         | Status | Tests |
| ------------------------------------------------------------------- | ------ | ----- |
| Verify exact gas consumption.                                       |        |       |
| Verify exact gas consumption minus one results in out-of-gas error. |        |       |

##### Variable Gas Cost

If the precompile charges variable gas cost given input conditions, test all listed scenarios using multiple different valid inputs.

| Description                                                         | Status | Tests |
| ------------------------------------------------------------------- | ------ | ----- |
| Verify exact gas consumption.                                       |        |       |
| Verify exact gas consumption minus one results in out-of-gas error. |        |       |

##### Excessive Gas

Verify spending all block gas in calls to the precompile (Use `Environment().gas_limit` as reference max amount).

| Description          | Status | Tests |
| -------------------- | ------ | ----- |
| Excessive gas usage. |        |       |

#### Fork transition

##### Pre-fork Block Call

Verify that calling the precompile before its activation fork results in a valid call, even for inputs that are expected to be invalid for the precompile, or a zero-gas call.

| Description         | Status | Tests |
| ------------------- | ------ | ----- |
| Invalid input call. |        |       |
| Zero-gas call.      |        |       |

##### Cold/Warm Precompile Address State

Verify the cold/warm state of the precompile address depending on the fork activation.

| Description                                                       | Status | Tests |
| ----------------------------------------------------------------- | ------ | ----- |
| Precompile address is cold by default before the fork activation. |        |       |
| Precompile address is warm by default after the fork activation.  |        |       |

### Framework Changes

- Add precompile address to relevant methods in the fork where the EIP is introduced in `packages/testing/src/execution_testing/forks/forks/forks.py`

## Removed Precompile

The EIP removes one or more precompiles from the existing list of precompiles.

### Test Vectors

#### Fork transition

##### Precompile Operation

Verify that the precompile remains operational up until the last block before the fork is active, and behaves as an account with empty code afterwards.

| Description                              | Status | Tests |
| ---------------------------------------- | ------ | ----- |
| Precompile operation on fork activation. |        |       |

##### Cold/Warm Precompile Address State

Verify the cold/warm state of the precompile address depending on the fork activation.

| Description                                                       | Status | Tests |
| ----------------------------------------------------------------- | ------ | ----- |
| Precompile address is warm by default before the fork activation. |        |       |
| Precompile address is cold by default after the fork activation.  |        |       |

### Framework Changes

- Remove the precompile address from relevant methods in the fork where the EIP is removed in `packages/testing/src/execution_testing/forks/forks/forks.py`

## New System Contract

### Test Vectors

#### Call contexts

Evaluate precompile behavior when called using different call opcodes or called from different execution contexts.

##### `CALL`

Verify system contract operation when called using the `CALL` opcode.

| Description | Status | Tests |
| ----------- | ------ | ----- |
| `CALL`.     |        |       |

##### `DELEGATECALL`

Verify system contract operation when called using the `DELEGATECALL` opcode.

| Description     | Status | Tests |
| --------------- | ------ | ----- |
| `DELEGATECALL`. |        |       |

##### `STATICCALL`

Verify system contract operation when called using the `STATICCALL` opcode.

If the system contract is stateful, meaning calling it affects its storage, this call must result in exceptional abort.

| Description   | Status | Tests |
| ------------- | ------ | ----- |
| `STATICCALL`. |        |       |

##### `CALLCODE`

Verify system contract operation when called using the `CALLCODE` opcode.

| Description | Status | Tests |
| ----------- | ------ | ----- |
| `CALLCODE`. |        |       |

##### Transaction Entry-point

Verify system contract behavior when it's used as `tx.to`.

| Description                                 | Status | Tests |
| ------------------------------------------- | ------ | ----- |
| System Contract as transaction entry-point. |        |       |

##### Initcode call

Verify calling the opcode during initcode execution of a new contract.

| Description                                                                        | Status | Tests |
| ---------------------------------------------------------------------------------- | ------ | ----- |
| Call from Initcode initiated from a CREATE/CREATE2 opcode.                         |        |       |
| Call from Initcode initiated from a contract-creating transaction (`tx.to==None`). |        |       |

##### System Contract as Set-code Delegated Address

Test setting the system contract as a set-code delegated address, and verify no system contract side-effects are triggered, even if the actual system contract logic is executed.

If the system contract requires specific storage pre-conditions to be set for proper execution (e.g. if the contract contains a safety mechanism that prevents it from executing prior to the fork activation), ensure the delegated account has the proper values in the storage to guarantee the correct logic is executed.

| Description                 | Status | Tests |
| --------------------------- | ------ | ----- |
| Set code delegated address. |        |       |

#### Inputs

| Description                                                              | Status | Tests |
| ------------------------------------------------------------------------ | ------ | ----- |
| Verify combinations of valid inputs to the system contract.              |        |       |
| Verify all boundary values given the system contract functionality.      |        |       |
| Verify all zeros input.                                                  |        |       |
| Verify 2^N-1 where N is a single or multiple valid bit-lengths.          |        |       |
| Verify combinations of invalid inputs to the precompile.                 |        |       |
| Inputs that fail validity checks.                                        |        |       |
| Inputs that fail specific mathematical or cryptographic validity checks. |        |       |
| Inputs that are malformed/corrupted.                                     |        |       |

#### Value Transfer

##### Minimum Fee System Contract

If the system contract requires a minimum value (fee) to execute, either constant or depending on a formula.

| Description                                                      | Status | Tests |
| ---------------------------------------------------------------- | ------ | ----- |
| Calls with the required value amount minus one, expect failure.  |        |       |
| Calls with the exact required amount, expect success.            |        |       |
| Calls with extra value than the required amount, expect success. |        |       |

##### No-Fee System Contract

If the system contract does not require any minimum value (fee) to execute.

| Description                                                                                 | Status | Tests |
| ------------------------------------------------------------------------------------------- | ------ | ----- |
| Sending non-zero value does not cause an exception (unless otherwise specified by the EIP). |        |       |

#### Out-of-bounds checks

If the system contract has out-of-bounds conditions in its inputs.

| Description                   | Status | Tests |
| ----------------------------- | ------ | ----- |
| Max value for each input.     |        |       |
| Max value + 1 for each input. |        |       |

#### Input Lengths

Verify different combinations of input lengths to the system contract, ensuring the correct minimum fee (if any) is provided.

##### Zero-length Input

Regardless of the input requirements for the system contract.

| Description           | Status | Tests |
| --------------------- | ------ | ----- |
| Zero-length calldata. |        |       |

##### Static Required Input Length

If the system contract has a static required input length.

| Description                                                                                      | Status | Tests |
| ------------------------------------------------------------------------------------------------ | ------ | ----- |
| Correct static-length calldata.                                                                  |        |       |
| Calldata too short, where the value represents a correct but truncated input to the contract.    |        |       |
| Calldata too long, where the value represents a correct input to the contract with padded zeros. |        |       |

##### Dynamic Required Input Length

If the system contract has a variable required input-length based on a formula, test all listed scenarios given different input lengths.

| Description                                                                                      | Status | Tests |
| ------------------------------------------------------------------------------------------------ | ------ | ----- |
| Verify correct system contract execution for valid lengths.                                      |        |       |
| Calldata too short, where the value represents a correct but truncated input to the contract.    |        |       |
| Calldata too long, where the value represents a correct input to the contract with padded zeros. |        |       |

#### Gas usage

##### Constant Gas Cost

If the system contract always charges the same gas cost regardless of input conditions.

| Description                                                         | Status | Tests |
| ------------------------------------------------------------------- | ------ | ----- |
| Verify exact gas consumption.                                       |        |       |
| Verify exact gas consumption minus one results in out-of-gas error. |        |       |

##### Variable Gas Cost

If the system contract charges variable gas cost given input conditions, test all listed scenarios using multiple different valid inputs.

| Description                                                         | Status | Tests |
| ------------------------------------------------------------------- | ------ | ----- |
| Verify exact gas consumption.                                       |        |       |
| Verify exact gas consumption minus one results in out-of-gas error. |        |       |

#### Excessive Gas Cases

##### Excessive Gas Usage During Block Execution

Verify spending all block gas in calls to system contract (Use `Environment().gas_limit` as reference max amount).

| Description              | Status | Tests |
| ------------------------ | ------ | ----- |
| Exhaust block gas limit. |        |       |

##### Excessive Gas Usage During System Call

If possible, produce a scenario where, given all transactions executed within the block result in the execution of the contract by the system address would result in excessive gas usage.

| Description                   | Status | Tests |
| ----------------------------- | ------ | ----- |
| Excessive gas on system call. |        |       |

#### System Contract Deployment

| Description                                                                                                                                        | Status | Tests |
| -------------------------------------------------------------------------------------------------------------------------------------------------- | ------ | ----- |
| Verify block execution behavior after fork activation if the system contract has not been deployed (Depending on the EIP, block could be invalid). |        |       |
| Verify deployment transaction results in the system contract being deployed to the expected address.                                               |        |       |

#### Contract Variations

Verify execution of the different variations of the contract for different networks (if any) results in the expected behavior.

| Description                            | Status | Tests |
| -------------------------------------- | ------ | ----- |
| Different network contract variations. |        |       |

#### Contract Substitution

Substitute the default system contract with a mock contract to modify its behavior when called by the system address (at the end of the block execution).

| Description                                                                         | Status | Tests |
| ----------------------------------------------------------------------------------- | ------ | ----- |
| Modified return value lengths.                                                      |        |       |
| Modified to emit logs or modified logs.                                             |        |       |
| Modified to cause an exception (e.g. invalid opcode).                               |        |       |
| Modified to consume 30,000,000 million gas exactly, execution should be successful. |        |       |
| Modified to consume 30,000,001 million gas exactly, execution should fail.          |        |       |

#### Fork transition

Verify calling the system contract before its activation fork results in correct behavior (depends on the system contract implementation).

| Description                       | Status | Tests |
| --------------------------------- | ------ | ----- |
| Call system contract before fork. |        |       |

### Framework Changes

- Add system contract address to relevant methods in the fork where the EIP is introduced in `packages/testing/src/execution_testing/forks/forks/forks.py`
- Add system contract bytecode to the returned value of `pre_allocation_blockchain` in the fork where the EIP is introduced in `packages/testing/src/execution_testing/forks/forks/forks.py`

## New Transaction Type

### Test Vectors

#### Intrinsic Validity

Verify the transaction (and the block it is included in) is valid or invalid given the intrinsic validity of the new transaction type, depending on each test scenario.

For each new field that affects the intrinsic gas cost of the transaction verify all listed scenarios.

##### Gas Limit

Note: Data floor gas cost affects the intrinsic validity of all transaction types, so it must be taken into account when designing all test scenarios.

| Description                                                                        | Status | Tests |
| ---------------------------------------------------------------------------------- | ------ | ----- |
| Provide the exact intrinsic gas as `gas_limit` value to the transaction.           |        |       |
| Provide the exact intrinsic gas minus one as `gas_limit` value to the transaction. |        |       |

##### Gas Fee

| Description                                                    | Status | Tests |
| -------------------------------------------------------------- | ------ | ----- |
| Invalid if `tx.max_priority_fee_per_gas < tx.max_fee_per_gas`. |        |       |
| Valid if `tx.max_priority_fee_per_gas == tx.max_fee_per_gas`.  |        |       |
| Invalid if `tx.max_fee_per_gas < block.base_fee_per_gas`.      |        |       |
| Valid if `tx.max_fee_per_gas < block.base_fee_per_gas`.        |        |       |

##### Chain ID

| Description                                   | Status | Tests |
| --------------------------------------------- | ------ | ----- |
| Invalid if `tx.chain_id != network.chain_id`. |        |       |

##### Nonce

| Description                                | Status | Tests |
| ------------------------------------------ | ------ | ----- |
| Invalid if `tx.nonce == sender.nonce - 1`. |        |       |
| Invalid if `tx.nonce == sender.nonce + 1`. |        |       |
| Valid if `tx.nonce == sender.nonce`.       |        |       |

##### To

| Description                                             | Status | Tests |
| ------------------------------------------------------- | ------ | ----- |
| Valid/Invalid if `tx.to == None`, depending on the EIP. |        |       |

##### Value

| Description                                                                                  | Status | Tests |
| -------------------------------------------------------------------------------------------- | ------ | ----- |
| Invalid if `tx.value == 1` and `account.balance == (tx.max_fee_per_gas * tx.gas_price)`.     |        |       |
| Valid if `tx.value == 1` and `account.balance == (tx.max_fee_per_gas * tx.gas_price) + 1`.   |        |       |
| Invalid if `tx.value == 0` and `account.balance == (tx.max_fee_per_gas * tx.gas_price) - 1`. |        |       |
| Valid if `tx.value == 0` and `account.balance == (tx.max_fee_per_gas * tx.gas_price)`.       |        |       |

##### Data

| Description                                                                                                           | Status | Tests |
| --------------------------------------------------------------------------------------------------------------------- | ------ | ----- |
| Invalid if `data_floor_cost(len(tx.data)) > tx.intrinsic_gas_cost` and `tx.gas_limit == tx.intrinsic_gas_cost`.       |        |       |
| Valid if `data_floor_cost(len(tx.data)) > tx.intrinsic_gas_cost` and `tx.gas_limit == data_floor_cost(len(tx.data))`. |        |       |

#### Signature

Verify the transaction is correctly rejected if it contains an invalid signature.

| Description                                                                     | Status | Tests |
| ------------------------------------------------------------------------------- | ------ | ----- |
| V, R, S represent a value that is inside of the field but outside of the curve. |        |       |

##### V

| Description                                                            | Status | Tests |
| ---------------------------------------------------------------------- | ------ | ----- |
| `2`.                                                                   |        |       |
| `27` (Type-0 transaction valid value).                                 |        |       |
| `28` (Type-0 transaction valid value).                                 |        |       |
| `35` (Type-0 replay-protected transaction valid value for chain id 1). |        |       |
| `36` (Type-0 replay-protected transaction valid value for chain id 1). |        |       |
| `2**8-1`.                                                              |        |       |

##### R

| Description     | Status | Tests |
| --------------- | ------ | ----- |
| `0`.            |        |       |
| `SECP256K1N-1`. |        |       |
| `SECP256K1N`.   |        |       |
| `SECP256K1N+1`. |        |       |
| `2**256-1`.     |        |       |
| `2**256`.       |        |       |

##### S

| Description                            | Status | Tests |
| -------------------------------------- | ------ | ----- |
| `0`.                                   |        |       |
| `SECP256K1N//2-1`.                     |        |       |
| `SECP256K1N//2`.                       |        |       |
| `SECP256K1N//2+1`.                     |        |       |
| `SECP256K1N-1`.                        |        |       |
| `SECP256K1N`.                          |        |       |
| `SECP256K1N+1`.                        |        |       |
| `2**256-1`.                            |        |       |
| `2**256`.                              |        |       |
| `SECP256K1N - S` of a valid signature. |        |       |

#### Transaction Attributes Readable From EVM

| Description                                                                                                                     | Status | Tests |
| ------------------------------------------------------------------------------------------------------------------------------- | ------ | ----- |
| Verify attributes that can be read in the EVM from transaction fields.                                                          |        |       |
| Verify attributes specific to the new transaction type that can be read in the EVM behave correctly on older transaction types. |        |       |

#### Transaction-Scoped Persistent Values

Verify values or variables that are persistent through the execution of the transaction (e.g. transient storage, warm/cold accounts).

| Description                                         | Status | Tests |
| --------------------------------------------------- | ------ | ----- |
| Persist throughout the entire transaction.          |        |       |
| Reset on subsequent transactions in the same block. |        |       |

#### Encoding (RLP, SSZ)

Verify correct transaction rejection in all listed scenarios.

##### Field Sizes

Verify all listed scenarios for each transaction field.

| Description                                       | Status | Tests |
| ------------------------------------------------- | ------ | ----- |
| Add leading zero byte.                            |        |       |
| Remove single byte from fixed-byte-length fields. |        |       |

##### Fields of List Type

Verify for each transaction field that is of type list.

| Description                                   | Status | Tests |
| --------------------------------------------- | ------ | ----- |
| Zero-element list (Failure depending on EIP). |        |       |
| Max count list.                               |        |       |
| Max count plus one list.                      |        |       |

##### Extra/Missing Fields

| Description                                                     | Status | Tests |
| --------------------------------------------------------------- | ------ | ----- |
| Any fields particular to the new transaction types are missing. |        |       |
| Transaction contains extra fields.                              |        |       |

##### Serialization Corruption

| Description                                       | Status | Tests |
| ------------------------------------------------- | ------ | ----- |
| Serialized bytes object is truncated by one byte. |        |       |
| Serialized bytes object has one extra byte.       |        |       |

##### Serializable Fields

Verify for each serializable field, all previous tests plus following listed scenario.

| Description                                                                                                  | Status | Tests |
| ------------------------------------------------------------------------------------------------------------ | ------ | ----- |
| Serializable field is encoded as bytes instead of using the correct encoding (e.g. list in the case of RLP). |        |       |

#### Out-of-bounds checks

Verify if the transaction has out-of-bounds conditions in its fields and verify.

| Description                   | Status | Tests |
| ----------------------------- | ------ | ----- |
| Max value for each field.     |        |       |
| Max value + 1 for each field. |        |       |

#### Contract creation

Verify that the transaction can create new contracts if the transaction type supports it.

| Description                                  | Status | Tests |
| -------------------------------------------- | ------ | ----- |
| Create contracts using new transaction type. |        |       |

#### Sender account modifications

| Description                                                                                                                                                                                               | Status | Tests |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ | ----- |
| Sender account has its nonce incremented at least by one after the transaction is included in a block (or more if the transaction type introduces a new mechanism that bumps the nonce by more than one). |        |       |
| Sender account has its balance reduced by the correct amount (gas consumed and value) at the start of execution (e.g. using `BALANCE`).                                                                   |        |       |

#### Block Level Interactions

##### Single Transaction In Block

Verify a block where the new transaction type is the sole transaction contained in the block.

| Description                                       | Status | Tests |
| ------------------------------------------------- | ------ | ----- |
| Invalid if `tx.gas_limit == block.gas_limit + 1`. |        |       |
| Valid if `tx.gas_limit == block.gas_limit`.       |        |       |

##### Two Transactions In Block

Verify a block where the new transaction type is the last transaction contained in a block with two transactions.

| Description                                                                                                                         | Status | Tests |
| ----------------------------------------------------------------------------------------------------------------------------------- | ------ | ----- |
| Valid if `block.txs[0].gas_used + block.txs[1].gas_limit == block.gas_limit`.                                                       |        |       |
| Invalid if `(block.txs[0].gas_used + block.txs[1].gas_limit == block.gas_limit + 1) and (block.txs[0].gas_used < block.gas_limit)`. |        |       |

##### EIP-7825

Verify a transaction of the new type is rejected if its gas limit exceeds the [EIP-7825](https://eips.ethereum.org/EIPS/eip-7825) gas limit for the current fork.

| Description                                  | Status | Tests |
| -------------------------------------------- | ------ | ----- |
| Exceeds EIP-7825 gas limit by one.           |        |       |
| Gas limit is exactly the EIP-7825 gas limit. |        |       |

##### Mixed transactions

Verify a block with all transactions types including the new type is executed correctly.

| Description         | Status | Tests |
| ------------------- | ------ | ----- |
| Mixed transactions. |        |       |

#### Fork transition

Verify that a block prior to fork activation where the new transaction type is introduced and containing the new transaction type is invalid.

| Description                                                 | Status | Tests |
| ----------------------------------------------------------- | ------ | ----- |
| New transaction type included before fork activation block. |        |       |

#### RPC Tests

- \*Verify `eth_estimateGas` behavior for different valid combinations of the new transaction type.
- Verify `eth_sendRawTransaction` using `execute`.

\*Tests must be added to [`execution-apis`](https://github.com/ethereum/execution-apis) repository.

### Framework Changes

- Modify `transaction_intrinsic_cost_calculator` in the fork where the EIP is introduced in `packages/testing/src/execution_testing/forks/forks/forks.py`, adding the appropriate new fields that the transaction introduced and the logic to the intrinsic gas cost calculation, if any.
- Add the transaction type number to `tx_types` response in the fork where the EIP is introduced in `packages/testing/src/execution_testing/forks/forks/forks.py` (If applicable add also to `contract_creating_tx_types`).

## New Block Header Field

### Test Vectors

#### Genesis value

Verify, if possible, that the value can be set at genesis if the network starting fork is the activation fork, and that clients can consume such genesis.

| Description                        | Status | Tests |
| ---------------------------------- | ------ | ----- |
| New block header field at genesis. |        |       |

#### Value behavior

Verify, given multiple initial values, that a block is accepted or rejected depending on the correct expected value for the current block.

| Description                                                                                                                                                                                      | Status | Tests |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------ | ----- |
| Block is accepted if the value is the correct expected for the current block, depending on the circumstances that affect the value as defined in the EIP.                                        |        |       |
| Block is rejected if the value is modified (using `block.rlp_modifier`) to an incorrect value for the current block, depending on the circumstances that affect the value as defined in the EIP. |        |       |

#### Fork transition

| Description                                                                                       | Status | Tests |
| ------------------------------------------------------------------------------------------------- | ------ | ----- |
| Verify initial value of the field at the first block of the activation fork.                      |        |       |
| Verify that a block containing the new header field before the activation of the fork is invalid. |        |       |
| Verify that a block lacking the new header field at the activation of the fork is invalid.        |        |       |

### Framework Changes

- Add the new header field to the relevant objects:
    - `execution_testing.fixtures.FixtureHeader`.
    - `execution_testing.fixtures.FixtureExecutionPayload`.
    - `execution_testing.specs.Header`.
- Add the appropriate `header_*_required` fork method to `BaseFork` in `execution_testing.forks`.

## New Block Body Field

### Test Vectors

#### Value behavior

Verify, given multiple initial values, that a block is accepted or rejected depending on the correct expected value for the current block.

| Description                                                                                                                                                                                     | Status | Tests |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ | ----- |
| Block is accepted if the value is the correct expected for the current block, depending on the circumstances that affect the value as defined in the EIP.                                       |        |       |
| Block is rejected if the value is modified (using appropriate `block`) to an incorrect value for the current block, depending on the circumstances that affect the value as defined in the EIP. |        |       |

#### Fork transition

| Description                                                                                           | Status | Tests |
| ----------------------------------------------------------------------------------------------------- | ------ | ----- |
| Verify that a block containing the new block body field before the activation of the fork is invalid. |        |       |
| Verify that a block lacking the new block field at the activation of the fork is invalid.             |        |       |

### Framework Changes

- Add the new body field to the relevant objects.
    - `execution_testing.fixtures.FixtureBlockBase`.
    - `execution_testing.fixtures.FixtureEngineNewPayload`.
    - `execution_testing.specs.Block`.
- Modify `execution_testing.specs.BlockchainTest` filling behavior to account for the new block field.

## Gas Cost Changes

### Test Vectors

#### Gas Usage

Measure and store the gas usage during the operations affected by the gas cost changes and verify the updated behavior.

| Description                | Status | Tests |
| -------------------------- | ------ | ----- |
| Measure updated gas costs. |        |       |

#### Out-of-gas

Verify the operations affected by the gas cost changes can run out-of-gas with the updated limits.

| Description                     | Status | Tests |
| ------------------------------- | ------ | ----- |
| Out-Of-Gas with new gas prices. |        |       |

#### Fork transition

Verify gas costs are updated at the fork transition boundary.

| Description                                           | Status | Tests |
| ----------------------------------------------------- | ------ | ----- |
| Costs unaffected before the fork activation block.    |        |       |
| Costs are updated on and after fork activation block. |        |       |

### Framework Changes

- Modify `transaction_intrinsic_cost_calculator` in the fork where the EIP is introduced in `packages/testing/src/execution_testing/forks/forks/forks.py` if the EIP affects intrinsic gas cost calculation.
- Modify `transaction_data_floor_cost_calculator` in the fork where the EIP is introduced in `packages/testing/src/execution_testing/forks/forks/forks.py` if the EIP affects calldata floor cost.
- Modify `memory_expansion_gas_calculator` in the fork where the EIP is introduced in `packages/testing/src/execution_testing/forks/forks/forks.py` if the EIP affects memory expansion gas cost calculation.
- Modify `gas_costs` in the fork where the EIP is introduced in `packages/testing/src/execution_testing/forks/forks/forks.py` if the EIP affects specific opcode gas costs.

## Gas Refunds Changes

### Test Vectors

#### Refund calculation

Verify that the refund does not exceed `gas_used // MAX_REFUND_QUOTIENT` (`MAX_REFUND_QUOTIENT==5` in [EIP-3529](https://eips.ethereum.org/EIPS/eip-3529)) in the following scenarios.

| Description                                      | Status | Tests |
| ------------------------------------------------ | ------ | ----- |
| `refund == gas_used // MAX_REFUND_QUOTIENT + 1`. |        |       |
| `refund == gas_used // MAX_REFUND_QUOTIENT`.     |        |       |
| `refund == gas_used // MAX_REFUND_QUOTIENT - 1`. |        |       |

#### Exceptional Abort

| Description                                                                                                                                                                                                             | Status | Tests |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ | ----- |
| If the operation causing the refund can be reverted, verify the refund is not applied if the following cases:.                                                                                                          |        |       |
| `REVERT`.                                                                                                                                                                                                               |        |       |
| Out-of-gas.                                                                                                                                                                                                             |        |       |
| Invalid opcode.                                                                                                                                                                                                         |        |       |
| `REVERT` of an upper call frame.                                                                                                                                                                                        |        |       |
| If the operation causing the refund cannot be reverted (e.g. in the case of a transaction-scoped operation such as authorization refunds in EIP-7702), verify the refund is still applied even in the following cases:. |        |       |
| `REVERT` at the top call frame.                                                                                                                                                                                         |        |       |
| Out-of-gas at the top call frame.                                                                                                                                                                                       |        |       |
| Invalid opcode at the top call frame.                                                                                                                                                                                   |        |       |

#### Cross-Functional Test

Verify the following tests are updated to support the new type of refunds.

| Description                                                    | Status | Tests |
| -------------------------------------------------------------- | ------ | ----- |
| `tests/prague/eip7623_increase_calldata_cost/test_refunds.py`. |        |       |

### Framework Changes

N/A

## Blob Count Changes

### Test Vectors

#### Existing Test Updates

Verify tests in `tests/cancun/eip4844_blobs` were correctly and automatically updated to take into account the new blob count values at the new fork activation block.

| Description                                                     | Status | Tests |
| --------------------------------------------------------------- | ------ | ----- |
| Updates to `tests/cancun/eip4844_blobs` were applied correctly. |        |       |

### Framework Changes

- Modify `blob_base_fee_update_fraction`, `target_blobs_per_block`, `max_blobs_per_block` in the fork where the EIP is introduced in `packages/testing/src/execution_testing/forks/forks/forks.py` if the EIP affects any of the values returned by each function.

## New Execution Layer Request

### Test Vectors

#### Cross-Request-Type Interaction

| Description                                                                                                                | Status | Tests |
| -------------------------------------------------------------------------------------------------------------------------- | ------ | ----- |
| Update `tests/prague/eip7685_general_purpose_el_requests` tests to include the new request type in the tests combinations. |        |       |

### Framework Changes

- Increment `max_request_type` in the fork where the EIP is introduced in `packages/testing/src/execution_testing/forks/forks/forks.py` to the new maximum request type number after the EIP is activated.

## New Transaction-Validity Constraint

### Test Vectors

#### Fork transition

| Description                                                                                            | Status | Tests |
| ------------------------------------------------------------------------------------------------------ | ------ | ----- |
| Verify that a block before the activation fork is accepted even when the new constraint is not met.    |        |       |
| Verify that a block after the activation fork is accepted when the new validity constraint is met.     |        |       |
| Verify that a block after the activation fork is rejected when the new validity constraint is not met. |        |       |

Note: All test cases must use off-by-one values to ensure proper boundary condition verification.

### Framework Changes

- Introduce the validity constraint as a fork method that returns:
    - `None` for forks before its activation.
    - A non-`None` value starting from the fork where the constraint becomes active.

## Modified Transaction-Validity Constraint

### Test Vectors

#### Fork transition

| Description                                                                                                                                 | Status | Tests |
| ------------------------------------------------------------------------------------------------------------------------------------------- | ------ | ----- |
| Verify that a block before the activation fork is accepted when the existing constraint is met and, ideally, the new constraint is not met. |        |       |
| Verify that a block before the activation fork is rejected when the existing constraint is not met and, ideally, the new constraint is met. |        |       |
| Verify that a block after the activation fork is accepted when the new validity constraint is met.                                          |        |       |
| Verify that a block after the activation fork is rejected when the new validity constraint is not met.                                      |        |       |

Note: All test cases must use off-by-one values to ensure proper boundary condition verification.

### Framework Changes

- Update the validity constraint as a fork method that returns the updated value starting from the fork where the constraint changes.

## Block-Level Validation Constraint

The EIP introduces a new constraint that applies at the block level (e.g., block RLP size limits, block validation rules).

### Test Vectors

#### Boundary Conditions

Verify block acceptance/rejection at constraint boundaries using off-by-one values.

| Description                                                                                 | Status | Tests |
| ------------------------------------------------------------------------------------------- | ------ | ----- |
| Verify that a block with constraint value at limit minus one is accepted (expect success).  |        |       |
| Verify that a block with constraint value exactly at limit is accepted (expect success).    |        |       |
| Verify that a block with constraint value at limit plus one is rejected (expect exception). |        |       |

#### Content Variations

Verify the constraint behaves correctly with different block contents that may affect the constraint calculation.

| Description                                                                   | Status | Tests |
| ----------------------------------------------------------------------------- | ------ | ----- |
| Verify constraint behavior with all supported transaction types in the block. |        |       |
| Verify constraint behavior when transactions emit logs.                       |        |       |
| Verify constraint behavior with varying receipt sizes.                        |        |       |
| Verify constraint behavior with non-empty withdrawals list.                   |        |       |

#### Fork Transition

| Description                                                                                         | Status | Tests |
| --------------------------------------------------------------------------------------------------- | ------ | ----- |
| Verify that a block before the activation fork is accepted even when the new constraint is not met. |        |       |
| Verify that a block after the activation fork is accepted when the new constraint is met.           |        |       |
| Verify that a block after the activation fork is rejected when the new constraint is not met.       |        |       |

Note: All test cases must use off-by-one values to ensure proper boundary condition verification.

### Framework Changes

- Introduce the constraint as a fork method that returns:
    - `None` for forks before its activation.
    - A non-`None` value starting from the fork where the constraint becomes active.
