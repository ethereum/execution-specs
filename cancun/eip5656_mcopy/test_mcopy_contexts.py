"""
abstract: Tests [EIP-5656: MCOPY - Memory copying instruction](https://eips.ethereum.org/EIPS/eip-5656)
    Test memory copy under different call contexts [EIP-5656: MCOPY - Memory copying instruction](https://eips.ethereum.org/EIPS/eip-5656)

"""  # noqa: E501
from itertools import cycle, islice
from typing import Mapping

import pytest

from ethereum_test_tools import Account, Address, Alloc, Bytecode, Environment
from ethereum_test_tools import Opcodes as Op
from ethereum_test_tools import StateTestFiller, Storage, Transaction, ceiling_division

from .common import REFERENCE_SPEC_GIT_PATH, REFERENCE_SPEC_VERSION

REFERENCE_SPEC_GIT_PATH = REFERENCE_SPEC_GIT_PATH
REFERENCE_SPEC_VERSION = REFERENCE_SPEC_VERSION


@pytest.fixture
def initial_memory_length() -> int:  # noqa: D103
    return 0x400


@pytest.fixture
def callee_bytecode(
    initial_memory_length: int,
    call_opcode: Op,
) -> Bytecode:
    """
    Callee simply performs mcopy operations that should not have any effect on the
    caller context.
    """
    bytecode = Bytecode()

    # Perform some copy operations
    bytecode += Op.MCOPY(0x00, 0x01, 0x01)
    bytecode += Op.MCOPY(0x01, 0x00, 0x01)
    bytecode += Op.MCOPY(0x01, 0x00, 0x20)
    # And a potential memory cleanup
    bytecode += Op.MCOPY(0x00, initial_memory_length, initial_memory_length)
    # Also try to expand the memory
    bytecode += Op.MCOPY(0x00, initial_memory_length * 2, 1)
    bytecode += Op.MCOPY(initial_memory_length * 2, 0x00, 1)

    if call_opcode != Op.STATICCALL and call_opcode != Op.EXTSTATICCALL:
        # Simple sstore to make sure we actually ran the code
        bytecode += Op.SSTORE(200_000, 1)

    # In case of initcode, return empty code
    bytecode += Op.RETURN(0x00, 0x00)

    return bytecode


@pytest.fixture
def initial_memory(
    callee_bytecode: Bytecode,
    initial_memory_length: int,
    call_opcode: Op,
) -> bytes:
    """
    Initial memory for the test.
    """
    assert len(callee_bytecode) <= initial_memory_length

    ret = bytes(list(islice(cycle(range(0x01, 0x100)), initial_memory_length)))

    if call_opcode in [Op.CREATE, Op.CREATE2]:
        # We also need to put the callee_bytecode as initcode in memory for create operations
        ret = bytes(callee_bytecode) + ret[len(callee_bytecode) :]

    assert len(ret) == initial_memory_length
    return ret


@pytest.fixture
def caller_storage() -> Storage:  # noqa: D103
    return Storage()


@pytest.fixture
def caller_bytecode(
    initial_memory: bytes,
    callee_address: Address,
    callee_bytecode: Bytecode,
    call_opcode: Op,
    caller_storage: Storage,
) -> Bytecode:
    """
    Prepares the bytecode and storage for the test, based on the starting memory and the final
    memory that resulted from the copy.
    """
    bytecode = Bytecode()

    # Fill memory with initial values
    for i in range(0, len(initial_memory), 0x20):
        bytecode += Op.MSTORE(i, Op.PUSH32(initial_memory[i : i + 0x20]))

    # Perform the call to the contract that is going to perform mcopy
    if call_opcode in [Op.CREATE, Op.CREATE2]:
        bytecode += call_opcode(size=len(callee_bytecode))
    else:
        bytecode += call_opcode(address=callee_address)

    # First save msize
    bytecode += Op.SSTORE(100_000, Op.MSIZE())
    caller_storage[100_000] = ceiling_division(len(initial_memory), 0x20) * 0x20

    # Store all memory in the initial range to verify the MCOPY in the subcall did not affect
    # this level's memory
    for w in range(0, len(initial_memory) // 0x20):
        bytecode += Op.SSTORE(w, Op.MLOAD(w * 0x20))
        caller_storage[w] = initial_memory[w * 0x20 : w * 0x20 + 0x20]

    return bytecode


@pytest.fixture
def caller_address(pre: Alloc, caller_bytecode) -> Address:  # noqa: D103
    return pre.deploy_contract(caller_bytecode)


@pytest.fixture
def callee_address(pre: Alloc, callee_bytecode) -> Address:  # noqa: D103
    return pre.deploy_contract(callee_bytecode)


@pytest.fixture
def tx(pre: Alloc, caller_address: Address) -> Transaction:  # noqa: D103
    return Transaction(
        sender=pre.fund_eoa(),
        to=caller_address,
        gas_limit=1_000_000,
    )


@pytest.fixture
def post(  # noqa: D103
    caller_address: Address,
    caller_storage: Storage,
    callee_address: Address,
    call_opcode: Op,
) -> Mapping:
    callee_storage: Storage.StorageDictType = {}
    if call_opcode in [Op.DELEGATECALL, Op.CALLCODE, Op.EXTDELEGATECALL]:
        caller_storage[200_000] = 1
    elif call_opcode in [Op.CALL, Op.EXTCALL]:
        callee_storage[200_000] = 1
    return {
        caller_address: Account(storage=caller_storage),
        callee_address: Account(storage=callee_storage),
    }


@pytest.mark.with_all_call_opcodes
@pytest.mark.valid_from("Cancun")
def test_no_memory_corruption_on_upper_call_stack_levels(
    state_test: StateTestFiller,
    pre: Alloc,
    post: Mapping[str, Account],
    tx: Transaction,
):
    """
    Perform a subcall with any of the following opcodes, which uses MCOPY during its execution,
    and verify that the caller's memory is unaffected
    """
    state_test(
        env=Environment(),
        pre=pre,
        post=post,
        tx=tx,
    )


@pytest.mark.parametrize(
    "call_opcode",
    [
        Op.CREATE,
        Op.CREATE2,
    ],
)
@pytest.mark.valid_from("Cancun")
def test_no_memory_corruption_on_upper_create_stack_levels(
    state_test: StateTestFiller,
    pre: Alloc,
    post: Mapping[str, Account],
    tx: Transaction,
):
    """
    Perform a subcall with any of the following opcodes, which uses MCOPY during its execution,
    and verify that the caller's memory is unaffected:
      - `CREATE`
      - `CREATE2`

    TODO: [EOF] Add EOFCREATE opcode
    """
    state_test(
        env=Environment(),
        pre=pre,
        post=post,
        tx=tx,
    )
