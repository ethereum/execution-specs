"""Defines EIP-8297 specification constants and functions."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """Reference specification."""

    git_path: str
    version: str


ref_spec_8297 = ReferenceSpec(
    git_path="EIPS/eip-8297.md",
    version="6c054508d3cee38911bcc265e5f1c5416077d99a",
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

    # Header stem layout: HEADER_STORAGE_OFFSET is itself a sub-index
    # marking where the storage sub-range starts within the header
    # stem's 256-wide space, and HEADER_STORAGE_SLOTS counts the
    # co-located slots. The sub-indices in use are the two fixed
    # leaves and that storage range; no key defined by the EIP
    # resolves to any other sub-index (see "Tree embedding").
    HEADER_STORAGE_OFFSET = 64
    HEADER_STORAGE_SLOTS = 64
    STEM_SUBTREE_WIDTH = 256

    # Code chunking: CODE_CHUNK_SIZE (31) is the code-payload length
    # in bytes -- the stored chunk itself is 32 bytes (one metadata
    # byte plus this payload). The name is not from the EIP text,
    # which uses a bare `31` literal; PUSH_OFFSET is the opcode-value
    # offset used to recover a PUSH's data length when marking a
    # chunk's leading PUSHDATA bytes, and PUSH1/PUSH32 bound the range
    # of opcodes that carry push data (see "Code").
    CODE_CHUNK_SIZE = 31
    PUSH_OFFSET = 95
    PUSH1 = 96
    PUSH32 = 127

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

    # Tree node hash-preimage tags: the first byte distinguishing a
    # leaf node's preimage from a branch node's, so the two can never
    # collide (see "Merkleization").
    LEAF_TAG = 0x00
    BRANCH_TAG = 0x01

    # BASIC_DATA leaf layout: byte offset and width of each field
    # packed into the account header's basic-data leaf (see "Header
    # values"). Widths sum to the leaf's full 32 bytes.
    BASIC_DATA_VERSION_OFFSET = 0
    BASIC_DATA_VERSION_WIDTH = 1
    BASIC_DATA_RESERVED_OFFSET = 1
    BASIC_DATA_RESERVED_WIDTH = 3
    BASIC_DATA_CODE_SIZE_OFFSET = 4
    BASIC_DATA_CODE_SIZE_WIDTH = 4
    BASIC_DATA_NONCE_OFFSET = 8
    BASIC_DATA_NONCE_WIDTH = 8
    BASIC_DATA_BALANCE_OFFSET = 16
    BASIC_DATA_BALANCE_WIDTH = 16

    @classmethod
    def header_storage_sub_index(cls, slot: int) -> int:
        """
        Return the account header sub-index for storage `slot`.

        Only valid for `slot < HEADER_STORAGE_SLOTS` (slots 0..63),
        which live in the account header's stem rather than the
        storage zone (see "Storage").
        """
        return cls.HEADER_STORAGE_OFFSET + slot

    @classmethod
    def storage_group_index(cls, slot: int) -> int:
        """
        Return the storage group (`tree_index`) that `slot` belongs to.

        Applies to slots stored in the storage zone, i.e.
        `slot >= HEADER_STORAGE_SLOTS` (see "Storage").
        An aligned range of `STEM_SUBTREE_WIDTH` slots sharing one
        `tree_index` forms one storage group. Group 0 is the
        exception: slots 0..63 live in the header, so its storage-zone
        leaves are slots 64..255 only.
        """
        return slot // cls.STEM_SUBTREE_WIDTH

    @classmethod
    def storage_sub_index(cls, slot: int) -> int:
        """
        Return `slot`'s sub-index within its storage group.

        Applies to slots stored in the storage zone, i.e.
        `slot >= HEADER_STORAGE_SLOTS` (see "Storage").
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
