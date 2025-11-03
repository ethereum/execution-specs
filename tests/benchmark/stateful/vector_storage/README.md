# Vector Storage Benchmark

Single contract design for minimal-overhead storage benchmarking with parametrized operations.

## Design Philosophy

This implementation uses **ONE contract** that:
- Is pre-deployed with 500 filled storage slots
- Accepts parameters via calldata for flexible operation
- Performs storage operations with minimal loop overhead (~30-40 gas per slot)

## Contract Architecture

### Calldata Layout (32-byte aligned)
```
Bytes 0-31:   Number of slots to write (uint256)
Bytes 32-63:  Starting slot index (uint256)
Bytes 64-95:  Value to write (uint256)
```

### Pre-deployed State
- **500 slots** pre-filled with value `0xDEADBEEF`
- Enables testing all transition types without redeployment
- Single contract instance for all benchmarks

## Three Test Scenarios

### 1. Cold Write (0 → non-zero)
- **Start**: Slot 500 (beyond prefilled range)
- **Operation**: Write new value to empty slots
- **Gas Cost**: ~20,000 gas per slot (most expensive)
- **Use Case**: Initial storage allocation

### 2. Storage Clear (non-zero → 0)
- **Start**: Slot 0 (within prefilled range)
- **Operation**: Write zeros to clear existing values
- **Gas Cost**: ~2,900 gas per slot + refund
- **Use Case**: Storage cleanup/deletion

### 3. Warm Update (non-zero → non-zero)
- **Start**: Slot 0 (within prefilled range)
- **Operation**: Update existing values
- **Gas Cost**: ~2,900 gas per slot
- **Use Case**: Typical storage updates

## Implementation Details

### Loop Overhead Breakdown
```
Per iteration:
- DUP operations: 12 gas (4 × 3 gas)
- ADD operation: 3 gas
- LT comparison: 3 gas
- ISZERO: 3 gas
- JUMPI/JUMP: 18 gas (8 + 10)
- SSTORE: Variable (based on transition)
Total overhead: ~39 gas per slot
```

### Contract Size
- Basic loop contract: ~100 bytes
- Well under EIP-3860 limit (24,576 bytes)
- Can handle thousands of operations per call

## Gas Cost Summary

| Transition Type | Gas per Slot | Notes |
|----------------|--------------|-------|
| 0 → non-zero | 20,000 | Cold slot, initial write |
| non-zero → 0 | 2,900 + refund | Max 20% refund of total gas |
| non-zero → non-zero | 2,900 | Warm slot update |
| Loop overhead | ~39 | Minimal per-slot overhead |

## Running the Benchmarks

### Generate Test Fixtures
```bash
# Run benchmarks with stateful marker
uv run fill tests/benchmark/stateful/vector_storage/test_vector_storage.py \
  -m stateful --fork Prague
```

### Execute Against Client
```bash
# Direct execution
uv run consume direct --input fixtures/ --client-bin /path/to/geth

# Via Engine API
uv run consume engine --input fixtures/ --engine-endpoint http://localhost:8551
```

## Advantages Over Multiple Contracts

1. **Single Deployment**: One contract handles all scenarios
2. **Consistent Overhead**: Same loop structure for all operations
3. **Flexible Testing**: Parametrized via calldata
4. **Realistic Patterns**: Mimics real smart contract storage patterns
5. **Accurate Benchmarking**: Minimal overhead ensures accurate gas measurements

## Test Parameters

- **num_slots**: [1, 10, 50, 100, 200] - Number of slots per operation
- **batch_size**: [10, 25, 50] - For batch operation tests
- **Pre-filled slots**: 500 - Consistent across all tests

## Example Usage

The contract can be called with raw calldata:
```python
# Write 100 values starting at slot 500
calldata = (
    (100).to_bytes(32, 'big') +  # num_slots
    (500).to_bytes(32, 'big') +  # start_slot
    (0x1234).to_bytes(32, 'big') # value
)
```

This design provides the most accurate storage benchmarking with minimal overhead and maximum flexibility.