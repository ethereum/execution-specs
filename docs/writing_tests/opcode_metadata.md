# Advanced: Opcode Metadata and Gas Calculations

## Overview

The execution testing package provides capabilities to calculate gas costs and refunds for individual opcodes and bytecode sequences based on their metadata. This is useful for:

- Writing tests that rely on exact gas consumption
- Creating gas benchmarking tests
- Validating gas cost calculations for specific opcode scenarios
- Future-proofing tests against breaking in upcoming forks that change gas rules

## Do Not Hand-Reconstruct Gas From Constants

Never build an expected gas amount by summing `fork.gas_costs()` constants (`NEW_ACCOUNT`, `CALL_VALUE`, `COLD_STORAGE_WRITE`, `VERY_LOW`, ...). Re-deriving the schedule by hand duplicates the framework's own calculation and silently breaks when a future fork reprices or restructures a cost. Always derive the expectation from a framework construct that tracks the live schedule:

- **The bytecode/opcode under test:** set the relevant metadata (see below) and read `bytecode.gas_cost(fork)` (execution + state), `.execution_cost(fork)`, `.state_cost(fork)`, or `.refund(fork)`. Link the exact opcode to the behavior, e.g. `Op.SELFDESTRUCT(account_new=True).state_cost(fork)`.
- **A single bare opcode/schedule cost** comes from a metadata-only opcode: `Op.BALANCE.with_metadata(address_warm=False).gas_cost(fork)` yields the cold account-access cost with no operand pushes.
- **Transaction-level costs:** `fork.transaction_intrinsic_cost_calculator()`, `fork.transaction_top_frame_state_gas(contract_creation=True)` (the created account's new-account state gas — on recent forks it is charged at the top frame, *not* in the intrinsic, so never subtract it from the intrinsic), `fork.transaction_data_floor_cost_calculator()`, and `fork.call_value_stipend()`.
- **Cross-fork / fork-transition comparisons:** evaluate the *same* bytecode or intrinsic at each fork (`before = fork.fork_at(timestamp=...)`, `after = ...`) and compare the resulting costs — do not compare raw schedule constants.

Additional rules:

- **Do not add "self-check" assertions** that compare a framework-computed value against a `fork.gas_costs()` decomposition of the same fork. They add no coverage over the runtime behavior the test already exercises and only break on repricing.
- **If the framework cannot express a cost, extend the framework** (wire the opcode into its gas/state map, add an accessor) rather than working around it in the test.
- **Exception:** a test whose *subject* is a specific schedule value — for example a regression asserting that an opcode's cost is unchanged across a fork — may compare a runtime measurement (`CodeGasMeasure`) against the fork's declared `fork.gas_costs().OPCODE_*` value. Even then, never hardcode the literal number.

## Opcode Metadata

Many opcodes accept metadata parameters that affect their gas cost calculations. Metadata represents runtime state information that influences gas consumption.

### Common Metadata Fields

#### Memory Expansion

Opcodes that can expand memory accept:

- `new_memory_size`: Memory size after the operation (in bytes)
- `old_memory_size`: Memory size before the operation (in bytes)

Example:

```python
Op.MSTORE(offset=0, value=0x123, new_memory_size=32, old_memory_size=0)
```

#### Account Access (Warm/Cold)

Opcodes that access accounts accept:

- `address_warm`: Whether the address is already warm (`True`) or cold (`False`)

Example:

```python
Op.BALANCE(address=0x1234, address_warm=True)   # Warm access: 100 gas
Op.BALANCE(address=0x1234, address_warm=False)  # Cold access: 2,600 gas
```

#### Storage Access

- `key_warm`: Whether the storage key is already warm
- `original_value`: The value the storage key had at the beginning of the transaction
- `current_value`: The value the storage key holds at the time the opcode is executed
- `new_value`: The value set by the opcode

Example:

```python
Op.SSTORE(key=1, value=0, key_warm=True, original_value=1, new_value=0)
```

#### Data Copy Operations

- `data_size`: Number of bytes being copied

Example:

```python
Op.CALLDATACOPY(dest_offset=0, offset=0, size=64, data_size=64, new_memory_size=64)
```

#### Contract Creation

- `init_code_size`: Size of the initialization code (affects CREATE/CREATE2 gas)

Example:

```python
Op.CREATE(value=0, offset=0, size=100, init_code_size=100, new_memory_size=100)
```

#### Call Operations

- `address_warm`: Whether the call target is warm
- `value_transfer`: Whether value is being transferred
- `account_new`: Whether creating a new account

Example:

```python
Op.CALL(
    gas=100000,
    address=0x5678,
    value=1,
    address_warm=False,
    value_transfer=True,
    account_new=True,
    new_memory_size=64
)
```

#### Return from Contract Creation

- `code_deposit_size`: Size of bytecode being deployed (only for RETURN in initcode)

Example:

```python
Op.RETURN(offset=0, size=100, code_deposit_size=100, new_memory_size=100)
```

#### Exponential Operation

- `exponent`: The exponent value (byte size calculated automatically)

Example:

```python
Op.EXP(a=2, exponent=0xFFFFFF)  # Gas based on exponent byte size
```

## Calculating Gas Costs

### For Individual Opcodes

Use the fork's `opcode_gas_calculator()` to get gas costs:

```python
from execution_testing import Op
from execution_testing.forks import Osaka

# Get the gas calculator for the fork
gas_calc = Osaka.opcode_gas_calculator()

# Calculate gas for a simple opcode
add_gas = gas_calc(Op.ADD)  # Returns 3 (G_VERY_LOW)

# Calculate gas for an opcode with metadata
mstore_gas = gas_calc(Op.MSTORE(new_memory_size=32))
# Returns: 3 (base) + memory_expansion_cost(32 bytes)

# Calculate gas for complex metadata
call_gas = gas_calc(
    Op.CALL(
        address_warm=False,
        value_transfer=True,
        account_new=True,
        new_memory_size=64
    )
)
# Returns: 2,600 (cold) + 9,000 (value) + 25,000 (new account) + memory_expansion_cost
```

### For Bytecode Sequences

Use the `bytecode.gas_cost(fork)` method:

```python
from execution_testing import Op
from execution_testing.forks import Osaka

# Simple bytecode
bytecode = Op.PUSH1(1) + Op.PUSH1(2) + Op.ADD
total_gas = bytecode.gas_cost(Osaka)
# Returns: 3 + 3 + 3 = 9

# With metadata
bytecode = Op.MSTORE(0, 1, new_memory_size=32) + Op.MLOAD(0)  # Last opcode does not expand the memory further
total_gas = bytecode.gas_cost(Osaka)
# Calculates total including memory expansion
```

### Fork-Specific Gas Costs

Gas costs can vary between forks. Always specify the fork when calculating:

```python
from execution_testing.forks import Shanghai, Osaka, Paris

# CREATE gas costs differ between forks (EIP-3860 in Shanghai)
create_op = Op.CREATE(init_code_size=100, new_memory_size=100)

shanghai_gas = create_op.gas_cost(Shanghai)
# Returns: 32,000 + (2 * 4 words) + memory_expansion = 32,008 + expansion

osaka_gas = create_op.gas_cost(Osaka)
# Same calculation, inherited from Shanghai

assert shanghai_gas == osaka_gas

paris_gas = create_op.gas_cost(Paris)
# Different calculation, prior to Shanghai the initcode was not metered

assert paris_gas != shanghai_gas
```

## Calculating Refunds

Some opcodes provide gas refunds. Currently, only `SSTORE` provides refunds when clearing storage.

### For Individual Opcodes

```python
from execution_testing import Op
from execution_testing.forks import Osaka

# Get the refund calculator
refund_calc = Osaka.opcode_refund_calculator()

# SSTORE clearing storage (non-zero → zero)
sstore_refund = refund_calc(
    Op.SSTORE(new_value=0, original_value=1)
)
# Returns: 4,800 (R_STORAGE_CLEAR)

# SSTORE not clearing storage
no_refund = refund_calc(
    Op.SSTORE(new_value=2, original_value=1)
)
# Returns: 0

# Other opcodes don't provide refunds
add_refund = refund_calc(Op.ADD)
# Returns: 0
```

### For Bytecode Sequences

Use the `bytecode.refund(fork)` method:

```python
from execution_testing import Op
from execution_testing.forks import Osaka

# Multiple SSTORE operations clearing storage
bytecode = (
    Op.SSTORE(0, 0, original_value=1, new_value=0) +
    Op.SSTORE(1, 0, original_value=1, new_value=0)
)
total_refund = bytecode.refund(Osaka)
# Returns: 4,800 + 4,800 = 9,600
```

## Writing Tests with Gas Calculations

### Example: Out-of-Gas Test Using Exact Gas Calculation

This example demonstrates a practical use case: testing that a subcall with insufficient gas fails correctly.

```python
import pytest
from execution_testing import (
    Account,
    Alloc,
    Environment,
    Fork,
    StateTestFiller,
    Transaction,
    Op,
)

@pytest.mark.valid_from("Byzantium")
def test_subcall_out_of_gas(
    state_test: StateTestFiller,
    fork: Fork,
    pre: Alloc,
    env: Environment,
):
    """
    Test that a subcall with exactly (gas_needed - 1) fails with out-of-gas,
    and verify via SSTORE that the operation didn't execute.
    """

    # Define the code that will run in the subcall
    # A simple SSTORE operation with known gas cost
    subcall_code = Op.SSTORE(
        slot=0,
        value=1,
        key_warm=False,  # Cold storage access
        new_value=1,
    ) + Op.STOP

    # Calculate exact gas needed for this operation in this fork
    subcall_gas_needed = subcall_code.gas_cost(fork)

    # Deploy contract that will be called
    callee = pre.deploy_contract(subcall_code)

    # Deploy caller contract that calls with insufficient gas
    caller = pre.deploy_contract(
        # Call with exactly 1 gas less than needed
        Op.SSTORE(
            slot=0,
            value=Op.CALL(
                gas=subcall_gas_needed - 1,  # Insufficient gas!
                address=callee,
                value=0,
                args_offset=0,
                args_size=0,
                ret_offset=0,
                ret_size=0,
            ),
        )
    )

    tx = Transaction(
        to=caller,
        gas_limit=500_000,
        sender=pre.fund_eoa(),
    )

    post = {
        caller: Account(
            storage={
                0: 0,  # CALL returns 0 on failure
            },
        ),
        callee: Account(
            storage={
                0: 0,  # SSTORE didn't execute due to OOG
            },
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
```

This example shows:

- **Practical Use**: Testing out-of-gas conditions requires knowing exact gas costs
- **Metadata Usage**: Using SSTORE metadata to calculate precise gas requirements
- **Verification**: Post-state checks confirm the subcall failed (storage unchanged)
- **Future-Proof**: Uses `gas_cost(fork)` so it adapts if gas calculations change

## Important Considerations

### 1. Most Tests Don't Need This

Most tests simply need to specify sufficient gas for the transaction to work and do not need to be exact. You typically only need explicit gas calculations when:

- Writing gas-focused benchmarks
- Verifying exact gas consumption for specific scenarios
- Testing edge cases in gas metering (off-by-one checks)

### 2. Metadata Must Match Runtime State

The metadata is not checked against the executed bytecode! When using metadata in tests, ensure the pre-state and transactions are accurately set up to reflect the bytecode metadata:

```python
# ❌ Incorrect: This is impossible because the first `Op.BALANCE` will always warm up the account:
Op.BALANCE(address=some_address, address_warm=False) + Op.BALANCE(address=some_address, address_warm=False)

# ✅ Correct: If the address was accessed earlier, it's warm:
Op.BALANCE(address=some_address, address_warm=False) + Op.BALANCE(address=some_address, address_warm=True)
```

Example using the test pre-conditions:

```python
# ✅ Correct: The address is in the access list, it's warm from the beginning:
code_address = pre.deploy_contract(Op.BALANCE(address=some_address, address_warm=True) + Op.BALANCE(address=some_address, address_warm=True))
...
tx = Transaction(
    to=code_address,
    gas_limit=500_000,
    sender=pre.fund_eoa(),
    access_list=[AccessList(address=code_address, storage_keys=[])]
)
```

### 3. Memory Size Calculations

Memory expansion is calculated from the highest offset accessed:

```python
# MSTORE to offset 0 requires 32 bytes of memory
Op.MSTORE(offset=0, value=0x123, new_memory_size=32)

# MSTORE to offset 32 requires 64 bytes total
Op.MSTORE(offset=32, value=0x456, new_memory_size=64, old_memory_size=32)
```

### 4. Fork Activation Matters

Some opcodes are only available in certain forks:

```python
# ✅ Available in Shanghai and later
Op.PUSH0.gas_cost(Shanghai)

# ❌ Not available in Paris
# Op.PUSH0.gas_cost(Paris)  # Would raise an error

# ✅ Available in Osaka and later
Op.CLZ.gas_cost(Osaka)
```

### 5. Refunds Are Limited

Only certain operations provide refunds:

- **SSTORE**: Refund when clearing storage (non-zero → zero)
- Most opcodes return 0 refund

Transaction-level operations like authorization lists also provide refunds, but these are handled at the transaction level, not in opcode metadata.

## See Also

- [Gas Optimization](./gas_optimization.md) - Optimizing test gas limits
- [Fork Methods](./fork_methods.md) - Using fork-specific methods
- [Writing Tests](./writing_a_new_test.md) - General test writing guide
