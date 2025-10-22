# Using and Extending Fork Methods

This document describes the Fork class in the Ethereum execution spec tests framework, which provides a standardized way to define properties of Ethereum forks. Understanding how to use and extend these fork methods is essential for writing flexible tests that can automatically adapt to different forks.

## Overview

The `BaseFork` class is an abstract base class that defines the interface for all Ethereum forks. Each implemented fork (like Frontier, Homestead, etc.) extends this class and implements its abstract methods to provide fork-specific behavior.

The fork system allows:

1. Defining fork-specific behaviors and parameters
2. Comparing forks chronologically (`Paris < Shanghai`)
3. Supporting automatic fork transitions
4. Writing tests that automatically adapt to different forks

## Using Fork Methods in Tests

Fork methods are powerful tools that allow your tests to adapt to different Ethereum forks automatically. Here are common patterns for using them:

### 1. Check Fork Support for Features

```python
def test_some_feature(fork):
    if fork.supports_blobs(block_number=0, timestamp=0):
        # Test blob-related functionality
        ...
    else:
        # Test alternative or skip
        pytest.skip("Fork does not support blobs")
```

### 2. Get Fork-Specific Parameters

```python
def test_transaction_gas(fork, state_test):
    gas_cost = fork.gas_costs(block_number=0, timestamp=0).G_TRANSACTION
    
    # Create a transaction with the correct gas parameters for this fork
    tx = Transaction(
        gas_limit=gas_cost + 10000,
        # ...
    )
    
    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        # ...
    )
```

### 3. Determine Valid Transaction Types

```python
def test_transaction_types(fork, state_test):
    for tx_type in fork.tx_types(block_number=0, timestamp=0):
        # Test each transaction type supported by this fork
        # ...
```

### 4. Determine Valid Opcodes

```python
def test_opcodes(fork, state_test):
    # Create bytecode using only opcodes valid for this fork
    valid_opcodes = fork.valid_opcodes()
    
    # Use these opcodes to create test bytecode
    # ...
```

### 5. Test Fork Transitions

```python
def test_fork_transition(transition_fork, blockchain_test):
    # The transition_fork is a special fork type that changes behavior
    # based on block number or timestamp
    fork_before = transition_fork.fork_at(block_number=4, timestamp=0)
    fork_after = transition_fork.fork_at(block_number=5, timestamp=0)
    
    # Test behavior before and after transition
    # ...
```

## Important Fork Methods

### Header Information

These methods determine what fields are required in block headers for a given fork:

```python
fork.header_base_fee_required(block_number=0, timestamp=0)  # Added in London
fork.header_prev_randao_required(block_number=0, timestamp=0)  # Added in Paris
fork.header_withdrawals_required(block_number=0, timestamp=0)  # Added in Shanghai
fork.header_excess_blob_gas_required(block_number=0, timestamp=0)  # Added in Cancun
fork.header_blob_gas_used_required(block_number=0, timestamp=0)  # Added in Cancun
fork.header_beacon_root_required(block_number=0, timestamp=0)  # Added in Cancun
fork.header_requests_required(block_number=0, timestamp=0)  # Added in Prague
```

### Gas Parameters

Methods for determining gas costs and calculations:

```python
fork.gas_costs(block_number=0, timestamp=0)  # Returns a GasCosts dataclass
fork.memory_expansion_gas_calculator(block_number=0, timestamp=0)  # Returns a callable
fork.transaction_intrinsic_cost_calculator(block_number=0, timestamp=0)  # Returns a callable
```

### Transaction Types

Methods for determining valid transaction types:

```python
fork.tx_types(block_number=0, timestamp=0)  # Returns list of supported transaction types
fork.contract_creating_tx_types(block_number=0, timestamp=0)  # Returns list of tx types that can create contracts 
fork.precompiles(block_number=0, timestamp=0)  # Returns list of precompile addresses
fork.system_contracts(block_number=0, timestamp=0)  # Returns list of system contract addresses
```

### EVM Features

Methods for determining EVM features and valid opcodes:

```python
fork.evm_code_types(block_number=0, timestamp=0)  # Returns list of supported code types (e.g., Legacy, EOF)
fork.valid_opcodes()  # Returns list of valid opcodes for this fork
fork.call_opcodes(block_number=0, timestamp=0)  # Returns list of call opcodes with their code types
fork.create_opcodes(block_number=0, timestamp=0)  # Returns list of create opcodes with their code types
```

### Blob-related Methods (Cancun+)

Methods for blob transaction support:

```python
fork.supports_blobs(block_number=0, timestamp=0)  # Returns whether blobs are supported
fork.blob_gas_price_calculator(block_number=0, timestamp=0)  # Returns a callable
fork.excess_blob_gas_calculator(block_number=0, timestamp=0)  # Returns a callable
fork.min_base_fee_per_blob_gas(block_number=0, timestamp=0)  # Returns minimum base fee per blob gas
fork.blob_gas_per_blob(block_number=0, timestamp=0)  # Returns blob gas per blob
fork.target_blobs_per_block(block_number=0, timestamp=0)  # Returns target blobs per block
fork.max_blobs_per_block(block_number=0, timestamp=0)  # Returns max blobs per block
```

### Meta Information

Methods for fork identification and comparison:

```python
fork.name()  # Returns the name of the fork
fork.transition_tool_name(block_number=0, timestamp=0)  # Returns name for transition tools
fork.is_deployed()  # Returns whether the fork is deployed to mainnet
```

## Fork Transitions

The framework supports creating transition forks that change behavior at specific block numbers or timestamps:

```python
@transition_fork(to_fork=Shanghai, at_timestamp=15_000)
class ParisToShanghaiAtTime15k(Paris):
    """Paris to Shanghai transition at Timestamp 15k."""
    pass
```

With transition forks, you can test how behavior changes across fork boundaries:

```python
# Behavior changes at block 5
fork = BerlinToLondonAt5
assert not fork.header_base_fee_required(block_number=4)  # Berlin doesn't require base fee
assert fork.header_base_fee_required(block_number=5)      # London requires base fee
```

## Adding New Fork Methods

When adding new fork methods, follow these guidelines:

1. **Abstract Method Definition**: Add the new abstract method to `BaseFork` in `base_fork.py`
2. **Consistent Parameter Pattern**: Use `block_number` and `timestamp` parameters with default values
3. **Method Documentation**: Add docstrings explaining the purpose and behavior
4. **Implementation in Subsequent Forks**: Implement the method in every subsequent fork class **only** if the fork updates the value from previous forks.

Example of adding a new method:

```python
@classmethod
@abstractmethod
def supports_new_feature(cls, *, block_number: int = 0, timestamp: int = 0) -> bool:
    """Return whether the given fork supports the new feature."""
    pass
```

Implementation in a fork class:

```python
@classmethod
def supports_new_feature(cls, *, block_number: int = 0, timestamp: int = 0) -> bool:
    """Return whether the given fork supports the new feature."""
    return False  # Frontier doesn't support this feature
```

Implementation in a newer fork class:

```python
@classmethod
def supports_new_feature(cls, *, block_number: int = 0, timestamp: int = 0) -> bool:
    """Return whether the given fork supports the new feature."""
    return True  # This fork does support the feature
```

## When to Add a New Fork Method

Add a new fork method when:

1. **A New EIP Introduces a Feature**: Add methods describing the new feature's behavior
2. **Tests Need to Behave Differently**: When tests need to adapt to different fork behaviors
3. **Common Fork Information is Needed**: When multiple tests need the same fork-specific information
4. **Intrinsic Fork Properties Change**: When gas costs, opcodes, or other intrinsic properties change

Do not add a new fork method when:

1. The information is only needed for one specific test
2. The information is not directly related to fork behavior
3. The information can be calculated using existing methods

## Best Practices

1. **Use Existing Methods**: Check if there's already a method that provides the information you need
2. **Name Methods Clearly**: Method names should clearly describe what they return
3. **Document Behavior**: Include clear docstrings explaining the method's purpose and return value
4. **Avoid Hard-coding**: Use fork methods in tests instead of hard-coding fork-specific behavior
5. **Test Transitions**: Ensure your method works correctly with transition forks

## Example: Complete Test Using Fork Methods

Here's an example of a test that fully utilizes fork methods to adapt its behavior:

```python
def test_transaction_with_fork_adaptability(fork, state_test):
    # Prepare pre-state
    pre = Alloc()
    sender = pre.fund_eoa()
    
    # Define transaction based on fork capabilities
    tx_params = {
        "gas_limit": 1_000_000,
        "sender": sender,
    }
    
    # Add appropriate transaction type based on fork
    tx_types = fork.tx_types(block_number=0, timestamp=0)
    if 3 in tx_types and fork.supports_blobs(block_number=0, timestamp=0):
        # EIP-4844 blob transaction (type 3)
        tx_params["blob_versioned_hashes"] = [Hash.generate_zero_hashes(1)[0]]
    elif 2 in tx_types:
        # EIP-1559 transaction (type 2)
        tx_params["max_fee_per_gas"] = 10
        tx_params["max_priority_fee_per_gas"] = 1
    elif 1 in tx_types:
        # EIP-2930 transaction (type 1)
        tx_params["access_list"] = []
        
    # Create and run the test
    tx = Transaction(**tx_params)
    
    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
        },
    )
```

## Conclusion

The Fork class is a powerful abstraction that allows tests to adapt to different Ethereum forks. By using fork methods consistently, you can write tests that automatically handle fork-specific behavior, making your tests more maintainable and future-proof.

When adding new fork methods, keep them focused, well-documented, and implement them across all forks. This will ensure that all tests can benefit from the information and that transitions between forks are handled correctly.
