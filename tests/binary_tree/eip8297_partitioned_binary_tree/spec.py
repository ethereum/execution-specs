"""Defines EIP-8297 specification constants and functions."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """Reference specification."""

    git_path: str
    version: str


ref_spec_8297 = ReferenceSpec(
    git_path="EIPS/eip-8297.md",
    version="cc08f9602cd7ff7ed9bc281473eee0c979f368d8",
)


class Spec:
    """
    Parameters transcribed directly from the EIP-8297 specification text.

    These are NOT imported from `ethereum.binary_trie` (the
    implementation under test): keeping the two independent lets these
    tests catch a regression in the implementation's own constants
    instead of checking the implementation against itself.
    """

    # Header leaf sub-indices: which of the two fixed leaves in an
    # account's header stem a header value lives at (see "Header
    # values").
    BASIC_DATA_LEAF_KEY = 0
    CODE_HASH_LEAF_KEY = 1

    # Header stem layout: how many storage slots and code chunks are
    # co-located in the account header before overflowing into the
    # storage/code zones (see "Tree embedding").
    HEADER_STORAGE_OFFSET = 64
    CODE_OFFSET = 128
    STEM_SUBTREE_WIDTH = 256

    # Code chunking: the chunk size in bytes, and the opcode-value
    # offset used to recover a PUSH's data length when marking a
    # chunk's leading PUSHDATA bytes (see "Code").
    CODE_CHUNK_SIZE = 31
    PUSH_OFFSET = 95

    # Zone identifiers: the first byte of every key, partitioning the
    # tree into account headers, code, and storage (see "Zones").
    ACCOUNT_ZONE = 0x00
    CODE_ZONE = 0x01
    STORAGE_ZONE = 0xFF

    # Key length bounds: the overall cap on key length, and the fixed
    # length of every key produced by each zone's embedding (see
    # "Maximum key length" and "Tree embedding").
    MAX_KEY_LENGTH = 8192
    ACCOUNT_KEY_LENGTH = 34
    CODE_KEY_LENGTH = 34
    STORAGE_KEY_LENGTH = 66

    @classmethod
    def header_storage_sub_index(cls, slot: int) -> int:
        """
        Return the account header sub-index for storage `slot`.

        Only valid for `slot < CODE_OFFSET - HEADER_STORAGE_OFFSET`
        (slots 0..63), which live in the account header's stem rather
        than the storage zone (see "Storage").
        """
        return cls.HEADER_STORAGE_OFFSET + slot

    @classmethod
    def storage_group_index(cls, slot: int) -> int:
        """
        Return the storage group (`tree_index`) that `slot` belongs to.

        An aligned range of `STEM_SUBTREE_WIDTH` slots sharing one
        `tree_index` forms one storage group. Group 0 is the exception:
        slots 0..63 live in the header, so its storage-zone leaves are
        slots 64..255 only (see "Storage").
        """
        return slot // cls.STEM_SUBTREE_WIDTH

    @classmethod
    def storage_sub_index(cls, slot: int) -> int:
        """
        Return `slot`'s sub-index within its storage group.

        Applies to slots stored in the storage zone, i.e.
        `slot >= CODE_OFFSET - HEADER_STORAGE_OFFSET` (see "Storage").
        """
        return slot % cls.STEM_SUBTREE_WIDTH

    @classmethod
    def code_chunk_count(cls, code_size: int) -> int:
        """
        Return the number of chunks `chunkify_code` splits `code_size`
        bytes of code into.

        Code is padded up to a multiple of `CODE_CHUNK_SIZE` bytes
        before chunking, so a final partial chunk still counts as one
        whole chunk (see "Code").
        """
        return -(-code_size // cls.CODE_CHUNK_SIZE)
