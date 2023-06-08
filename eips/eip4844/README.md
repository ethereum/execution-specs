# 🧪 Execution Specification Test Cases

**Note:** *This is still a WIP but the tests can still be used by any client team. The priority levels (🔴, 🟠, 🟡, 🟢) represent very high, high, medium, low  priorities respectively.*

## 📖 Blobhash Opcode

Test Module - `eip4844/test_blobhash_opcode.py`

Verifies that the `BLOBHASH` opcode, works as intended for a variety of contexts, retrieves the blob versioned hash correctly for a given index, returns the correct zeroed `bytes32` value for out-of-range indices, and consumes the correct amount of gas.

**1) 🔴 test_blobhash_opcode_contexts():**

Tests that the `BLOBHASH` opcode functions correctly when called in different contexts including:
- `BLOBHASH` opcode on the top level of the call stack.
- `BLOBHASH` opcode on the max value.
- `BLOBHASH` opcode on `CALL`, `DELEGATECALL`, `STATICCALL`, and `CALLCODE`.
- `BLOBHASH` opcode on Initcode.
- `BLOBHASH` opcode on `CREATE` and `CREATE2`.
- `BLOBHASH` opcode on transaction types 0, 1 and 2.

**2) 🔴 test_blobhash_blob_versioned_hash():**

Tests that the `BLOBHASH` opcode returns the correct versioned hash for various valid indexes. This test covers various scenarios with random `blob_versioned_hash` values within the valid range `[0, 2**256-1]`.

**3) 🔴 test_blobhash_invalid_blob_index():**

Tests that the `BLOBHASH` opcode returns a zeroed `bytes32` value for invalid indexes. This test includes cases where the index is negative (`index < 0`) or exceeds the maximum number of `blob_versioned_hash` values stored (`index >= len(tx.message.blob_versioned_hashes)`). It confirms that the returned value is a zeroed `bytes32` value for these cases.

**4) 🟠 test_blobhash_gas_cost():**

Asserts the gas consumption of the `BLOBHASH` opcode is correct by ensuring it matches `HASH_OPCODE_GAS = 3`. It includes both valid and invalid random index sizes from the range `[0, 2**256-1]`, for tx types 2 and 3.

**5) 🟡 test_blobhash_multiple_txs_in_block():**

Tests that the `BLOBHASH` opcode returns the appropriate values when there is more than one blob tx type within a block (for tx types 2 and 3). Scenarios involve tx type 3 followed by tx type 2 running the same code within a block. In this case `BLOBHASH` returns 0, but for the opposite scenario `BLOBHASH` returns the correct `blob_versioned_hash`.


## 💽⛽💸 Excess Data Gas

Test Module - `eip4844/test_excess_data_gas.py`

Predominantly verifies that `excess_data_gas` & `data_gasprice` are calculated correctly ensuring both valid and invalid transactions are processed accordingly. Extra verification is added specifically for invalid blob transactions when the `max_fee_per_data_gas`, number of blobs or transaction type are erroneous. 

**1) 🔴 test_excess_data_gas_calculation():**

Tests that the `excess_data_gas` is calculated correctly within a single block for various contexts, where the `parent.excess_data_gas` and the proposed block `excess_data_gas` have a variety of values. The excess data gas is calculated using the following formula:

```python
def calc_excess_data_gas(parent_excess_data_gas: int, parent_blobs: int) -> int:
    """
    Calculate the excess data gas for a block given the parent excess data gas
    and the number of blobs in the block.
    """
    parent_consumed_data_gas = parent_blobs * DATA_GAS_PER_BLOB
    if parent_excess_data_gas + parent_consumed_data_gas < TARGET_DATA_GAS_PER_BLOCK:
        return 0
    else:
        return parent_excess_data_gas + parent_consumed_data_gas - TARGET_DATA_GAS_PER_BLOCK

```

For blocks to be valid in these contexts they must meet the following conditions of the EIP:
  - Each block can only have a maximum of `MAX_BLOBS_PER_BLOCK`.
  - A type 5 blob transaction must have at least one blob - `len(versioned_hashes) > 0`.
  - The user is open to paying the current data gasprice for the transaction -`tx.message.max_fee_per_data_gas >= get_data_gasprice(parent(block).header)`
  - The account used for the blob transaction must have enough balance - `signer(tx).balance >= tx.message.gas * tx.message.max_fee_per_gas + get_total_data_gas(tx) * tx.message.max_fee_per_data_gas`
  
**2) 🔴 test_invalid_excess_data_gas_in_header():**

Asserts that blocks with invalid `excess_data_gas` values in the header are ignored, ensuring the blob transaction is rejected and no state changes occur. The invalidity of `excess_data_gas` within a new block header is tested across the following scenarios:

- `excess_data_gas` decreases or increases by `TARGET_DATA_GAS_PER_BLOCK + 1` in a single block. Note that the EIP only allows `excess_data_gas` to decrease & increase by a maximum of `TARGET_DATA_GAS_PER_BLOCK`.

- `excess_data_gas` is **unchanged** when the number of blobs in the proposed block **doesn't** equal the `TARGET_BLOBS_PER_BLOCK`. If the number of blobs are different from the target, `excess_data_gas` must change. 

- `excess_data_gas` is **changed** when the number of blobs in the proposed block **does** equal the `TARGET_BLOBS_PER_BLOCK`. If the number of blobs are equal to the target,`excess_data_gas` must remain the same value - `parent_excess_data_gas`.

- `excess_data_gas` is less than the `TARGET_DATA_GAS_PER_BLOCK` when the parent has 0 blobs (`parent.excess_data_gas` = 0), and the calculated excess is non-zero. This is invalid as the first condition in the excess data gas calculation must be met, and hence return zero for this case. 

- `excess_data_gas` is a value greater than `2**256-1`. It must be a value that fits within 256-bits.

**3) 🔴 test_fork_transition_excess_data_gas_in_header():**

Tests that the `excess_data_gas` calculation is correct when transitioning from the Shanghai fork to the Cancun fork, where appended blocks are valid and state changes occur. Each block has a single transaction with `MAX_BLOBS_PER_BLOCK` blobs. The first block during the transition period has a parent of zero `excess_data_gas` in the header. Each block afterwards calculates `excess_data_gas` using the following `calc_excess_data_gas` function such that it continuously increases.

**4) 🔴 test_invalid_blob_txs():**

Asserts that blocks with invalid blob transactions are rejected and no state changes occur. This is tested across the following scenarios:

- `max_fee_per_data_gas` is less than the required `data_gasprice` for a set number of excess blobs. This is invalid as a valid block must obey the following condition:
  - `tx.message.max_fee_per_data_gas >= get_data_gasprice(parent(block).header)`

- `max_fee_per_data_gas` is greater than the required `data_gasprice` for a set number of excess blobs but the account doesn't have the required balance to cover the total cost of the transaction. A valid block must prove true for the following condition: 
  - `signer(tx).balance >= tx.message.gas * tx.message.max_fee_per_gas + get_total_data_gas(tx) * tx.message.max_fee_per_data_gas`

- `max_fee_per_data_gas` has an invalid value of zero. This value is invalid as it is less than `MIN_DATA_GASPRICE = 1`.

- `len(blobs)` is greater than `MAX_BLOBS_PER_BLOCK =  MAX_DATA_GAS_PER_BLOCK // DATA_GAS_PER_BLOB` in a single transaction within one block. There cannot be more than `MAX_BLOBS_PER_BLOCK` blobs in a block.

- `len(wrapper.tx.message)` is greater that `MAX_BLOBS_PER_BLOCK` but with `len(blobs) = 1` for each transaction. As before there cannot be more than `MAX_BLOBS_PER_BLOCK` blobs in a block.

- `len(blobs)` is zero within a transaction. Valid blob txs (type 3) must have at least one blob within it, obeying the following condition:
  - `len(tx.message.blob_versioned_hashes) > 0`

- Blob transaction type 3 is used in a pre-Cancun fork. This transaction type can only be used in a post-Cancun fork.

## 📖 Point Evaluation Precompile

Test Module - `eip4844/test_point_evaluation_precompile.py`

Verifies correct behavior on calls to the point evaluation precompile introduced by EIP-4844.

**1) 🔴 test_point_evaluation_precompile():**

- Correct Proof, verify call return values are `bytes32(FIELD_ELEMENTS_PER_BLOB) + bytes32(BLS_MODULUS)`
- Out of bounds Z value (equal to BLS_MODULUS)
- Out of bounds Y value (equal to BLS_MODULUS)
- Correct Proof, input length 1 byte too short
- Correct Proof, input length 47 bytes too short
- Correct Proof, input length 1 byte too long
- Correct Proof, input length 976 bytes too long
- Null length input
- Correct length input, but all zeros
- Correct length input, but all zeros except for versioned hash (correct)
- Correct Proof, but inverted endianness
- Correct Proof, but incorrect versioned hash version (0x00, 0x02, 0xFF)

Test also all vectors included in `eip4844/point_evaluation_vectors` in json format.

**2) 🔴 test_point_evaluation_precompile_calls():**
Test return values of the precompile contract using different call opcodes, and gas amounts.
- Test correct and incorrect point evaluations using CALL, DELEGATECALL, CALLCODE, STATICCALL
- Test using sufficient and insufficient gas (50,000 gas)

**3) 🔴 test_point_evaluation_precompile_gas_usage():**
Test gas consumption of a call to the precompile:
- Test 50,000 gas consumption on a correct evaluation
- Test 50,001+ gas consumption on a incorrect evaluation
- Test gas consumption using CALL, DELEGATECALL, CALLCODE, and STATICCALL opcodes
- Test full gas consumption on calls with less than 50,000 gas

**3) 🔴 test_point_evaluation_precompile_before_fork():**
Test sending an incorrect kzg proof point evaluation to the precompile address before and after the fork:
- Before the fork, the call must succeed
- After the fork, the call must fail