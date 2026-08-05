"""
Tests making the EEST-side `Spec` transcription of EIP-8297 constants
earn its keep.

`spec.py` keeps its own copy of these constants so a regression in the
implementation's values is caught here, rather than checked against
itself; nothing else compares the two.
"""

from ethereum_types.numeric import U32, U64, U256

from ethereum.binary_trie.embedding import (
    ACCOUNT_KEY_LENGTH,
    ACCOUNT_ZONE,
    BASIC_DATA_LEAF_KEY,
    CODE_HASH_LEAF_KEY,
    CODE_KEY_LENGTH,
    CODE_ZONE,
    HEADER_STORAGE_OFFSET,
    HEADER_STORAGE_SLOTS,
    PUSH1,
    PUSH32,
    PUSH_OFFSET,
    STEM_SUBTREE_WIDTH,
    STORAGE_KEY_LENGTH,
    STORAGE_ZONE,
    encode_basic_data,
)
from ethereum.binary_trie.trie import (
    BRANCH_NODE_TAG,
    LEAF_NODE_TAG,
    MAX_KEY_LENGTH,
)
from tests.binary_tree.eip8297_partitioned_binary_tree.spec import Spec


def test_spec_constants_match_implementation() -> None:
    """
    Every `Spec` constant that has a direct `ethereum.binary_trie`
    counterpart equals it.

    (`CODE_CHUNK_SIZE` has no named counterpart -- `31` is a bare
    literal in `chunkify_code`; BASIC_DATA offsets/widths are covered
    functionally, below, instead of by equality here.)

    Compared by explicit `==`, not rebuilt by keyword: `Spec`'s values
    must come from the EIP text, independent of whatever the
    implementation currently says.
    """
    assert Spec.BASIC_DATA_LEAF_KEY == BASIC_DATA_LEAF_KEY
    assert Spec.CODE_HASH_LEAF_KEY == CODE_HASH_LEAF_KEY
    assert Spec.HEADER_STORAGE_OFFSET == HEADER_STORAGE_OFFSET
    assert Spec.HEADER_STORAGE_SLOTS == HEADER_STORAGE_SLOTS
    assert Spec.STEM_SUBTREE_WIDTH == STEM_SUBTREE_WIDTH
    assert Spec.PUSH_OFFSET == PUSH_OFFSET
    assert Spec.PUSH1 == PUSH1
    assert Spec.PUSH32 == PUSH32
    assert Spec.ACCOUNT_ZONE == ACCOUNT_ZONE
    assert Spec.CODE_ZONE == CODE_ZONE
    assert Spec.STORAGE_ZONE == STORAGE_ZONE
    assert Spec.MAX_KEY_LENGTH == MAX_KEY_LENGTH
    assert Spec.ACCOUNT_KEY_LENGTH == ACCOUNT_KEY_LENGTH
    assert Spec.CODE_KEY_LENGTH == CODE_KEY_LENGTH
    assert Spec.STORAGE_KEY_LENGTH == STORAGE_KEY_LENGTH
    assert bytes([Spec.LEAF_TAG]) == LEAF_NODE_TAG
    assert bytes([Spec.BRANCH_TAG]) == BRANCH_NODE_TAG


def test_spec_header_offset_invariant_holds() -> None:
    """
    The EIP's stated invariant holds for the implementation's own
    constants.

    EIP text: "It is a required invariant that `HEADER_STORAGE_OFFSET
    + HEADER_STORAGE_SLOTS <= STEM_SUBTREE_WIDTH`." The header
    storage sweep and the storage-slot key split silently assume the
    header slots fit inside one stem's sub-index space.
    """
    assert (
        HEADER_STORAGE_OFFSET + HEADER_STORAGE_SLOTS <= STEM_SUBTREE_WIDTH
    )


def test_spec_basic_data_offsets_match_encode_basic_data() -> None:
    """
    Slicing a real `encode_basic_data` leaf with `Spec`'s transcribed
    BASIC_DATA offsets and widths recovers exactly the fields packed
    into it.

    `encode_basic_data` has no named offset constants to compare
    against directly, so this checks `Spec`'s offsets against real
    output instead. `code_size`, `nonce`, and `balance` each get a
    distinct, nonzero value so a wrong offset or width shows up as a
    mismatch; `version` and `reserved` are always zero, checked against
    that fixed value.
    """
    code_size_hex = "11223344"
    nonce_hex = "5566778899aabbcc"
    balance_hex = "0123456789abcdef0123456789abcdef"

    value = encode_basic_data(
        code_size=U32(int(code_size_hex, 16)),
        nonce=U64(int(nonce_hex, 16)),
        balance=U256(int(balance_hex, 16)),
    )

    def field(offset: int, width: int) -> bytes:
        return bytes(value[offset : offset + width])

    assert (
        field(Spec.BASIC_DATA_VERSION_OFFSET, Spec.BASIC_DATA_VERSION_WIDTH)
        == b"\x00"
    )
    assert (
        field(Spec.BASIC_DATA_RESERVED_OFFSET, Spec.BASIC_DATA_RESERVED_WIDTH)
        == b"\x00" * 3
    )
    assert field(
        Spec.BASIC_DATA_CODE_SIZE_OFFSET, Spec.BASIC_DATA_CODE_SIZE_WIDTH
    ) == bytes.fromhex(code_size_hex)
    assert field(
        Spec.BASIC_DATA_NONCE_OFFSET, Spec.BASIC_DATA_NONCE_WIDTH
    ) == bytes.fromhex(nonce_hex)
    assert field(
        Spec.BASIC_DATA_BALANCE_OFFSET, Spec.BASIC_DATA_BALANCE_WIDTH
    ) == bytes.fromhex(balance_hex)
    assert (
        Spec.BASIC_DATA_BALANCE_OFFSET + Spec.BASIC_DATA_BALANCE_WIDTH == 32
    ), "the widths must sum to the leaf's full 32 bytes"
