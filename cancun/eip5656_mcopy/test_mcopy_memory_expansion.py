"""
abstract: Tests [EIP-5656: MCOPY - Memory copying instruction](https://eips.ethereum.org/EIPS/eip-5656)
    Test copy operations of [EIP-5656: MCOPY - Memory copying instruction](https://eips.ethereum.org/EIPS/eip-5656)
    that produce a memory expansion, and potentially an out-of-gas error.

"""  # noqa: E501
import itertools
from typing import Mapping

import pytest

from ethereum_test_forks import Fork
from ethereum_test_tools import Account, Address, Alloc, Bytecode, Environment
from ethereum_test_tools import Opcodes as Op
from ethereum_test_tools import StateTestFiller, Transaction

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
def callee_bytecode(dest: int, src: int, length: int) -> Bytecode:
    """
    Callee performs a single mcopy operation and then returns.
    """
    bytecode = Bytecode()

    # Copy the initial memory
    bytecode += Op.CALLDATACOPY(0x00, 0x00, Op.CALLDATASIZE())

    # Pushes for the return operation
    bytecode += Op.PUSH1(0x00) + Op.PUSH1(0x00)

    bytecode += Op.SSTORE(slot_code_worked, value_code_worked)

    # Perform the mcopy operation
    bytecode += Op.MCOPY(dest, src, length)

    bytecode += Op.RETURN

    return bytecode


@pytest.fixture
def call_exact_cost(
    fork: Fork,
    initial_memory: bytes,
    dest: int,
    length: int,
) -> int:
    """
    Returns the exact cost of the subcall, based on the initial memory and the length of the copy.
    """
    cost_memory_bytes = fork.memory_expansion_gas_calculator()
    gas_costs = fork.gas_costs()
    tx_intrinsic_gas_cost_calculator = fork.transaction_intrinsic_cost_calculator()

    mcopy_cost = 3
    mcopy_cost += 3 * ((length + 31) // 32)
    if length > 0 and dest + length > len(initial_memory):
        mcopy_cost += cost_memory_bytes(
            new_bytes=dest + length, previous_bytes=len(initial_memory)
        )

    calldatacopy_cost = 3
    calldatacopy_cost += 3 * ((len(initial_memory) + 31) // 32)
    calldatacopy_cost += cost_memory_bytes(new_bytes=len(initial_memory))

    pushes_cost = gas_costs.G_VERY_LOW * 9
    calldatasize_cost = gas_costs.G_BASE

    sstore_cost = 22100
    return (
        tx_intrinsic_gas_cost_calculator(calldata=initial_memory)
        + mcopy_cost
        + calldatacopy_cost
        + pushes_cost
        + calldatasize_cost
        + sstore_cost
    )


@pytest.fixture
def tx_max_fee_per_gas() -> int:  # noqa: D103
    return 7


@pytest.fixture
def block_gas_limit() -> int:  # noqa: D103
    return 100_000_000


@pytest.fixture
def tx_gas_limit(  # noqa: D103
    call_exact_cost: int,
    block_gas_limit: int,
    successful: bool,
) -> int:
    return min(call_exact_cost - (0 if successful else 1), block_gas_limit)


@pytest.fixture
def env(  # noqa: D103
    block_gas_limit: int,
) -> Environment:
    return Environment(gas_limit=block_gas_limit)


@pytest.fixture
def caller_address(pre: Alloc, callee_bytecode: bytes) -> Address:  # noqa: D103
    return pre.deploy_contract(code=callee_bytecode)


@pytest.fixture
def sender(pre: Alloc, tx_max_fee_per_gas: int, tx_gas_limit: int) -> Address:  # noqa: D103
    return pre.fund_eoa(tx_max_fee_per_gas * tx_gas_limit)


@pytest.fixture
def tx(  # noqa: D103
    sender: Address,
    caller_address: Address,
    initial_memory: bytes,
    tx_max_fee_per_gas: int,
    tx_gas_limit: int,
) -> Transaction:
    return Transaction(
        sender=sender,
        to=caller_address,
        data=initial_memory,
        gas_limit=tx_gas_limit,
        max_fee_per_gas=tx_max_fee_per_gas,
        max_priority_fee_per_gas=0,
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
@pytest.mark.with_all_evm_code_types
@pytest.mark.valid_from("Cancun")
def test_mcopy_memory_expansion(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    post: Mapping[str, Account],
    tx: Transaction,
):
    """
    Perform MCOPY operations that expand the memory, and verify the gas it costs to do so.
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
@pytest.mark.parametrize(
    "call_exact_cost",
    [2**128 - 1],
    ids=[""],
)  # Limit subcall gas, otherwise it would be impossibly large
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
@pytest.mark.with_all_evm_code_types
@pytest.mark.valid_from("Cancun")
def test_mcopy_huge_memory_expansion(
    state_test: StateTestFiller,
    env: Environment,
    pre: Mapping[str, Account],
    post: Mapping[str, Account],
    tx: Transaction,
):
    """
    Perform MCOPY operations that expand the memory by huge amounts, and verify that it correctly
    runs out of gas.
    """
    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
    )
