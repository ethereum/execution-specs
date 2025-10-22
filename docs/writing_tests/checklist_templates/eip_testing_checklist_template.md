<!-- markdownlint-disable MD001 (MD001=heading-increment) -->
# EIP Execution Layer Testing Checklist Template

Depending on the changes introduced by an EIP, the following template is the minimum baseline to guarantee test coverage of the Execution Layer features.

## Checklist Progress Tracker

| Total Checklist Items | Covered Checklist Items | Percentage |
| --------------------- | ----------------------- | ---------- |
| TOTAL_CHECKLIST_ITEMS | COVERED_CHECKLIST_ITEMS | PERCENTAGE |

<!-- WARNINGS LINE -->

## General

#### Code coverage

| ID                                    | Description                                                                                                                                                                                                  | Status | Tests |
| ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------ | ----- |
| `general/code_coverage/eels`          | Run produced tests against [EELS](https://github.com/ethereum/execution-specs) and verify that line code coverage of new added lines for the EIP is 100%, with only exceptions being unreachable code lines. |        |       |
| `general/code_coverage/test_coverage` | Run coverage on the test code itself (as a basic logic sanity check), i.e., `uv run fill --cov tests`.                                                                                                       |        |       |
| `general/code_coverage/second_client` | Optional - Run against a second client and verify sufficient code coverage over new code added for the EIP.                                                                                                  |        |       |

#### Fuzzing

Fuzzing is recommended to be performed on EIPs that introduce new cryptography primitives.

See [holiman/goevmlab](https://github.com/holiman/goevmlab) for an example of a fuzzing framework for the EVM.

## New Opcode

The EIP introduces one or more new opcodes to the EVM.

### Test Vectors

#### Memory expansion

If the opcode execution can expand the memory size, either by writing to memory or reading from an offset that exceeds current memory, or interaction of both parameters (size of zero should never result in memory expansion, regardless of offset value).

| ID                                               | Description                                                      | Status | Tests |
| ------------------------------------------------ | ---------------------------------------------------------------- | ------ | ----- |
| `opcode/test/mem_exp/zero_bytes_zero_offset` | Zero bytes expansion with zero-offset.                           |        |       |
| `opcode/test/mem_exp/zero_bytes_max_offset`  | Zero bytes expansion with 2\*\*256-1 offset.                     |        |       |
| `opcode/test/mem_exp/single_byte`            | Single byte expansion.                                           |        |       |
| `opcode/test/mem_exp/31_bytes`               | 31 bytes expansion.                                              |        |       |
| `opcode/test/mem_exp/32_bytes`               | 32 bytes expansion.                                              |        |       |
| `opcode/test/mem_exp/33_bytes`               | 33 bytes expansion.                                              |        |       |
| `opcode/test/mem_exp/64_bytes`               | 64 bytes expansion.                                              |        |       |
| `opcode/test/mem_exp/2_32_minus_one_bytes`   | `2**32-1` bytes expansion.                                       |        |       |
| `opcode/test/mem_exp/2_32_bytes`             | 2\*\*32 bytes expansion.                                         |        |       |
| `opcode/test/mem_exp/2_64_minus_one_bytes`   | 2\*\*64-1 bytes expansion.                                       |        |       |
| `opcode/test/mem_exp/2_64_bytes`             | 2\*\*64 bytes expansion.                                         |        |       |
| `opcode/test/mem_exp/2_256_minus_one_bytes`  | 2\*\*256-1 bytes expansion (Should always result in Out-of-gas). |        |       |

#### Stack

##### Stack Overflow

If the opcode pushes one or more items to the stack, and the opcode pushes more elements than it pops, verify that the opcode execution results in exceptional abort when pushing elements to the stack would result in the stack having more than 1024 elements.

| ID                               | Description     | Status | Tests |
| -------------------------------- | --------------- | ------ | ----- |
| `opcode/test/stack_overflow` | Stack Overflow. |        |       |

##### Stack Underflow

If the opcode pops one or more items to the stack, or it has a minimum stack height of one or more (e.g. `DUPN` requires a minimum amount of elements in the stack even when it does not pop any element from it), verify that the opcode execution results in exceptional abort then stack has 1 less item than the minimum stack height expected.

| ID                                | Description      | Status | Tests |
| --------------------------------- | ---------------- | ------ | ----- |
| `opcode/test/stack_underflow` | Stack Underflow. |        |       |

##### Stack Complex Operations

If opcode performs stack operations more complex than simple pop/push (e.g. the opcode has a data portion that specifies a variable to access a specific stack element), perform the following test combinations.

| ID                                                            | Description                                              | Status | Tests |
| ------------------------------------------------------------- | -------------------------------------------------------- | ------ | ----- |
| `opcode/test/stack_complex_operations/stack_heights/zero` | Operation on an empty stack (Potential stack-underflow). |        |       |
| `opcode/test/stack_complex_operations/stack_heights/odd`  | Operation on a stack with an odd height.                 |        |       |
| `opcode/test/stack_complex_operations/stack_heights/even` | Operation on a stack with an even height.                |        |       |

##### Stack Manipulation With Data Portion Variables

If the opcode contains variables in its data portion, for each variable `n` of the opcode that accesses the nth stack item, test `n` being.

| ID                                                           | Description        | Status | Tests |
| ------------------------------------------------------------ | ------------------ | ------ | ----- |
| `opcode/test/stack_complex_operations/data_portion_variables/top`    | Top stack item.    |        |       |
| `opcode/test/stack_complex_operations/data_portion_variables/bottom` | Bottom stack item. |        |       |
| `opcode/test/stack_complex_operations/data_portion_variables/middle` | Middle stack item. |        |       |

#### Execution context

Evaluate opcode's behavior in different execution contexts.

##### `CALL`

Verify opcode operation in a subcall frame originated from a `CALL` opcode.

| ID                                       | Description | Status | Tests |
| ---------------------------------------- | ----------- | ------ | ----- |
| `opcode/test/execution_context/call` | `CALL`.     |        |       |

##### `STATICCALL`

Verify opcode operation in a subcall frame originated from a `STATICCALL` opcode.

| ID                                                                 | Description                                                                                                                                                                                                                                                                                | Status | Tests |
| ------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------ | ----- |
| `opcode/test/execution_context/staticcall` | `STATICCALL`.     |        |       |
| `opcode/test/execution_context/staticcall/ban_check`           | Verify exceptional abort if the opcode attempts to modify the code, storage or balance of an account.                                                                                                                                                                                      |        |       |
| `opcode/test/execution_context/staticcall/ban_no_modification` | If the opcode is completely banned from static contexts, verify that even when its inputs would not cause any account modification, the opcode still results in exceptional abort of the execution (e.g. `PAY` with zero value, or `SSTORE` to the value it already has in the storage). |        |       |
| `opcode/test/execution_context/staticcall/sub_calls`           | Verify sub-calls using other opcodes (e.g. `CALL`, `DELEGATECALL`, etc) also results in the same exceptional abort behavior.                                                                                                                                                               |        |       |

##### `DELEGATECALL`

Verify opcode operation in a subcall frame originated from a `DELEGATECALL` opcode.

| ID                                                       | Description                                                                                                                                                                   | Status | Tests |
| -------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ | ----- |
| `opcode/test/execution_context/delegatecall`         | `DELEGATECALL`.                                                                                                                                                               |        |       |
| `opcode/test/execution_context/delegatecall/storage` | If the opcode modifies the storage of the account currently executing it, verify that only the account that is delegating execution is the one that has its storage modified. |        |       |
| `opcode/test/execution_context/delegatecall/balance` | If the opcode modifies the balance of the account currently executing it, verify that only the account that is delegating execution is the one that has its balance modified. |        |       |
| `opcode/test/execution_context/delegatecall/code`    | If the opcode modifies the code of the account currently executing it, verify that only the account that is delegating execution is the one that has its code modified.       |        |       |

##### `CALLCODE`

Verify opcode operation in a subcall frame originated from a `CALLCODE` opcode.

| ID                                           | Description | Status | Tests |
| -------------------------------------------- | ----------- | ------ | ----- |
| `opcode/test/execution_context/callcode` | `CALLCODE`. |        |       |

##### Initcode

Verify opcode behaves as expected when running during the initcode phase of contract creation.

| ID                                                           | Description                                                                                  | Status | Tests |
| ------------------------------------------------------------ | -------------------------------------------------------------------------------------------- | ------ | ----- |
| `opcode/test/execution_context/initcode/behavior`        | Initcode operation.                                                                          |        |       |
| `opcode/test/execution_context/initcode/behavior/tx`     | Initcode of a contract creating transaction.                                                 |        |       |
| `opcode/test/execution_context/initcode/behavior/opcode` | Initcode of a contract creating opcode (including itself if opcode creates a contract).      |        |       |
| `opcode/test/execution_context/initcode/reentry`         | Initcode re-entry: using the same initcode and same address (e.g. CREATE2->REVERT->CREATE2). |        |       |

##### Set-code Delegated Account

Verify opcode operations are applied to the set-code account and do not affect the address that is the target of the delegation.

| ID                                           | Description                 | Status | Tests |
| -------------------------------------------- | --------------------------- | ------ | ----- |
| `opcode/test/execution_context/set_code` | Set-code delegated account. |        |       |

##### Transaction Context

If opcode changes behavior depending on particular transaction properties, test using multiple values for each property.

| ID                                             | Description                           | Status | Tests |
| ---------------------------------------------- | ------------------------------------- | ------ | ----- |
| `opcode/test/execution_context/tx_context` | Transaction-context dependent opcode. |        |       |

##### Block Context

If opcode changes behavior depending on particular block properties, test using multiple values for each property.

| ID                                                | Description                     | Status | Tests |
| ------------------------------------------------- | ------------------------------- | ------ | ----- |
| `opcode/test/execution_context/block_context` | Block-context dependent opcode. |        |       |

#### Return data

Verify proper return data buffer overwriting if the opcode is meant to interact with it, otherwise verify that the return data buffer is unaffected.

| ID                                           | Description                            | Status | Tests |
| -------------------------------------------- | -------------------------------------- | ------ | ----- |
| `opcode/test/return_data/buffer/current` | Return buffer at current call context. |        |       |
| `opcode/test/return_data/buffer/parent`  | Return buffer at parent call context.  |        |       |

#### Gas Usage

##### Normal Operation

Verify gas usage affectation of each stack argument or memory input consumed by the opcode.

| ID                                 | Description                 | Status | Tests |
| ---------------------------------- | --------------------------- | ------ | ----- |
| `opcode/test/gas_usage/normal` | Normal operation gas usage. |        |       |

##### Memory Expansion

Verify that the memory expansion correctly follows the gas calculation.

| ID                                           | Description       | Status | Tests |
| -------------------------------------------- | ----------------- | ------ | ----- |
| `opcode/test/gas_usage/memory_expansion` | Memory expansion. |        |       |

##### Extra Gas

Verify that attempting to execute the opcode when gas available is 1 more than the required gas results in exceptional abort.

| ID                                               | Description                         | Status | Tests |
| ------------------------------------------------ | ----------------------------------- | ------ | ----- |
| `opcode/test/gas_usage/extra_gas` | extra gas should not fail the execution  |        |       |

##### Out-Of-Gas

Verify that attempting to execute the opcode when gas available is 1 less than the required gas results in exceptional abort.

| ID                                               | Description                         | Status | Tests |
| ------------------------------------------------ | ----------------------------------- | ------ | ----- |
| `opcode/test/gas_usage/out_of_gas_execution` | Out-of-gas due to opcode inputs.    |        |       |
| `opcode/test/gas_usage/out_of_gas_memory`    | Out-of-gas due to memory expansion. |        |       |

##### Order-of-operations

If the opcode requires different gas stipends for other operations (e.g. contract creation, cold/warm account access), create one case for each operation (ideally independent of each other) and the listed cases for each.

| ID                                                    | Description                                                        | Status | Tests |
| ----------------------------------------------------- | ------------------------------------------------------------------ | ------ | ----- |
| `opcode/test/gas_usage/order_of_operations/exact` | Success using the exact amount of gas required for the stipend.    |        |       |
| `opcode/test/gas_usage/order_of_operations/oog`   | OOG with a 1-gas-difference from the gas required for the stipend. |        |       |

#### Terminating opcode

If an opcode is terminating, meaning it results in the current call context to end execution.

| ID                                                | Description                 | Status | Tests |
| ------------------------------------------------- | --------------------------- | ------ | ----- |
| `opcode/test/terminating/scenarios/top_level` | Top-level call termination. |        |       |
| `opcode/test/terminating/scenarios/sub_level` | Sub-level call termination. |        |       |
| `opcode/test/terminating/scenarios/initcode`  | Initcode termination.       |        |       |

#### Aborting/Reverting opcode

If the terminating opcode is meant to rollback the executing call frame, verify the listed events are properly rolled back.

| ID                                               | Description         | Status | Tests |
| ------------------------------------------------ | ------------------- | ------ | ----- |
| `opcode/test/terminating/rollback/balance`   | Balance changes.    |        |       |
| `opcode/test/terminating/rollback/storage`   | Storage changes.    |        |       |
| `opcode/test/terminating/rollback/contracts` | Contract creations. |        |       |
| `opcode/test/terminating/rollback/nonce`     | Nonce increments.   |        |       |
| `opcode/test/terminating/rollback/logs`      | Log events.         |        |       |

#### Out-of-bounds checks

If the opcode has out-of-bounds conditions in its parameters/inputs.

| ID                                                  | Description                       | Status | Tests |
| --------------------------------------------------- | --------------------------------- | ------ | ----- |
| `opcode/test/out_of_bounds/verify/max`          | Max value for each parameter.     |        |       |
| `opcode/test/out_of_bounds/verify/max_plus_one` | Max value + 1 for each parameter. |        |       |

#### Exceptional Abort

If the opcode has conditions, either inputs or execution context states, that should cause exceptional abort and are different than out-of-gas or stack overflow or underflow.

| ID                                  | Description                   | Status | Tests |
| ----------------------------------- | ----------------------------- | ------ | ----- |
| `opcode/test/exceptional_abort` | Exceptional abort conditions. |        |       |

#### Data portion

If an opcode has a data portion, meaning the `N` bytes following the opcode in the contract bytecode are skipped from execution.

| ID                                       | Description                                                                      | Status | Tests |
| ---------------------------------------- | -------------------------------------------------------------------------------- | ------ | ----- |
| `opcode/test/data_portion/all_zeros` | All zeros data portion.                                                          |        |       |
| `opcode/test/data_portion/max_value` | Max value data portion (`2**N-1` where `N` is the bit size of the data portion). |        |       |
| `opcode/test/data_portion/jump`      | Jump into the data portion.                                                      |        |       |

#### Contract creation

If the opcode execution results in the creation of a new contract in the state.

##### Correct Creation

Verify contract is created at the expected address given multiple inputs.

| ID                                          | Description          | Status | Tests |
| ------------------------------------------- | -------------------- | ------ | ----- |
| `opcode/test/contract_creation/address` | Address calculation. |        |       |

##### Creation Failure

The contract creation fails given the listed conditions.

| ID                                                             | Description                                                                                       | Status | Tests |
| -------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- | ------ | ----- |
| `opcode/test/contract_creation/failure/oog`                | Out-of-gas when available gas is less than minimum contract creation stipend.                     |        |       |
| `opcode/test/contract_creation/failure/insufficient_value` | Opcode has a value parameter and the caller does not have enough funds.                           |        |       |
| `opcode/test/contract_creation/failure/collision`          | Creation would result in an address collision with an existing contract or EOA-delegated address. |        |       |

##### Recursive Contract Creation

Opcode is used to attempt to recreate a contract that is currently mid-creation by a previous call of the same opcode.

| ID                                            | Description                                   | Status | Tests |
| --------------------------------------------- | --------------------------------------------- | ------ | ----- |
| `opcode/test/contract_creation/recursive` | Recursive contract creation using the opcode. |        |       |

#### Fork transition

| ID                                        | Description                                                                                                                               | Status | Tests |
| ----------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- | ------ | ----- |
| `opcode/test/fork_transition/invalid` | Exceptional abort if executed before its activation fork/after its deactivation fork.                                                     |        |       |
| `opcode/test/fork_transition/at`      | Verify correct opcode behavior at transition block, in the case of opcodes which behavior depends on current or parent block information. |        |       |

### Framework Changes

- Add opcode to `src/ethereum_test_vm/opcode.py`
- Add opcode to relevant methods in the fork where the EIP is introduced in `src/ethereum_test_forks/forks/forks.py`

## New Precompile

The EIP introduces one or more new precompiles.

### Test Vectors

#### Call contexts

Evaluate precompile behavior when called using different call opcodes or called from different execution contexts.

##### `CALL`

Verify precompile operation when called using the `CALL` opcode.

| ID                                         | Description | Status | Tests |
| ------------------------------------------ | ----------- | ------ | ----- |
| `precompile/test/call_contexts/normal` | `CALL`.     |        |       |

##### `DELEGATECALL`

Verify precompile operation when called using the `DELEGATECALL` opcode.

| ID                                           | Description     | Status | Tests |
| -------------------------------------------- | --------------- | ------ | ----- |
| `precompile/test/call_contexts/delegate` | `DELEGATECALL`. |        |       |

##### `STATICCALL`

Verify precompile operation when called using the `STATICCALL` opcode.

If the precompile is stateful, meaning calling it affects its storage, this call must result in exceptional abort.

| ID                                         | Description   | Status | Tests |
| ------------------------------------------ | ------------- | ------ | ----- |
| `precompile/test/call_contexts/static` | `STATICCALL`. |        |       |

##### `CALLCODE`

Verify precompile operation when called using the `CALLCODE` opcode.

| ID                                           | Description | Status | Tests |
| -------------------------------------------- | ----------- | ------ | ----- |
| `precompile/test/call_contexts/callcode` | `CALLCODE`. |        |       |

##### Transaction Entry-point

Verify precompile behavior when it's used as `tx.to`.

| ID                                           | Description                            | Status | Tests |
| -------------------------------------------- | -------------------------------------- | ------ | ----- |
| `precompile/test/call_contexts/tx_entry` | Precompile as transaction entry-point. |        |       |

##### Initcode call

Verify calling the opcode during initcode execution of a new contract.

| ID                                                  | Description                                                                        | Status | Tests |
| --------------------------------------------------- | ---------------------------------------------------------------------------------- | ------ | ----- |
| `precompile/test/call_contexts/initcode/CREATE` | Call from Initcode initiated from a CREATE/CREATE2 opcode.                         |        |       |
| `precompile/test/call_contexts/initcode/tx`     | Call from Initcode initiated from a contract-creating transaction (`tx.to==None`). |        |       |

##### Precompile as Set-code Delegated Address

Test setting the precompile as a set-code delegated address, and verify no precompile logic is executed.

| ID                                           | Description                 | Status | Tests |
| -------------------------------------------- | --------------------------- | ------ | ----- |
| `precompile/test/call_contexts/set_code` | Set code delegated address. |        |       |

#### Inputs

| ID                                             | Description                                                                                                                                                                                                          | Status | Tests |
| ---------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ | ----- |
| `precompile/test/inputs/valid`             | Verify combinations of valid inputs to the precompile.                                                                                                                                                               |        |       |
| `precompile/test/inputs/valid/boundary`    | Verify all boundary values given the precompile functionality.                                                                                                                                                       |        |       |
| `precompile/test/inputs/valid/crypto`      | If precompile performs cryptographic operations, verify behavior on all inputs that have special cryptographic properties (e.g. infinity points as inputs, or input values that result in infinity points returned). |        |       |
| `precompile/test/inputs/all_zeros`         | Verify all zeros input.                                                                                                                                                                                              |        |       |
| `precompile/test/inputs/max_values`        | Verify 2^N-1 where N is a single or multiple valid bit-lengths.                                                                                                                                                      |        |       |
| `precompile/test/inputs/invalid`           | Verify combinations of invalid inputs to the precompile.                                                                                                                                                             |        |       |
| `precompile/test/inputs/invalid/crypto`    | Inputs that fail specific mathematical or cryptographic validity checks.                                                                                                                                             |        |       |
| `precompile/test/inputs/invalid/corrupted` | Inputs that are malformed/corrupted.                                                                                                                                                                                 |        |       |

#### Value Transfer

##### Minimum Fee Precompile

If the precompile requires a minimum value (fee) to execute, either constant or depending on a formula.

| ID                                             | Description                                                      | Status | Tests |
| ---------------------------------------------- | ---------------------------------------------------------------- | ------ | ----- |
| `precompile/test/value_transfer/fee/under` | Calls with the required value amount minus one, expect failure.  |        |       |
| `precompile/test/value_transfer/fee/exact` | Calls with the exact required amount, expect success.            |        |       |
| `precompile/test/value_transfer/fee/over`  | Calls with extra value than the required amount, expect success. |        |       |

##### No-Fee Precompile

If the precompile does not require any minimum value (fee) to execute.

| ID                                             | Description                                                      | Status | Tests |
| ---------------------------------------------- | ---------------------------------------------------------------- | ------ | ----- |
| `precompile/test/value_transfer/no_fee` | Sending non-zero value does not cause an exception (unless otherwise specified by the EIP). | | |

#### Out-of-bounds checks

If the precompile has out-of-bounds conditions in its inputs.

| ID                                               | Description                   | Status | Tests |
| ------------------------------------------------ | ----------------------------- | ------ | ----- |
| `precompile/test/out_of_bounds/max`          | Max value for each input.     |        |       |
| `precompile/test/out_of_bounds/max_plus_one` | Max value + 1 for each input. |        |       |

#### Input Lengths

Verify different combinations of input lengths to the precompile, ensuring the correct minimum fee (if any) is provided.

##### Zero-length Input

Regardless of the input requirements for the precompile.

| ID                                       | Description           | Status | Tests |
| ---------------------------------------- | --------------------- | ------ | ----- |
| `precompile/test/input_lengths/zero` | Zero-length calldata. |        |       |

##### Static Required Input Length

If the precompile has a static required input length.

| ID                                                   | Description                                                                                        | Status | Tests |
| ---------------------------------------------------- | -------------------------------------------------------------------------------------------------- | ------ | ----- |
| `precompile/test/input_lengths/static/correct`   | Correct static-length calldata.                                                                    |        |       |
| `precompile/test/input_lengths/static/too_short` | Calldata too short, where the value represents a correct but truncated input to the precompile.    |        |       |
| `precompile/test/input_lengths/static/too_long`  | Calldata too long, where the value represents a correct input to the precompile with padded zeros. |        |       |

##### Dynamic Required Input Length

If the precompile has a variable required input-length based on a formula, test all listed scenarios given different input lengths.

| ID                                                    | Description                                                                                        | Status | Tests |
| ----------------------------------------------------- | -------------------------------------------------------------------------------------------------- | ------ | ----- |
| `precompile/test/input_lengths/dynamic/valid`     | Verify correct precompile execution for valid lengths.                                             |        |       |
| `precompile/test/input_lengths/dynamic/too_short` | Calldata too short, where the value represents a correct but truncated input to the precompile.    |        |       |
| `precompile/test/input_lengths/dynamic/too_long`  | Calldata too long, where the value represents a correct input to the precompile with padded zeros. |        |       |

#### Gas usage

##### Constant Gas Cost

If the precompile always charges the same gas cost regardless of input conditions.

| ID                                             | Description                                                         | Status | Tests |
| ---------------------------------------------- | ------------------------------------------------------------------- | ------ | ----- |
| `precompile/test/gas_usage/constant/exact` | Verify exact gas consumption.                                       |        |       |
| `precompile/test/gas_usage/constant/oog`   | Verify exact gas consumption minus one results in out-of-gas error. |        |       |

##### Variable Gas Cost

If the precompile charges variable gas cost given input conditions, test all listed scenarios using multiple different valid inputs.

| ID                                            | Description                                                         | Status | Tests |
| --------------------------------------------- | ------------------------------------------------------------------- | ------ | ----- |
| `precompile/test/gas_usage/dynamic/exact` | Verify exact gas consumption.                                       |        |       |
| `precompile/test/gas_usage/dynamic/oog`   | Verify exact gas consumption minus one results in out-of-gas error. |        |       |

##### Excessive Gas

Verify spending all block gas in calls to the precompile (Use `Environment().gas_limit` as reference max amount).

| ID                                        | Description          | Status | Tests |
| ----------------------------------------- | -------------------- | ------ | ----- |
| `precompile/test/excessive_gas_usage` | Excessive gas usage. |        |       |

#### Fork transition

##### Pre-fork Block Call

Verify that calling the precompile before its activation fork results in a valid call, even for inputs that are expected to be invalid for the precompile, or a zero-gas call.

| ID                                                         | Description         | Status | Tests |
| ---------------------------------------------------------- | ------------------- | ------ | ----- |
| `precompile/test/fork_transition/before/invalid_input` | Invalid input call. |        |       |
| `precompile/test/fork_transition/before/zero_gas`      | Zero-gas call.      |        |       |

##### Cold/Warm Precompile Address State

Verify the cold/warm state of the precompile address depending on the fork activation.

| ID                                                | Description                                                       | Status | Tests |
| ------------------------------------------------- | ----------------------------------------------------------------- | ------ | ----- |
| `precompile/test/fork_transition/before/cold` | Precompile address is cold by default before the fork activation. |        |       |
| `precompile/test/fork_transition/after/warm`  | Precompile address is warm by default after the fork activation.  |        |       |

### Framework Changes

- Add precompile address to relevant methods in the fork where the EIP is introduced in `src/ethereum_test_forks/forks/forks.py`

## Removed Precompile

The EIP removes one or more precompiles from the existing list of precompiles.

### Test Vectors

#### Fork transition

##### Precompile Operation

Verify that the precompile remains operational up until the last block before the fork is active, and behaves as an account with empty code afterwards.

| ID                                                    | Description                              | Status | Tests |
| ----------------------------------------------------- | ---------------------------------------- | ------ | ----- |
| `removed_precompile/test/fork_transition/operational` | Precompile operation on fork activation. |        |       |

##### Cold/Warm Precompile Address State

Verify the cold/warm state of the precompile address depending on the fork activation.

| ID                                                    | Description                                                       | Status | Tests |
| ----------------------------------------------------- | ----------------------------------------------------------------- | ------ | ----- |
| `removed_precompile/test/fork_transition/before/warm` | Precompile address is warm by default before the fork activation. |        |       |
| `removed_precompile/test/fork_transition/after/cold`  | Precompile address is cold by default after the fork activation.  |        |       |

### Framework Changes

- Remove the precompile address from relevant methods in the fork where the EIP is removed in `src/ethereum_test_forks/forks/forks.py`

## New System Contract

### Test Vectors

#### Call contexts

Evaluate precompile behavior when called using different call opcodes or called from different execution contexts.

##### `CALL`

Verify system contract operation when called using the `CALL` opcode.

| ID                                              | Description | Status | Tests |
| ----------------------------------------------- | ----------- | ------ | ----- |
| `system_contract/test/call_contexts/normal` | `CALL`.     |        |       |

##### `DELEGATECALL`

Verify system contract operation when called using the `DELEGATECALL` opcode.

| ID                                                | Description     | Status | Tests |
| ------------------------------------------------- | --------------- | ------ | ----- |
| `system_contract/test/call_contexts/delegate` | `DELEGATECALL`. |        |       |

##### `STATICCALL`

Verify system contract operation when called using the `STATICCALL` opcode.

If the system contract is stateful, meaning calling it affects its storage, this call must result in exceptional abort.

| ID                                              | Description   | Status | Tests |
| ----------------------------------------------- | ------------- | ------ | ----- |
| `system_contract/test/call_contexts/static` | `STATICCALL`. |        |       |

##### `CALLCODE`

Verify system contract operation when called using the `CALLCODE` opcode.

| ID                                                | Description | Status | Tests |
| ------------------------------------------------- | ----------- | ------ | ----- |
| `system_contract/test/call_contexts/callcode` | `CALLCODE`. |        |       |

##### Transaction Entry-point

Verify system contract behavior when it's used as `tx.to`.

| ID                                                | Description                                 | Status | Tests |
| ------------------------------------------------- | ------------------------------------------- | ------ | ----- |
| `system_contract/test/call_contexts/tx_entry` | System Contract as transaction entry-point. |        |       |

##### Initcode call

Verify calling the opcode during initcode execution of a new contract.

| ID                                                       | Description                                                                        | Status | Tests |
| -------------------------------------------------------- | ---------------------------------------------------------------------------------- | ------ | ----- |
| `system_contract/test/call_contexts/initcode/CREATE` | Call from Initcode initiated from a CREATE/CREATE2 opcode.                         |        |       |
| `system_contract/test/call_contexts/initcode/tx`     | Call from Initcode initiated from a contract-creating transaction (`tx.to==None`). |        |       |

##### System Contract as Set-code Delegated Address

Test setting the system contract as a set-code delegated address, and verify no system contract side-effects are triggered, even if the actual system contract logic is executed.

If the system contract requires specific storage pre-conditions to be set for proper execution (e.g. if the contract contains a safety mechanism that prevents it from executing prior to the fork activation), ensure the delegated account has the proper values in the storage to guarantee the correct logic is executed.

| ID                                                | Description                 | Status | Tests |
| ------------------------------------------------- | --------------------------- | ------ | ----- |
| `system_contract/test/call_contexts/set_code` | Set code delegated address. |        |       |

#### Inputs

| ID                                                  | Description                                                              | Status | Tests |
| --------------------------------------------------- | ------------------------------------------------------------------------ | ------ | ----- |
| `system_contract/test/inputs/valid`             | Verify combinations of valid inputs to the system contract.              |        |       |
| `system_contract/test/inputs/boundary`          | Verify all boundary values given the system contract functionality.      |        |       |
| `system_contract/test/inputs/all_zeros`         | Verify all zeros input.                                                  |        |       |
| `system_contract/test/inputs/max_values`        | Verify 2^N-1 where N is a single or multiple valid bit-lengths.          |        |       |
| `system_contract/test/inputs/invalid`           | Verify combinations of invalid inputs to the precompile.                 |        |       |
| `system_contract/test/inputs/invalid/checks`    | Inputs that fail validity checks.                                        |        |       |
| `system_contract/test/inputs/invalid/crypto`    | Inputs that fail specific mathematical or cryptographic validity checks. |        |       |
| `system_contract/test/inputs/invalid/corrupted` | Inputs that are malformed/corrupted.                                     |        |       |

#### Value Transfer

##### Minimum Fee System Contract

If the system contract requires a minimum value (fee) to execute, either constant or depending on a formula.

| ID                                                  | Description                                                      | Status | Tests |
| --------------------------------------------------- | ---------------------------------------------------------------- | ------ | ----- |
| `system_contract/test/value_transfer/fee/under` | Calls with the required value amount minus one, expect failure.  |        |       |
| `system_contract/test/value_transfer/fee/exact` | Calls with the exact required amount, expect success.            |        |       |
| `system_contract/test/value_transfer/fee/over`  | Calls with extra value than the required amount, expect success. |        |       |

##### No-Fee System Contract

If the system contract does not require any minimum value (fee) to execute.

| ID                                               | Description                                                                                 | Status | Tests |
| ------------------------------------------------ | ------------------------------------------------------------------------------------------- | ------ | ----- |
| `system_contract/test/value_transfer/no_fee` | Sending non-zero value does not cause an exception (unless otherwise specified by the EIP). |        |       |

#### Out-of-bounds checks

If the system contract has out-of-bounds conditions in its inputs.

| ID                                                    | Description                   | Status | Tests |
| ----------------------------------------------------- | ----------------------------- | ------ | ----- |
| `system_contract/test/out_of_bounds/max`          | Max value for each input.     |        |       |
| `system_contract/test/out_of_bounds/max_plus_one` | Max value + 1 for each input. |        |       |

#### Input Lengths

Verify different combinations of input lengths to the system contract, ensuring the correct minimum fee (if any) is provided.

##### Zero-length Input

Regardless of the input requirements for the system contract.

| ID                                            | Description           | Status | Tests |
| --------------------------------------------- | --------------------- | ------ | ----- |
| `system_contract/test/input_lengths/zero` | Zero-length calldata. |        |       |

##### Static Required Input Length

If the system contract has a static required input length.

| ID                                                        | Description                                                                                      | Status | Tests |
| --------------------------------------------------------- | ------------------------------------------------------------------------------------------------ | ------ | ----- |
| `system_contract/test/input_lengths/static/correct`   | Correct static-length calldata.                                                                  |        |       |
| `system_contract/test/input_lengths/static/too_short` | Calldata too short, where the value represents a correct but truncated input to the contract.    |        |       |
| `system_contract/test/input_lengths/static/too_long`  | Calldata too long, where the value represents a correct input to the contract with padded zeros. |        |       |

##### Dynamic Required Input Length

If the system contract has a variable required input-length based on a formula, test all listed scenarios given different input lengths.

| ID                                                         | Description                                                                                      | Status | Tests |
| ---------------------------------------------------------- | ------------------------------------------------------------------------------------------------ | ------ | ----- |
| `system_contract/test/input_lengths/dynamic/valid`     | Verify correct system contract execution for valid lengths.                                      |        |       |
| `system_contract/test/input_lengths/dynamic/too_short` | Calldata too short, where the value represents a correct but truncated input to the contract.    |        |       |
| `system_contract/test/input_lengths/dynamic/too_long`  | Calldata too long, where the value represents a correct input to the contract with padded zeros. |        |       |

#### Gas usage

##### Constant Gas Cost

If the system contract always charges the same gas cost regardless of input conditions.

| ID                                                  | Description                                                         | Status | Tests |
| --------------------------------------------------- | ------------------------------------------------------------------- | ------ | ----- |
| `system_contract/test/gas_usage/constant/exact` | Verify exact gas consumption.                                       |        |       |
| `system_contract/test/gas_usage/constant/oog`   | Verify exact gas consumption minus one results in out-of-gas error. |        |       |

##### Variable Gas Cost

If the system contract charges variable gas cost given input conditions, test all listed scenarios using multiple different valid inputs.

| ID                                                 | Description                                                         | Status | Tests |
| -------------------------------------------------- | ------------------------------------------------------------------- | ------ | ----- |
| `system_contract/test/gas_usage/dynamic/exact` | Verify exact gas consumption.                                       |        |       |
| `system_contract/test/gas_usage/dynamic/oog`   | Verify exact gas consumption minus one results in out-of-gas error. |        |       |

#### Excessive Gas Cases

##### Excessive Gas Usage During Block Execution

Verify spending all block gas in calls to system contract (Use `Environment().gas_limit` as reference max amount).

| ID                                                 | Description              | Status | Tests |
| -------------------------------------------------- | ------------------------ | ------ | ----- |
| `system_contract/test/excessive_gas/block_gas` | Exhaust block gas limit. |        |       |

##### Excessive Gas Usage During System Call

If possible, produce a scenario where, given all transactions executed within the block result in the execution of the contract by the system address would result in excessive gas usage.

| ID                                                   | Description                   | Status | Tests |
| ---------------------------------------------------- | ----------------------------- | ------ | ----- |
| `system_contract/test/excessive_gas/system_call` | Excessive gas on system call. |        |       |

#### System Contract Deployment

| ID                                            | Description                                                                                                                                        | Status | Tests |
| --------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- | ------ | ----- |
| `system_contract/test/deployment/missing` | Verify block execution behavior after fork activation if the system contract has not been deployed (Depending on the EIP, block could be invalid). |        |       |
| `system_contract/test/deployment/address` | Verify deployment transaction results in the system contract being deployed to the expected address.                                               |        |       |

#### Contract Variations

Verify execution of the different variations of the contract for different networks (if any) results in the expected behavior.

| ID                                                      | Description                            | Status | Tests |
| ------------------------------------------------------- | -------------------------------------- | ------ | ----- |
| `system_contract/test/contract_variations/networks` | Different network contract variations. |        |       |

#### Contract Substitution

Substitute the default system contract with a mock contract to modify its behavior when called by the system address (at the end of the block execution).

| ID                                                                 | Description                                                                         | Status | Tests |
| ------------------------------------------------------------------ | ----------------------------------------------------------------------------------- | ------ | ----- |
| `system_contract/test/contract_substitution/return_lengths`    | Modified return value lengths.                                                      |        |       |
| `system_contract/test/contract_substitution/logs`              | Modified to emit logs or modified logs.                                             |        |       |
| `system_contract/test/contract_substitution/exception`         | Modified to cause an exception (e.g. invalid opcode).                               |        |       |
| `system_contract/test/contract_substitution/gas_limit_success` | Modified to consume 30,000,000 million gas exactly, execution should be successful. |        |       |
| `system_contract/test/contract_substitution/gas_limit_failure` | Modified to consume 30,000,001 million gas exactly, execution should fail.          |        |       |

#### Fork transition

Verify calling the system contract before its activation fork results in correct behavior (depends on the system contract implementation).

| ID                                                          | Description                       | Status | Tests |
| ----------------------------------------------------------- | --------------------------------- | ------ | ----- |
| `system_contract/test/fork_transition/call_before_fork` | Call system contract before fork. |        |       |

### Framework Changes

- Add system contract address to relevant methods in the fork where the EIP is introduced in `src/ethereum_test_forks/forks/forks.py`
- Add system contract bytecode to the returned value of `pre_allocation_blockchain` in the fork where the EIP is introduced in `src/ethereum_test_forks/forks/forks.py`

## New Transaction Type

### Test Vectors

#### Intrinsic Validity

Verify the transaction (and the block it is included in) is valid or invalid given the intrinsic validity of the new transaction type, depending on each test scenario.

For each new field that affects the intrinsic gas cost of the transaction verify all listed scenarios.

##### Gas Limit

Note: Data floor gas cost affects the intrinsic validity of all transaction types, so it must be taken into account when designing all test scenarios.

| ID                                                                    | Description                                                                        | Status | Tests |
| --------------------------------------------------------------------- | ---------------------------------------------------------------------------------- | ------ | ----- |
| `transaction_type/test/intrinsic_validity/gas_limit/exact`        | Provide the exact intrinsic gas as `gas_limit` value to the transaction.           |        |       |
| `transaction_type/test/intrinsic_validity/gas_limit/insufficient` | Provide the exact intrinsic gas minus one as `gas_limit` value to the transaction. |        |       |

##### Gas Fee

| ID                                                                                     | Description                                                    | Status | Tests |
| -------------------------------------------------------------------------------------- | -------------------------------------------------------------- | ------ | ----- |
| `transaction_type/test/intrinsic_validity/max_fee/max_priority_lower_than_max_fee` | Invalid if `tx.max_priority_fee_per_gas < tx.max_fee_per_gas`. |        |       |
| `transaction_type/test/intrinsic_validity/max_fee/max_priority_equal_to_max_fee`   | Valid if `tx.max_priority_fee_per_gas == tx.max_fee_per_gas`.  |        |       |
| `transaction_type/test/intrinsic_validity/max_fee/base_lower`                      | Invalid if `tx.max_fee_per_gas < block.base_fee_per_gas`.      |        |       |
| `transaction_type/test/intrinsic_validity/max_fee/base_equal`                      | Valid if `tx.max_fee_per_gas < block.base_fee_per_gas`.        |        |       |

##### Chain ID

| ID                                                      | Description                                   | Status | Tests |
| ------------------------------------------------------- | --------------------------------------------- | ------ | ----- |
| `transaction_type/test/intrinsic_validity/chain_id` | Invalid if `tx.chain_id != network.chain_id`. |        |       |

##### Nonce

| ID                                                             | Description                                | Status | Tests |
| -------------------------------------------------------------- | ------------------------------------------ | ------ | ----- |
| `transaction_type/test/intrinsic_validity/nonce_minus_one` | Invalid if `tx.nonce == sender.nonce - 1`. |        |       |
| `transaction_type/test/intrinsic_validity/nonce_plus_one`  | Invalid if `tx.nonce == sender.nonce + 1`. |        |       |
| `transaction_type/test/intrinsic_validity/nonce_exact`     | Valid if `tx.nonce == sender.nonce`.       |        |       |

##### To

| ID                                                | Description                                             | Status | Tests |
| ------------------------------------------------- | ------------------------------------------------------- | ------ | ----- |
| `transaction_type/test/intrinsic_validity/to` | Valid/Invalid if `tx.to == None`, depending on the EIP. |        |       |

##### Value

| ID                                                                                 | Description                                                                                  | Status | Tests |
| ---------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- | ------ | ----- |
| `transaction_type/test/intrinsic_validity/value_non_zero_insufficient_balance` | Invalid if `tx.value == 1` and `account.balance == (tx.max_fee_per_gas * tx.gas_price)`.     |        |       |
| `transaction_type/test/intrinsic_validity/value_non_zero_sufficient_balance`   | Valid if `tx.value == 1` and `account.balance == (tx.max_fee_per_gas * tx.gas_price) + 1`.   |        |       |
| `transaction_type/test/intrinsic_validity/value_zero_insufficient_balance`     | Invalid if `tx.value == 0` and `account.balance == (tx.max_fee_per_gas * tx.gas_price) - 1`. |        |       |
| `transaction_type/test/intrinsic_validity/value_zero_sufficient_balance`       | Valid if `tx.value == 0` and `account.balance == (tx.max_fee_per_gas * tx.gas_price)`.       |        |       |

##### Data

| ID                                                                                 | Description                                                                                                           | Status | Tests |
| ---------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- | ------ | ----- |
| `transaction_type/test/intrinsic_validity/data_floor_above_intrinsic_gas_cost` | Invalid if `data_floor_cost(len(tx.data)) > tx.intrinsic_gas_cost` and `tx.gas_limit == tx.intrinsic_gas_cost`.       |        |       |
| `transaction_type/test/intrinsic_validity/data_floor_above_intrinsic_gas_cost` | Valid if `data_floor_cost(len(tx.data)) > tx.intrinsic_gas_cost` and `tx.gas_limit == data_floor_cost(len(tx.data))`. |        |       |

#### Signature

Verify the transaction is correctly rejected if it contains an invalid signature.

| ID                                                                | Description                                                                     | Status | Tests |
| ----------------------------------------------------------------- | ------------------------------------------------------------------------------- | ------ | ----- |
| `transaction_type/test/signature/invalid/field_outside_curve` | V, R, S represent a value that is inside of the field but outside of the curve. |        |       |

##### V

| ID                                                  | Description                                                            | Status | Tests |
| --------------------------------------------------- | ---------------------------------------------------------------------- | ------ | ----- |
| `transaction_type/test/signature/invalid/v/2`   | `2`.                                                                   |        |       |
| `transaction_type/test/signature/invalid/v/27`  | `27` (Type-0 transaction valid value).                                 |        |       |
| `transaction_type/test/signature/invalid/v/28`  | `28` (Type-0 transaction valid value).                                 |        |       |
| `transaction_type/test/signature/invalid/v/35`  | `35` (Type-0 replay-protected transaction valid value for chain id 1). |        |       |
| `transaction_type/test/signature/invalid/v/36`  | `36` (Type-0 replay-protected transaction valid value for chain id 1). |        |       |
| `transaction_type/test/signature/invalid/v/max` | `2**8-1`.                                                              |        |       |

##### R

| ID                                                                   | Description     | Status | Tests |
| -------------------------------------------------------------------- | --------------- | ------ | ----- |
| `transaction_type/test/signature/invalid/r/0`                    | `0`.            |        |       |
| `transaction_type/test/signature/invalid/r/secp256k1n_minus_one` | `SECP256K1N-1`. |        |       |
| `transaction_type/test/signature/invalid/r/secp256k1n`           | `SECP256K1N`.   |        |       |
| `transaction_type/test/signature/invalid/r/secp256k1n_plus_one`  | `SECP256K1N+1`. |        |       |
| `transaction_type/test/signature/invalid/r/max_minus_one`        | `2**256-1`.     |        |       |
| `transaction_type/test/signature/invalid/r/max`                  | `2**256`.       |        |       |

##### S

| ID                                                                        | Description                            | Status | Tests |
| ------------------------------------------------------------------------- | -------------------------------------- | ------ | ----- |
| `transaction_type/test/signature/invalid/s/0`                         | `0`.                                   |        |       |
| `transaction_type/test/signature/invalid/s/secp256k1n_half_minus_one` | `SECP256K1N//2-1`.                     |        |       |
| `transaction_type/test/signature/invalid/s/secp256k1n_half`           | `SECP256K1N//2`.                       |        |       |
| `transaction_type/test/signature/invalid/s/secp256k1n_half_plus_one`  | `SECP256K1N//2+1`.                     |        |       |
| `transaction_type/test/signature/invalid/s/secp256k1n_minus_one`      | `SECP256K1N-1`.                        |        |       |
| `transaction_type/test/signature/invalid/s/secp256k1n`                | `SECP256K1N`.                          |        |       |
| `transaction_type/test/signature/invalid/s/secp256k1n_plus_one`       | `SECP256K1N+1`.                        |        |       |
| `transaction_type/test/signature/invalid/s/max_minus_one`             | `2**256-1`.                            |        |       |
| `transaction_type/test/signature/invalid/s/max`                       | `2**256`.                              |        |       |
| `transaction_type/test/signature/invalid/s/complement`                | `SECP256K1N - S` of a valid signature. |        |       |

#### Transaction Attributes Readable From EVM

| ID                                                              | Description                                                                                                                     | Status | Tests |
| --------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- | ------ | ----- |
| `transaction_type/test/tx_scoped_attributes/read`           | Verify attributes that can be read in the EVM from transaction fields.                                                          |        |       |
| `transaction_type/test/tx_scoped_attributes/older_tx_types` | Verify attributes specific to the new transaction type that can be read in the EVM behave correctly on older transaction types. |        |       |

#### Transaction-Scoped Persistent Values

Verify values or variables that are persistent through the execution of the transaction (e.g. transient storage, warm/cold accounts).

| ID                                                                    | Description                                   | Status | Tests |
| --------------------------------------------------------------------- | ----------------------------------------------| ------ | ----- |
| `transaction_type/test/tx_scoped_attributes/persistent/throughout` | Persist throughout the entire transaction. | | |
| `transaction_type/test/tx_scoped_attributes/persistent/reset` | Reset on subsequent transactions in the same block. | | |

#### Encoding (RLP, SSZ)

Verify correct transaction rejection in all listed scenarios.

##### Field Sizes

Verify all listed scenarios for each transaction field.

| ID                                                            | Description                                       | Status | Tests |
| ------------------------------------------------------------- | ------------------------------------------------- | ------ | ----- |
| `transaction_type/test/encoding/field_sizes/leading_zero` | Add leading zero byte.                            |        |       |
| `transaction_type/test/encoding/field_sizes/remove_byte`  | Remove single byte from fixed-byte-length fields. |        |       |

##### Fields of List Type

Verify for each transaction field that is of type list.

| ID                                                           | Description                                   | Status | Tests |
| ------------------------------------------------------------ | --------------------------------------------- | ------ | ----- |
| `transaction_type/test/encoding/list_field/zero`         | Zero-element list (Failure depending on EIP). |        |       |
| `transaction_type/test/encoding/list_field/max`          | Max count list.                               |        |       |
| `transaction_type/test/encoding/list_field/max_plus_one` | Max count plus one list.                      |        |       |

##### Extra/Missing Fields

| ID                                                  | Description                                                     | Status | Tests |
| --------------------------------------------------- | --------------------------------------------------------------- | ------ | ----- |
| `transaction_type/test/encoding/missing_fields` | Any fields particular to the new transaction types are missing. |        |       |
| `transaction_type/test/encoding/extra_fields`   | Transaction contains extra fields.                              |        |       |

##### Serialization Corruption

| ID                                               | Description                                       | Status | Tests |
| ------------------------------------------------ | ------------------------------------------------- | ------ | ----- |
| `transaction_type/test/encoding/truncated`   | Serialized bytes object is truncated by one byte. |        |       |
| `transaction_type/test/encoding/extra_bytes` | Serialized bytes object has one extra byte.       |        |       |

##### Serializable Fields

Verify for each serializable field, all previous tests plus following listed scenario.

| ID                                                                | Description                                                                                                  | Status | Tests |
| ----------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ | ------ | ----- |
| `transaction_type/test/encoding/new_types/incorrect_encoding` | Serializable field is encoded as bytes instead of using the correct encoding (e.g. list in the case of RLP). |        |       |

#### Out-of-bounds checks

Verify if the transaction has out-of-bounds conditions in its fields and verify.

| ID                                                     | Description                   | Status | Tests |
| ------------------------------------------------------ | ----------------------------- | ------ | ----- |
| `transaction_type/test/out_of_bounds/max`          | Max value for each field.     |        |       |
| `transaction_type/test/out_of_bounds/max_plus_one` | Max value + 1 for each field. |        |       |

#### Contract creation

Verify that the transaction can create new contracts if the transaction type supports it.

| ID                                            | Description                                  | Status | Tests |
| --------------------------------------------- | -------------------------------------------- | ------ | ----- |
| `transaction_type/test/contract_creation` | Create contracts using new transaction type. |        |       |

#### Sender account modifications

| ID                                                 | Description                                                                                                                                                                                               | Status | Tests |
| -------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ | ----- |
| `transaction_type/test/sender_account/nonce`   | Sender account has its nonce incremented at least by one after the transaction is included in a block (or more if the transaction type introduces a new mechanism that bumps the nonce by more than one). |        |       |
| `transaction_type/test/sender_account/balance` | Sender account has its balance reduced by the correct amount (gas consumed and value) at the start of execution (e.g. using `BALANCE`).                                                                  |        |       |

#### Block Level Interactions

##### Single Transaction In Block

Verify a block where the new transaction type is the sole transaction contained in the block.

| ID                                                               | Description                                       | Status | Tests |
| ---------------------------------------------------------------- | ------------------------------------------------- | ------ | ----- |
| `transaction_type/test/block_interactions/single_tx/invalid` | Invalid if `tx.gas_limit == block.gas_limit + 1`. |        |       |
| `transaction_type/test/block_interactions/single_tx/valid`   | Valid if `tx.gas_limit == block.gas_limit`.       |        |       |

##### Two Transactions In Block

Verify a block where the new transaction type is the last transaction contained in a block with two transactions.

| ID                                                             | Description                                                                                                                         | Status | Tests |
| -------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- | ------ | ----- |
| `transaction_type/test/block_interactions/last_tx/valid`   | Valid if `block.txs[0].gas_used + block.txs[1].gas_limit == block.gas_limit`.                                                       |        |       |
| `transaction_type/test/block_interactions/last_tx/invalid` | Invalid if `(block.txs[0].gas_used + block.txs[1].gas_limit == block.gas_limit + 1) and (block.txs[0].gas_used < block.gas_limit)`. |        |       |

##### EIP-7825

Verify a transaction of the new type is rejected if its gas limit exceeds the [EIP-7825](https://eips.ethereum.org/EIPS/eip-7825) gas limit for the current fork.

| ID                                                             | Description                                  | Status | Tests |
| -------------------------------------------------------------- | -------------------------------------------- | ------ | ----- |
| `transaction_type/test/block_interactions/eip7825/invalid` | Exceeds EIP-7825 gas limit by one.           |        |       |
| `transaction_type/test/block_interactions/eip7825/valid`   | Gas limit is exactly the EIP-7825 gas limit. |        |       |

##### Mixed transactions

Verify a block with all transactions types including the new type is executed correctly.

| ID                                                       | Description         | Status | Tests |
| -------------------------------------------------------- | ------------------- | ------ | ----- |
| `transaction_type/test/block_interactions/mixed_txs` | Mixed transactions. |        |       |

#### Fork transition

Verify that a block prior to fork activation where the new transaction type is introduced and containing the new transaction type is invalid.

| ID                                                 | Description                                                 | Status | Tests |
| -------------------------------------------------- | ----------------------------------------------------------- | ------ | ----- |
| `transaction_type/test/fork_transition/before` | New transaction type included before fork activation block. |        |       |

#### RPC Tests

- \*Verify `eth_estimateGas` behavior for different valid combinations of the new transaction type.
- `transaction_type/test/rpc/send_raw` | Verify `eth_sendRawTransaction` using `execute`.

\*Tests must be added to [`execution-apis`](https://github.com/ethereum/execution-apis) repository.

### Framework Changes

- Modify `transaction_intrinsic_cost_calculator` in the fork where the EIP is introduced in `src/ethereum_test_forks/forks/forks.py`, adding the appropriate new fields that the transaction introduced and the logic to the intrinsic gas cost calculation, if any.
- Add the transaction type number to `tx_types` response in the fork where the EIP is introduced in `src/ethereum_test_forks/forks/forks.py` (If applicable add also to `contract_creating_tx_types`).

## New Block Header Field

### Test Vectors

#### Genesis value

Verify, if possible, that the value can be set at genesis if the network starting fork is the activation fork, and that clients can consume such genesis.

| ID                                    | Description                        | Status | Tests |
| ------------------------------------- | ---------------------------------- | ------ | ----- |
| `block_header_field/test/genesis` | New block header field at genesis. |        |       |

#### Value behavior

Verify, given multiple initial values, that a block is accepted or rejected depending on the correct expected value for the current block.

| ID                                                  | Description                                                                                                                                                                                      | Status | Tests |
| --------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------ | ----- |
| `block_header_field/test/value_behavior/accept` | Block is accepted if the value is the correct expected for the current block, depending on the circumstances that affect the value as defined in the EIP.                                        |        |       |
| `block_header_field/test/value_behavior/reject` | Block is rejected if the value is modified (using `block.rlp_modifier`) to an incorrect value for the current block, depending on the circumstances that affect the value as defined in the EIP. |        |       |

#### Fork transition

| ID                                                    | Description                                                                                       | Status | Tests |
| ----------------------------------------------------- | ------------------------------------------------------------------------------------------------- | ------ | ----- |
| `block_header_field/test/fork_transition/initial` | Verify initial value of the field at the first block of the activation fork.                      |        |       |
| `block_header_field/test/fork_transition/before`  | Verify that a block containing the new header field before the activation of the fork is invalid. |        |       |
| `block_header_field/test/fork_transition/after`   | Verify that a block lacking the new header field at the activation of the fork is invalid.        |        |       |

### Framework Changes

- Add the new header field to the relevant objects:
    - `ethereum_test_fixtures.FixtureHeader`.
    - `ethereum_test_fixtures.FixtureExecutionPayload`.
    - `ethereum_test_specs.Header`.
- Add the appropriate `header_*_required` fork method to `BaseFork` in `ethereum_test_forks`.

## New Block Body Field

### Test Vectors

#### Value behavior

Verify, given multiple initial values, that a block is accepted or rejected depending on the correct expected value for the current block.

| ID                                                | Description                                                                                                                                                                                     | Status | Tests |
| ------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ | ----- |
| `block_body_field/test/value_behavior/accept` | Block is accepted if the value is the correct expected for the current block, depending on the circumstances that affect the value as defined in the EIP.                                       |        |       |
| `block_body_field/test/value_behavior/reject` | Block is rejected if the value is modified (using appropriate `block`) to an incorrect value for the current block, depending on the circumstances that affect the value as defined in the EIP. |        |       |

#### Fork transition

| ID                                                 | Description                                                                                           | Status | Tests |
| -------------------------------------------------- | ----------------------------------------------------------------------------------------------------- | ------ | ----- |
| `block_body_field/test/fork_transition/before` | Verify that a block containing the new block body field before the activation of the fork is invalid. |        |       |
| `block_body_field/test/fork_transition/after`  | Verify that a block lacking the new block field at the activation of the fork is invalid.             |        |       |

### Framework Changes

- Add the new body field to the relevant objects.
    - `ethereum_test_fixtures.FixtureBlockBase`.
    - `ethereum_test_fixtures.FixtureEngineNewPayload`.
    - `ethereum_test_specs.Block`.
- Modify `ethereum_test_specs.BlockchainTest` filling behavior to account for the new block field.

## Gas Cost Changes

### Test Vectors

#### Gas Usage

Measure and store the gas usage during the operations affected by the gas cost changes and verify the updated behavior.

| ID                                              | Description                | Status | Tests |
| ----------------------------------------------- | -------------------------- | ------ | ----- |
| `gas_cost_changes/test/gas_updates_measurement` | Measure updated gas costs. |        |       |

#### Out-of-gas

Verify the operations affected by the gas cost changes can run out-of-gas with the updated limits.

| ID                                 | Description                     | Status | Tests |
| ---------------------------------- | ------------------------------- | ------ | ----- |
| `gas_cost_changes/test/out_of_gas` | Out-Of-Gas with new gas prices. |        |       |

#### Fork transition

Verify gas costs are updated at the fork transition boundary.

| ID                                             | Description                                           | Status | Tests |
| ---------------------------------------------- | ----------------------------------------------------- | ------ | ----- |
| `gas_cost_changes/test/fork_transition/before` | Costs unaffected before the fork activation block.    |        |       |
| `gas_cost_changes/test/fork_transition/after`  | Costs are updated on and after fork activation block. |        |       |

### Framework Changes

- Modify `transaction_intrinsic_cost_calculator` in the fork where the EIP is introduced in `src/ethereum_test_forks/forks/forks.py` if the EIP affects intrinsic gas cost calculation.
- Modify `transaction_data_floor_cost_calculator` in the fork where the EIP is introduced in `src/ethereum_test_forks/forks/forks.py` if the EIP affects calldata floor cost.
- Modify `memory_expansion_gas_calculator` in the fork where the EIP is introduced in `src/ethereum_test_forks/forks/forks.py` if the EIP affects memory expansion gas cost calculation.
- Modify `gas_costs` in the fork where the EIP is introduced in `src/ethereum_test_forks/forks/forks.py` if the EIP affects specific opcode gas costs.

## Gas Refunds Changes

### Test Vectors

#### Refund calculation

Verify that the refund does not exceed `gas_used // MAX_REFUND_QUOTIENT` (`MAX_REFUND_QUOTIENT==5` in [EIP-3529](https://eips.ethereum.org/EIPS/eip-3529)) in the following scenarios.

| ID                                                  | Description                                      | Status | Tests |
| --------------------------------------------------- | ------------------------------------------------ | ------ | ----- |
| `gas_refunds_changes/test/refund_calculation/over`  | `refund == gas_used // MAX_REFUND_QUOTIENT + 1`. |        |       |
| `gas_refunds_changes/test/refund_calculation/exact` | `refund == gas_used // MAX_REFUND_QUOTIENT`.     |        |       |
| `gas_refunds_changes/test/refund_calculation/under` | `refund == gas_used // MAX_REFUND_QUOTIENT - 1`. |        |       |

#### Exceptional Abort

| ID                                                                         | Description                                                                                                                                                                                                             | Status | Tests |
| -------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ | ----- |
| `gas_refunds_changes/test/exceptional_abort/revertable`                    | If the operation causing the refund can be reverted, verify the refund is not applied if the following cases:.                                                                                                          |        |       |
| `gas_refunds_changes/test/exceptional_abort/revertable/revert`             | `REVERT`.                                                                                                                                                                                                               |        |       |
| `gas_refunds_changes/test/exceptional_abort/revertable/out_of_gas`         | Out-of-gas.                                                                                                                                                                                                             |        |       |
| `gas_refunds_changes/test/exceptional_abort/revertable/invalid_opcode`     | Invalid opcode.                                                                                                                                                                                                         |        |       |
| `gas_refunds_changes/test/exceptional_abort/revertable/upper_revert`       | `REVERT` of an upper call frame.                                                                                                                                                                                        |        |       |
| `gas_refunds_changes/test/exceptional_abort/non_revertable`                | If the operation causing the refund cannot be reverted (e.g. in the case of a transaction-scoped operation such as authorization refunds in EIP-7702), verify the refund is still applied even in the following cases:. |        |       |
| `gas_refunds_changes/test/exceptional_abort/non_revertable/revert`         | `REVERT` at the top call frame.                                                                                                                                                                                         |        |       |
| `gas_refunds_changes/test/exceptional_abort/non_revertable/out_of_gas`     | Out-of-gas at the top call frame.                                                                                                                                                                                       |        |       |
| `gas_refunds_changes/test/exceptional_abort/non_revertable/invalid_opcode` | Invalid opcode at the top call frame.                                                                                                                                                                                   |        |       |

#### Cross-Functional Test

Verify the following tests are updated to support the new type of refunds.

| ID                                                        | Description                                                    | Status | Tests |
| --------------------------------------------------------- | -------------------------------------------------------------- | ------ | ----- |
| `gas_refunds_changes/test/cross_functional/calldata_cost` | `tests/prague/eip7623_increase_calldata_cost/test_refunds.py`. |        |       |

### Framework Changes

N/A

## Blob Count Changes

### Test Vectors

#### Existing Test Updates

Verify tests in `tests/cancun/eip4844_blobs` were correctly and automatically updated to take into account the new blob count values at the new fork activation block.

| ID                                              | Description                                                     | Status | Tests |
| ----------------------------------------------- | --------------------------------------------------------------- | ------ | ----- |
| `blob_count_changes/test/eip4844_blobs_changes` | Updates to `tests/cancun/eip4844_blobs` were applied correctly. |        |       |

### Framework Changes

- Modify `blob_base_fee_update_fraction`, `target_blobs_per_block`, `max_blobs_per_block` in the fork where the EIP is introduced in `src/ethereum_test_forks/forks/forks.py` if the EIP affects any of the values returned by each function.

## New Execution Layer Request

### Test Vectors

#### Cross-Request-Type Interaction

| ID                                                           | Description                                                                                                                | Status | Tests |
| ------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------- | ------ | ----- |
| `execution_layer_request/test/cross_request_type/update` | Update `tests/prague/eip7685_general_purpose_el_requests` tests to include the new request type in the tests combinations. |        |       |

### Framework Changes

- Increment `max_request_type` in the fork where the EIP is introduced in `src/ethereum_test_forks/forks/forks.py` to the new maximum request type number after the EIP is activated.

## New Transaction-Validity Constraint

### Test Vectors

#### Fork transition

| ID                                        | Description                                                                                                                               | Status | Tests |
| ----------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- | ------ | ----- |
| `new_transaction_validity_constraint/test/fork_transition/accepted_before_fork` | Verify that a block before the activation fork is accepted even when the new constraint is not met. |        |       |
| `new_transaction_validity_constraint/test/fork_transition/accepted_after_fork` | Verify that a block after the activation fork is accepted when the new validity constraint is met. |        |       |
| `new_transaction_validity_constraint/test/fork_transition/rejected_after_fork` | Verify that a block after the activation fork is rejected when the new validity constraint is not met. |        |       |

Note: All test cases must use off-by-one values to ensure proper boundary condition verification.

### Framework Changes

- Introduce the validity constraint as a fork method that returns:
    - `None` for forks before its activation.
    - A non-`None` value starting from the fork where the constraint becomes active.

## Modified Transaction-Validity Constraint

### Test Vectors

#### Fork transition

| ID                                        | Description                                                                                                                               | Status | Tests |
| ----------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- | ------ | ----- |
| `modified_transaction_validity_constraint/test/fork_transition/accepted_before_fork` | Verify that a block before the activation fork is accepted when the existing constraint is met and, ideally, the new constraint is not met. |        |       |
| `modified_transaction_validity_constraint/test/fork_transition/rejected_before_fork` | Verify that a block before the activation fork is rejected when the existing constraint is not met and, ideally, the new constraint is met. |        |       |
| `modified_transaction_validity_constraint/test/fork_transition/accepted_after_fork` | Verify that a block after the activation fork is accepted when the new validity constraint is met. |        |       |
| `modified_transaction_validity_constraint/test/fork_transition/rejected_after_fork` | Verify that a block after the activation fork is rejected when the new validity constraint is not met. |        |       |

Note: All test cases must use off-by-one values to ensure proper boundary condition verification.

### Framework Changes

- Update the validity constraint as a fork method that returns the updated value starting from the fork where the constraint changes.

## Block-Level Validation Constraint

The EIP introduces a new constraint that applies at the block level (e.g., block RLP size limits, block validation rules).

### Test Vectors

#### Boundary Conditions

Verify block acceptance/rejection at constraint boundaries using off-by-one values.

| ID                                        | Description                                                                                 | Status | Tests |
| ----------------------------------------- |---------------------------------------------------------------------------------------------| ------ | ----- |
| `block_level_constraint/test/boundary/under` | Verify that a block with constraint value at limit minus one is accepted (expect success).  |        |       |
| `block_level_constraint/test/boundary/exact` | Verify that a block with constraint value exactly at limit is accepted (expect success).    |        |       |
| `block_level_constraint/test/boundary/over` | Verify that a block with constraint value at limit plus one is rejected (expect exception). |        |       |

#### Content Variations

Verify the constraint behaves correctly with different block contents that may affect the constraint calculation.

| ID                                        | Description                                                                                                                               | Status | Tests |
| ----------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- | ------ | ----- |
| `block_level_constraint/test/content/transaction_types` | Verify constraint behavior with all supported transaction types in the block. |        |       |
| `block_level_constraint/test/content/logs` | Verify constraint behavior when transactions emit logs. |        |       |
| `block_level_constraint/test/content/receipts` | Verify constraint behavior with varying receipt sizes. |        |       |
| `block_level_constraint/test/content/withdrawals` | Verify constraint behavior with non-empty withdrawals list. |        |       |

#### Fork Transition

| ID                                        | Description                                                                                                                               | Status | Tests |
| ----------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- | ------ | ----- |
| `block_level_constraint/test/fork_transition/accepted_before_fork` | Verify that a block before the activation fork is accepted even when the new constraint is not met. |        |       |
| `block_level_constraint/test/fork_transition/accepted_after_fork` | Verify that a block after the activation fork is accepted when the new constraint is met. |        |       |
| `block_level_constraint/test/fork_transition/rejected_after_fork` | Verify that a block after the activation fork is rejected when the new constraint is not met. |        |       |

Note: All test cases must use off-by-one values to ensure proper boundary condition verification.

### Framework Changes

- Introduce the constraint as a fork method that returns:
    - `None` for forks before its activation.
    - A non-`None` value starting from the fork where the constraint becomes active.
