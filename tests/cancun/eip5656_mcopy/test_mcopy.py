"""
Tests [EIP-5656: MCOPY - Memory copying instruction](https://eips.ethereum.org/EIPS/eip-5656).
"""

from typing import Mapping

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytecode,
    Environment,
    Hash,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
    ceiling_division,
    keccak256,
)

from .common import REFERENCE_SPEC_GIT_PATH, REFERENCE_SPEC_VERSION, mcopy

REFERENCE_SPEC_GIT_PATH = REFERENCE_SPEC_GIT_PATH
REFERENCE_SPEC_VERSION = REFERENCE_SPEC_VERSION


@pytest.fixture
def initial_memory() -> bytes:
    """Init memory for the test."""
    return bytes(range(0x00, 0x100))


@pytest.fixture
def final_memory(
    *, dest: int, src: int, length: int, initial_memory: bytes
) -> bytes:
    """Memory after the MCOPY operation."""
    return mcopy(dest=dest, src=src, length=length, memory=initial_memory)


@pytest.fixture
def code_storage() -> Storage:
    """Storage for the code contract."""
    return Storage()


@pytest.fixture
def code_bytecode(
    initial_memory: bytes,
    final_memory: bytes,
    code_storage: Storage,
) -> Bytecode:
    """
    Prepare bytecode and storage for the test, based on the starting memory and
    the final memory that resulted from the copy.
    """
    bytecode = Bytecode()

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
        code_storage.store_next(final_byte_length),
        Op.MSIZE,
    )

    # Then save the hash of the entire memory
    bytecode += Op.SSTORE(
        code_storage.store_next(
            keccak256(final_memory.ljust(final_byte_length, b"\x00"))
        ),
        Op.SHA3(0, Op.MSIZE),
    )

    # Store all memory in the initial range to verify the MCOPY
    for w in range(0, len(initial_memory) // 0x20):
        bytecode += Op.SSTORE(
            code_storage.store_next(final_memory[w * 0x20 : w * 0x20 + 0x20]),
            Op.MLOAD(w * 0x20),
        )

    # If the memory was extended beyond the initial range, store the last word
    # of the resulting memory into storage too
    if len(final_memory) > len(initial_memory):
        last_word = ceiling_division(len(final_memory), 0x20) - 1
        bytecode += Op.SSTORE(
            code_storage.store_next(
                final_memory[last_word * 0x20 : (last_word + 1) * 0x20].ljust(
                    32, b"\x00"
                )
            ),
            Op.MLOAD(last_word * 0x20),
        )

    return bytecode


@pytest.fixture
def code_address(pre: Alloc, code_bytecode: Bytecode) -> Address:
    """Address of the contract that is going to perform the MCOPY operation."""
    return pre.deploy_contract(code_bytecode)


@pytest.fixture
def tx(  # noqa: D103
    pre: Alloc, code_address: Address, dest: int, src: int, length: int
) -> Transaction:
    return Transaction(
        sender=pre.fund_eoa(),
        to=code_address,
        data=Hash(dest) + Hash(src) + Hash(length),
        gas_limit=1_000_000,
    )


@pytest.fixture
def post(code_address: Address, code_storage: Storage) -> Mapping:  # noqa: D103
    return {
        code_address: Account(storage=code_storage),
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
    pre: Alloc,
    post: Mapping[str, Account],
    tx: Transaction,
) -> None:
    """
    Perform MCOPY operations using different offsets and lengths.

      - Zero inputs
      - Memory rewrites (copy from and to the same location)
      - Memory overwrites (copy from and to different locations)
      - Memory extensions (copy to a location that is out of bounds)
      - Memory clear (copy from a location that is out of bounds).
    """
    state_test(
        env=Environment(),
        pre=pre,
        post=post,
        tx=tx,
    )


PATTERN = bytes.fromhex(
    "a0a1a2a3a4a5a6a7a8a9aaabacadaeafb0b1b2b3b4b5b6b7b8b9babbbcbdbebf"
)


@pytest.mark.parametrize(
    "dest,src,length",
    [
        pytest.param(0x1010, 0x0000, 0x0020, id="clear_low_half_0"),
        pytest.param(0x1020, 0x1010, 0x0010, id="clear_low_half_1"),
        pytest.param(0x1020, 0x1040, 0x0010, id="clear_low_half_2"),
        pytest.param(0x1030, 0x0000, 0x1020, id="clear_high_half_0"),
        pytest.param(0x1021, 0x1020, 0x0123, id="memmove_forward"),
        pytest.param(0x1020, 0x1023, 0x001D, id="memmove_backward"),
    ],
)
@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/Cancun/stEIP5656_MCOPY/MCOPY_memory_hashFiller.yml",  # noqa: E501
    ],
    pr=["https://github.com/ethereum/execution-specs/pull/2490"],
)
@pytest.mark.valid_from("Cancun")
def test_mcopy_repeated(
    state_test: StateTestFiller,
    pre: Alloc,
    dest: int,
    src: int,
    length: int,
) -> None:
    """
    Perform the same MCOPY twice and verify the memory hash after each.

    For non-overlapping or idempotent copies the hash is the same both
    times; for overlapping forward/backward moves the second copy
    operates on already-modified memory, so the hashes differ.
    """
    # Build initial memory: zeros with PATTERN at offset 0x1020.
    buf = bytearray(0x1020 + len(PATTERN))
    buf[0x1020 : 0x1020 + len(PATTERN)] = PATTERN
    initial = bytes(buf)

    # Compute memory after first and second MCOPY.
    after_first = mcopy(dest=dest, src=src, length=length, memory=initial)
    after_second = mcopy(dest=dest, src=src, length=length, memory=after_first)

    first_size = ceiling_division(len(after_first), 0x20) * 0x20
    second_size = ceiling_division(len(after_second), 0x20) * 0x20
    hash_first = keccak256(after_first.ljust(first_size, b"\x00"))
    hash_second = keccak256(after_second.ljust(second_size, b"\x00"))

    storage = Storage()

    # Build bytecode: fill memory, MCOPY, hash, MCOPY again, hash.
    code = Bytecode()
    code += Op.MSTORE(
        0x1020,
        Op.PUSH32(PATTERN),
    )
    code += Op.MCOPY(
        Op.CALLDATALOAD(0x00),
        Op.CALLDATALOAD(0x20),
        Op.CALLDATALOAD(0x40),
    )
    code += Op.SSTORE(
        storage.store_next(hash_first, "hash_after_first_mcopy"),
        Op.SHA3(0, Op.MSIZE),
    )
    code += Op.MCOPY(
        Op.CALLDATALOAD(0x00),
        Op.CALLDATALOAD(0x20),
        Op.CALLDATALOAD(0x40),
    )
    code += Op.SSTORE(
        storage.store_next(hash_second, "hash_after_second_mcopy"),
        Op.SHA3(0, Op.MSIZE),
    )

    contract = pre.deploy_contract(code)
    post = {contract: Account(storage=storage)}

    state_test(
        env=Environment(),
        pre=pre,
        post=post,
        tx=Transaction(
            sender=pre.fund_eoa(),
            to=contract,
            data=Hash(dest) + Hash(src) + Hash(length),
            gas_limit=1_000_000,
        ),
    )


@pytest.mark.parametrize("dest", [0x00, 0x20])
@pytest.mark.parametrize("src", [0x00, 0x20])
@pytest.mark.parametrize("length", [0x00, 0x01])
@pytest.mark.parametrize("initial_memory", [bytes()], ids=["empty_memory"])
@pytest.mark.valid_from("Cancun")
def test_mcopy_on_empty_memory(
    state_test: StateTestFiller,
    pre: Alloc,
    post: Mapping[str, Account],
    tx: Transaction,
) -> None:
    """
    Perform MCOPY operations on an empty memory, using different offsets and
    lengths.
    """
    state_test(
        env=Environment(),
        pre=pre,
        post=post,
        tx=tx,
    )
