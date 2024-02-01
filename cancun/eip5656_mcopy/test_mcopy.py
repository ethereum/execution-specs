"""
abstract: Tests [EIP-5656: MCOPY - Memory copying instruction](https://eips.ethereum.org/EIPS/eip-5656)
    Test copy operations of [EIP-5656: MCOPY - Memory copying instruction](https://eips.ethereum.org/EIPS/eip-5656)

"""  # noqa: E501
from typing import Mapping, Tuple

import pytest
from ethereum.crypto.hash import keccak256

from ethereum_test_tools import Account, Environment, Hash
from ethereum_test_tools import Opcodes as Op
from ethereum_test_tools import (
    StateTestFiller,
    Storage,
    TestAddress,
    Transaction,
    ceiling_division,
)

from .common import REFERENCE_SPEC_GIT_PATH, REFERENCE_SPEC_VERSION, mcopy

# Code address used to call the test bytecode on every test case.
code_address = 0x100

REFERENCE_SPEC_GIT_PATH = REFERENCE_SPEC_GIT_PATH
REFERENCE_SPEC_VERSION = REFERENCE_SPEC_VERSION


@pytest.fixture
def initial_memory() -> bytes:
    """
    Initial memory for the test.
    """
    return bytes(range(0x00, 0x100))


@pytest.fixture
def final_memory(*, dest: int, src: int, length: int, initial_memory: bytes) -> bytes:
    """
    Memory after the MCOPY operation.
    """
    return mcopy(dest=dest, src=src, length=length, memory=initial_memory)


@pytest.fixture
def bytecode_storage(
    initial_memory: bytes,
    final_memory: bytes,
    dest: int,
    src: int,
    length: int,
) -> Tuple[bytes, Storage]:
    """
    Prepares the bytecode and storage for the test, based on the starting memory and the final
    memory that resulted from the copy.
    """
    bytecode = b""
    storage = Storage()

    # Fill memory with initial values
    for i in range(0, len(initial_memory), 0x20):
        bytecode += Op.MSTORE(i, Op.PUSH32(initial_memory[i : i + 0x20]))

    # Perform the MCOPY according to calldata values
    bytecode += Op.MCOPY(
        Op.CALLDATALOAD(0x00),
        Op.CALLDATALOAD(0x20),
        Op.CALLDATALOAD(0x40),
    )

    final_byte_length = ceiling_division(len(final_memory), 0x20) * 0x20
    # First save msize
    bytecode += Op.SSTORE(
        storage.store_next(final_byte_length),
        Op.MSIZE,
    )

    # Then save the hash of the entire memory
    bytecode += Op.SSTORE(
        storage.store_next(keccak256(final_memory.ljust(final_byte_length, b"\x00"))),
        Op.SHA3(0, Op.MSIZE),
    )

    # Store all memory in the initial range to verify the MCOPY
    for w in range(0, len(initial_memory) // 0x20):
        bytecode += Op.SSTORE(
            storage.store_next(final_memory[w * 0x20 : w * 0x20 + 0x20]),
            Op.MLOAD(w * 0x20),
        )

    # If the memory was extended beyond the initial range, store the last word of the resulting
    # memory into storage too
    if len(final_memory) > len(initial_memory):
        last_word = ceiling_division(len(final_memory), 0x20) - 1
        bytecode += Op.SSTORE(
            storage.store_next(
                final_memory[last_word * 0x20 : (last_word + 1) * 0x20].ljust(32, b"\x00")
            ),
            Op.MLOAD(last_word * 0x20),
        )

    return (bytecode, storage)


@pytest.fixture
def pre(bytecode_storage: Tuple[bytes, Storage]) -> Mapping:  # noqa: D103
    return {
        TestAddress: Account(balance=10**40),
        code_address: Account(code=bytecode_storage[0]),
    }


@pytest.fixture
def tx(dest: int, src: int, length: int) -> Transaction:  # noqa: D103
    return Transaction(
        to=code_address,
        data=Hash(dest) + Hash(src) + Hash(length),
        gas_limit=1_000_000,
    )


@pytest.fixture
def post(bytecode_storage: Tuple[bytes, Storage]) -> Mapping:  # noqa: D103
    return {
        code_address: Account(storage=bytecode_storage[1]),
    }


@pytest.mark.parametrize(
    "dest,src,length",
    [
        (0x00, 0x00, 0x00),
        (2**256 - 1, 0x00, 0x00),
        (0x00, 0x00, 0x01),
        (0x00, 0x00, 0x20),
        (0x01, 0x00, 0x01),
        (0x01, 0x00, 0x20),
        (0x11, 0x11, 0x01),
        (0x11, 0x11, 0x20),
        (0x11, 0x11, 0x40),
        (0x10, 0x00, 0x40),
        (0x00, 0x10, 0x40),
        (0x0F, 0x10, 0x40),
        (0x100, 0x01, 0x01),
        (0x100, 0x01, 0x20),
        (0x100, 0x01, 0x1F),
        (0x100, 0x01, 0x21),
        (0x00, 0x00, 0x100),
        (0x100, 0x00, 0x100),
        (0x200, 0x00, 0x100),
        (0x00, 0x100, 0x100),
        (0x100, 0x100, 0x01),
    ],
    ids=[
        "zero_inputs",
        "zero_length_out_of_bounds_destination",
        "single_byte_rewrite",
        "full_word_rewrite",
        "single_byte_forward_overwrite",
        "full_word_forward_overwrite",
        "mid_word_single_byte_rewrite",
        "mid_word_single_word_rewrite",
        "mid_word_multi_word_rewrite",
        "two_words_forward_overwrite",
        "two_words_backward_overwrite",
        "two_words_backward_overwrite_single_byte_offset",
        "single_byte_memory_extension",
        "single_word_memory_extension",
        "single_word_minus_one_byte_memory_extension",
        "single_word_plus_one_byte_memory_extension",
        "full_memory_rewrite",
        "full_memory_copy",
        "full_memory_copy_offset",
        "full_memory_clean",
        "out_of_bounds_memory_extension",
    ],
)
@pytest.mark.valid_from("Cancun")
def test_valid_mcopy_operations(
    state_test: StateTestFiller,
    pre: Mapping[str, Account],
    post: Mapping[str, Account],
    tx: Transaction,
):
    """
    Perform MCOPY operations using different offsets and lengths:
      - Zero inputs
      - Memory rewrites (copy from and to the same location)
      - Memory overwrites (copy from and to different locations)
      - Memory extensions (copy to a location that is out of bounds)
      - Memory clear (copy from a location that is out of bounds)
    """
    state_test(
        env=Environment(),
        pre=pre,
        post=post,
        tx=tx,
    )


@pytest.mark.parametrize("dest", [0x00, 0x20])
@pytest.mark.parametrize("src", [0x00, 0x20])
@pytest.mark.parametrize("length", [0x00, 0x01])
@pytest.mark.parametrize("initial_memory", [bytes()], ids=["empty_memory"])
@pytest.mark.valid_from("Cancun")
def test_mcopy_on_empty_memory(
    state_test: StateTestFiller,
    pre: Mapping[str, Account],
    post: Mapping[str, Account],
    tx: Transaction,
):
    """
    Perform MCOPY operations on an empty memory, using different offsets and lengths.
    """
    state_test(
        env=Environment(),
        pre=pre,
        post=post,
        tx=tx,
    )
