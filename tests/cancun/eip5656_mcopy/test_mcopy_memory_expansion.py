"""
Test MCOPY with memory expansion and potential OOG errors.

Test copy operations of [EIP-5656: MCOPY - Memory copying
instruction](https://eips.ethereum.org/EIPS/eip-5656) that produce
a memory expansion, and potentially an out-of-gas error.
"""

import itertools
from typing import List, Mapping

import pytest
from execution_testing import (
    AccessList,
    Account,
    Address,
    Alloc,
    Bytecode,
    Environment,
    Fork,
    Op,
    StateTestFiller,
    Transaction,
    TransactionReceipt,
)

from .common import REFERENCE_SPEC_GIT_PATH, REFERENCE_SPEC_VERSION

REFERENCE_SPEC_GIT_PATH = REFERENCE_SPEC_GIT_PATH
REFERENCE_SPEC_VERSION = REFERENCE_SPEC_VERSION

"""Storage addresses for common testing fields"""
_slot = itertools.count(1)
slot_code_worked = next(_slot)
slot_last_slot = next(_slot)

"""Storage values for common testing fields"""
value_code_worked = 0x2015


@pytest.fixture
def callee_bytecode(
    dest: int, src: int, length: int, initial_memory: bytes
) -> Bytecode:
    """Callee performs a single mcopy operation and then returns."""
    bytecode = Bytecode()

    # Copy the initial memory
    bytecode += Op.CALLDATACOPY(
        dest_offset=0x00,
        offset=0x00,
        size=Op.CALLDATASIZE,
        old_memory_size=0,
        new_memory_size=len(initial_memory),
        data_size=len(initial_memory),
    )

    # Pushes for the return operation
    bytecode += Op.PUSH1(0x00) + Op.PUSH1(0x00)

    bytecode += Op.SSTORE(slot_code_worked, value_code_worked)

    # Perform the mcopy operation
    new_memory_size = len(initial_memory)
    if dest + length > new_memory_size and length > 0:
        new_memory_size = dest + length
    bytecode += Op.MCOPY(
        dest,
        src,
        length,
        old_memory_size=len(initial_memory),
        new_memory_size=new_memory_size,
        data_size=length,
    )

    bytecode += Op.RETURN

    return bytecode


@pytest.fixture
def tx_access_list() -> List[AccessList]:
    """Access list for the transaction."""
    return [
        AccessList(address=Address(i), storage_keys=[]) for i in range(1, 10)
    ]


@pytest.fixture
def block_gas_limit(env: Environment) -> int:  # noqa: D103
    return env.gas_limit


@pytest.fixture
def tx_gas_limit(  # noqa: D103
    fork: Fork,
    callee_bytecode: Bytecode,
    block_gas_limit: int,
    successful: bool,
    initial_memory: bytes,
    tx_access_list: List[AccessList],
) -> int:
    tx_intrinsic_gas_cost_calculator = (
        fork.transaction_intrinsic_cost_calculator()
    )
    call_exact_cost = callee_bytecode.gas_cost(fork)
    return min(
        call_exact_cost
        - (0 if successful else 1)
        + tx_intrinsic_gas_cost_calculator(
            calldata=initial_memory, access_list=tx_access_list
        ),
        # If the transaction gas limit cap is not set (pre-osaka),
        # use the block gas limit
        fork.transaction_gas_limit_cap() or block_gas_limit,
    )


@pytest.fixture
def caller_address(pre: Alloc, callee_bytecode: bytes) -> Address:  # noqa: D103
    return pre.deploy_contract(code=callee_bytecode)


@pytest.fixture
def tx(  # noqa: D103
    sender: Address,
    caller_address: Address,
    initial_memory: bytes,
    tx_gas_limit: int,
    tx_access_list: List[AccessList],
) -> Transaction:
    return Transaction(
        sender=sender,
        to=caller_address,
        access_list=tx_access_list,
        data=initial_memory,
        gas_limit=tx_gas_limit,
        expected_receipt=TransactionReceipt(cumulative_gas_used=tx_gas_limit),
    )


@pytest.fixture
def post(  # noqa: D103
    caller_address: Address,
    successful: bool,
) -> Mapping:
    return {
        caller_address: Account(
            storage={slot_code_worked: value_code_worked} if successful else {}
        )
    }


@pytest.mark.parametrize(
    "dest,src,length",
    [
        (0x00, 0x00, 0x01),
        (0x100, 0x00, 0x01),
        (0x1F, 0x00, 0x01),
        (0x20, 0x00, 0x01),
        (0x1000, 0x00, 0x01),
        (0x1000, 0x00, 0x40),
        (0x00, 0x00, 0x00),
        (2**256 - 1, 0x00, 0x00),
        (0x00, 2**256 - 1, 0x00),
        (2**256 - 1, 2**256 - 1, 0x00),
    ],
    ids=[
        "single_byte_expansion",
        "single_byte_expansion_2",
        "single_byte_expansion_word_boundary",
        "single_byte_expansion_word_boundary_2",
        "multi_word_expansion",
        "multi_word_expansion_2",
        "zero_length_expansion",
        "huge_dest_zero_length",
        "huge_src_zero_length",
        "huge_dest_huge_src_zero_length",
    ],
)
@pytest.mark.parametrize("successful", [True, False])
@pytest.mark.parametrize(
    "initial_memory",
    [
        bytes(range(0x00, 0x100)),
        bytes(),
    ],
    ids=[
        "from_existent_memory",
        "from_empty_memory",
    ],
)
@pytest.mark.valid_from("Cancun")
def test_mcopy_memory_expansion(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    post: Mapping[str, Account],
    tx: Transaction,
) -> None:
    """
    Perform MCOPY operations that expand the memory, and verify the gas it
    costs to do so.
    """
    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
    )


@pytest.mark.parametrize(
    "dest,src,length",
    [
        (2**256 - 1, 0x00, 0x01),
        (2**256 - 2, 0x00, 0x01),
        (2**255 - 1, 0x00, 0x01),
        (0x00, 2**256 - 1, 0x01),
        (0x00, 2**256 - 2, 0x01),
        (0x00, 2**255 - 1, 0x01),
        (0x00, 0x00, 2**256 - 1),
        (0x00, 0x00, 2**256 - 2),
        (0x00, 0x00, 2**255 - 1),
    ],
    ids=[
        "max_dest_single_byte_expansion",
        "max_dest_minus_one_single_byte_expansion",
        "half_max_dest_single_byte_expansion",
        "max_src_single_byte_expansion",
        "max_src_minus_one_single_byte_expansion",
        "half_max_src_single_byte_expansion",
        "max_length_expansion",
        "max_length_minus_one_expansion",
        "half_max_length_expansion",
    ],
)
@pytest.mark.parametrize("successful", [False])
@pytest.mark.parametrize(
    "initial_memory",
    [
        bytes(range(0x00, 0x100)),
        bytes(),
    ],
    ids=[
        "from_existent_memory",
        "from_empty_memory",
    ],
)
@pytest.mark.valid_from("Cancun")
def test_mcopy_huge_memory_expansion(
    state_test: StateTestFiller,
    env: Environment,
    pre: Mapping[str, Account],
    post: Mapping[str, Account],
    tx: Transaction,
) -> None:
    """
    Perform MCOPY operations that expand the memory by huge amounts, and verify
    that it correctly runs out of gas.
    """
    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
    )
