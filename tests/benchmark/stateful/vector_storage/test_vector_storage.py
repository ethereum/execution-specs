"""
abstract: Vector storage benchmark with single parametrized contract.

This test uses a single contract that accepts parameters via calldata to
benchmark different storage state transitions with minimal overhead:
- 0 -> non-zero (cold write to empty slots)
- non-zero -> non-zero (warm update of existing slots)
- non-zero -> 0 (clearing slots with gas refund)

The contract is pre-deployed with 500 filled slots to enable all scenarios.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytecode,
    Fork,
    Op,
    Storage,
    Transaction,
)

REFERENCE_SPEC_GIT_PATH = "DUMMY/vector_storage.md"
REFERENCE_SPEC_VERSION = "1.0"

# Pre-fill configuration
PREFILLED_SLOTS = 500
PREFILLED_VALUE = 0xDEADBEEF


def create_storage_contract() -> Bytecode:
    """
    Creates a storage benchmark contract that accepts parameters
    via calldata.

    Calldata layout (32-byte aligned):
    - Bytes 0-31: Number of slots to write
    - Bytes 32-63: Starting slot index
    - Bytes 64-95: Value to write

    The contract uses a minimal overhead loop to perform storage operations.
    Stack layout: [bottom] num_slots, start_slot, value, counter [top]
    """
    bytecode = Bytecode()

    # Load parameters from calldata
    bytecode += Op.PUSH1(0) + Op.CALLDATALOAD      # num_slots at bytes 0-31
    bytecode += Op.PUSH1(32) + Op.CALLDATALOAD     # start_slot at bytes 32-63
    bytecode += Op.PUSH1(64) + Op.CALLDATALOAD     # value at bytes 64-95

    # Initialize counter to 0
    bytecode += Op.PUSH1(0)                        # counter = 0

    # Main loop start (JUMPDEST at offset 11)
    bytecode += Op.JUMPDEST                        # Loop start marker

    # Check loop condition: counter < num_slots
    bytecode += Op.DUP4                            # Get num_slots (position 4 from top)
    bytecode += Op.DUP2                            # Duplicate counter (position 2 from top after DUP4)
    bytecode += Op.LT                              # counter < num_slots?
    bytecode += Op.ISZERO                          # Negate for JUMPI (jump if >=)

    # Jump to exit if counter >= num_slots
    bytecode += Op.PUSH1(31)                       # Push exit offset
    bytecode += Op.JUMPI                           # Exit if counter >= num_slots

    # Store operation: store value at (start_slot + counter)
    bytecode += Op.DUP1                            # Duplicate counter
    bytecode += Op.DUP4                            # Get start_slot (position 4 from top after DUP1)
    bytecode += Op.ADD                             # slot = start_slot + counter
    bytecode += Op.DUP3                            # Get value (position 3 from top after ADD)
    bytecode += Op.SWAP1                           # Put slot on top for SSTORE
    bytecode += Op.SSTORE                          # Store value at slot

    # Increment counter
    bytecode += Op.PUSH1(1)                        # Push 1
    bytecode += Op.ADD                             # counter++

    # Jump back to loop start
    bytecode += Op.PUSH1(11)                       # Push loop start offset
    bytecode += Op.JUMP                            # Jump to loop start

    # Exit point (JUMPDEST at offset 31)
    bytecode += Op.JUMPDEST                        # Exit marker
    bytecode += Op.STOP                            # Stop execution

    return bytecode


@pytest.mark.valid_from("Prague")
@pytest.mark.stateful  # Mark as stateful instead of benchmark
@pytest.mark.parametrize("num_slots", [1, 10, 50, 100, 200])
@pytest.mark.parametrize(
    "transition_type,start_offset,write_value",
    [
        # Write to empty slots (beyond the 500 prefilled)
        pytest.param(
            "zero_to_nonzero",
            PREFILLED_SLOTS,  # Start at slot 500
            0x1234,
            id="0_to_nonzero"
        ),

        # Clear existing slots (write 0 to prefilled slots)
        pytest.param(
            "nonzero_to_zero",
            0,  # Start at slot 0
            0,  # Write zeros
            id="nonzero_to_0"
        ),

        # Update existing slots (change value of prefilled slots)
        pytest.param(
            "nonzero_to_nonzero",
            0,  # Start at slot 0
            0xBEEFBEEF,  # Different value
            id="nonzero_to_nonzero"
        ),
    ],
)
def test_storage_transitions_benchmark(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    num_slots: int,
    transition_type: str,
    start_offset: int,
    write_value: int,
) -> None:
    """
    Benchmark storage operations using a single parametrized contract.

    The contract is pre-deployed with 500 filled slots and accepts
    parameters via calldata to perform different storage operations:

    1. 0 to nonzero: Writing to cold, empty slots (most expensive)
    2. nonzero to 0: Clearing existing slots (provides gas refund)
    3. nonzero to nonzero: Updating warm slots (moderate cost)
    """
    sender = pre.fund_eoa(10**18)

    # Pre-fill storage with 500 slots
    initial_storage = Storage()
    for i in range(PREFILLED_SLOTS):
        initial_storage[i] = PREFILLED_VALUE

    # Deploy the optimized contract with prefilled storage
    storage_contract = pre.deploy_contract(
        code=create_storage_contract(),
        storage=initial_storage,
    )

    # Prepare calldata with parameters
    calldata = (
        num_slots.to_bytes(32, 'big') +      # Number of slots to write
        start_offset.to_bytes(32, 'big') +   # Starting slot index
        write_value.to_bytes(32, 'big')      # Value to write
    )

    # Create transaction to call the contract
    # Use a reasonable gas limit that covers the operation
    # Each SSTORE costs up to 20,000 gas for cold writes plus overhead
    gas_limit = 21000 + (num_slots * 50000)  # Base tx cost + storage operations

    tx = Transaction(
        to=storage_contract,
        gas_limit=gas_limit,
        data=calldata,
        sender=sender,
    )

    # Calculate expected post-state storage
    expected_storage = Storage()

    # Start with the initial prefilled storage
    for i in range(PREFILLED_SLOTS):
        expected_storage[i] = PREFILLED_VALUE

    # Apply the storage modifications
    for i in range(num_slots):
        slot = start_offset + i

        if write_value == 0 and slot < PREFILLED_SLOTS:
            # Clearing a prefilled slot (nonzero->0)
            # Remove from expected storage (becomes 0)
            if slot in expected_storage:
                del expected_storage[slot]
        elif write_value != 0:
            # Writing a non-zero value
            expected_storage[slot] = write_value
        # If write_value == 0 and slot >= PREFILLED_SLOTS,
        # we're writing 0 to an already empty slot (no change)

    post = {
        storage_contract: Account(storage=expected_storage),
    }

    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[tx])],
        post=post,
    )


