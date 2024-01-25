"""
abstract: Tests [EIP-5656: MCOPY - Memory copying instruction](https://eips.ethereum.org/EIPS/eip-5656)
    Test memory copy under different call contexts [EIP-5656: MCOPY - Memory copying instruction](https://eips.ethereum.org/EIPS/eip-5656)

"""  # noqa: E501
from itertools import cycle, islice
from typing import List, Mapping, Tuple

import pytest

from ethereum_test_tools import Account, Environment, OpcodeCallArg
from ethereum_test_tools import Opcodes as Op
from ethereum_test_tools import (
    StateTestFiller,
    Storage,
    TestAddress,
    Transaction,
    ceiling_division,
)

from .common import REFERENCE_SPEC_GIT_PATH, REFERENCE_SPEC_VERSION

# Code address used to call the test bytecode on every test case.
code_address = 0x100

# Code address of the callee contract
callee_address = 0x200


REFERENCE_SPEC_GIT_PATH = REFERENCE_SPEC_GIT_PATH
REFERENCE_SPEC_VERSION = REFERENCE_SPEC_VERSION


@pytest.fixture
def initial_memory_length() -> int:  # noqa: D103
    return 0x400


@pytest.fixture
def callee_bytecode(
    initial_memory_length: int,
    opcode: Op,
) -> bytes:
    """
    Callee simply performs mcopy operations that should not have any effect on the
    caller context.
    """
    bytecode = b""

    # Perform some copy operations
    bytecode += Op.MCOPY(0x00, 0x01, 0x01)
    bytecode += Op.MCOPY(0x01, 0x00, 0x01)
    bytecode += Op.MCOPY(0x01, 0x00, 0x20)
    # And a potential memory cleanup
    bytecode += Op.MCOPY(0x00, initial_memory_length, initial_memory_length)
    # Also try to expand the memory
    bytecode += Op.MCOPY(0x00, initial_memory_length * 2, 1)
    bytecode += Op.MCOPY(initial_memory_length * 2, 0x00, 1)

    if opcode != Op.STATICCALL:
        # Simple sstore to make sure we actually ran the code
        bytecode += Op.SSTORE(200_000, 1)

    # In case of initcode, return empty code
    bytecode += Op.RETURN(0x00, 0x00)

    return bytecode


@pytest.fixture
def initial_memory(
    callee_bytecode: bytes,
    initial_memory_length: int,
    opcode: Op,
) -> bytes:
    """
    Initial memory for the test.
    """
    assert len(callee_bytecode) <= initial_memory_length

    ret = bytes(list(islice(cycle(range(0x01, 0x100)), initial_memory_length)))

    if opcode in [Op.CREATE, Op.CREATE2]:
        # We also need to put the callee_bytecode as initcode in memory for create operations
        ret = callee_bytecode + ret[len(callee_bytecode) :]

    assert len(ret) == initial_memory_length
    return ret


@pytest.fixture
def caller_bytecode(
    callee_bytecode: bytes,
    opcode: Op,
) -> bytes:
    """
    Bytecode to be used by the top level call to make a successful call to the callee,
    or execute initcode.
    """
    args: List[OpcodeCallArg] = []
    if opcode in [Op.CALL, Op.CALLCODE]:
        args = [Op.GAS(), callee_address, 0, 0, 0, 0, 0]
    elif opcode in [Op.DELEGATECALL, Op.STATICCALL]:
        args = [Op.GAS(), callee_address, 0, 0, 0, 0]
    elif opcode in [Op.CREATE, Op.CREATE2]:
        # First copy the initcode that uses mcopy
        if opcode == Op.CREATE:
            args = [0, 0, len(callee_bytecode)]
        else:
            args = [0, 0, len(callee_bytecode), 0]

    return opcode(*args)


@pytest.fixture
def bytecode_storage(
    initial_memory: bytes,
    caller_bytecode: bytes,
) -> Tuple[bytes, Storage.StorageDictType]:
    """
    Prepares the bytecode and storage for the test, based on the starting memory and the final
    memory that resulted from the copy.
    """
    bytecode = b""
    storage: Storage.StorageDictType = {}

    # Fill memory with initial values
    for i in range(0, len(initial_memory), 0x20):
        bytecode += Op.MSTORE(i, Op.PUSH32(initial_memory[i : i + 0x20]))

    # Perform the call to the contract that is going to perform mcopy
    bytecode += caller_bytecode

    # First save msize
    bytecode += Op.SSTORE(100_000, Op.MSIZE())
    storage[100_000] = ceiling_division(len(initial_memory), 0x20) * 0x20

    # Store all memory in the initial range to verify the MCOPY in the subcall did not affect
    # this level's memory
    for w in range(0, len(initial_memory) // 0x20):
        bytecode += Op.SSTORE(w, Op.MLOAD(w * 0x20))
        storage[w] = initial_memory[w * 0x20 : w * 0x20 + 0x20]

    return (bytecode, storage)


@pytest.fixture
def pre(  # noqa: D103
    bytecode_storage: Tuple[bytes, Storage.StorageDictType],
    callee_bytecode: bytes,
) -> Mapping:
    return {
        TestAddress: Account(balance=10**40),
        code_address: Account(code=bytecode_storage[0]),
        callee_address: Account(code=callee_bytecode),
    }


@pytest.fixture
def tx() -> Transaction:  # noqa: D103
    return Transaction(
        to=code_address,
        gas_limit=1_000_000,
    )


@pytest.fixture
def post(  # noqa: D103
    bytecode_storage: Tuple[bytes, Storage.StorageDictType],
    opcode: Op,
) -> Mapping:
    caller_storage = bytecode_storage[1]
    callee_storage: Storage.StorageDictType = {}
    if opcode in [Op.DELEGATECALL, Op.CALLCODE]:
        caller_storage[200_000] = 1
    elif opcode in [Op.CALL]:
        callee_storage[200_000] = 1
    return {
        code_address: Account(storage=caller_storage),
        callee_address: Account(storage=callee_storage),
    }


@pytest.mark.parametrize(
    "opcode",
    [
        Op.CALL,
        Op.DELEGATECALL,
        Op.STATICCALL,
        Op.CALLCODE,
        Op.CREATE,
        Op.CREATE2,
    ],
)
@pytest.mark.valid_from("Cancun")
def test_no_memory_corruption_on_upper_call_stack_levels(
    state_test: StateTestFiller,
    pre: Mapping[str, Account],
    post: Mapping[str, Account],
    tx: Transaction,
):
    """
    Perform a subcall with any of the following opcodes, which uses MCOPY during its execution,
    and verify that the caller's memory is unaffected:
      - `CALL`
      - `CALLCODE`
      - `DELEGATECALL`
      - `STATICCALL`
      - `CREATE`
      - `CREATE2`
    """
    state_test(
        env=Environment(),
        pre=pre,
        post=post,
        tx=tx,
    )
