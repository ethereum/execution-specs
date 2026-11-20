"""
Tests for the Snappy raw-block codec RLPx payloads travel in.

The hand-built blocks follow the element layouts of google/snappy's
`format_description.txt`:
https://github.com/google/snappy/blob/main/format_description.txt
"""

import random

import pytest

from ..snappy import SnappyError, compress, decompress


class TestRoundTrip:
    """Every payload decodes to itself."""

    @pytest.mark.parametrize(
        "size", [0, 1, 60, 61, 256, 257, 65_536, 65_537, 200_000]
    )
    def test_literal_boundaries(self, size: int) -> None:
        """Payloads at each literal length encoding's edges survive."""
        data = random.Random(size).randbytes(size)
        assert decompress(compress(data)) == data


class TestDecompress:
    """Blocks a client compresses, back-references included."""

    def test_an_overlapping_copy_repeats_its_source(self) -> None:
        """A copy reaching into its own output is run length encoding."""
        # Length 10; literal "ab"; copy of 8 bytes at offset 2.
        block = bytes([10, 1 << 2]) + b"ab" + bytes([0b01 | (4 << 2), 2])
        assert decompress(block) == b"ababababab"

    def test_a_copy_with_a_high_one_byte_offset(self) -> None:
        """A 1-byte-offset copy takes offset bits 8-10 from its tag."""
        # Length 304; a 300-byte literal with a two byte length; then a
        # copy of 4 bytes at offset 300 (0x12c: tag bits 1, byte 0x2c).
        literal = bytes(range(256)) + bytes(range(44))
        block = bytes([0xB0, 0x02, 61 << 2]) + (299).to_bytes(2, "little")
        block += literal + bytes([0b01 | (1 << 5), 0x2C])
        assert decompress(block) == literal + literal[:4]

    def test_a_copy_with_a_two_byte_offset(self) -> None:
        """A 2-byte-offset copy stores its length minus one in the tag."""
        # Length 8; literal "abcd"; copy of 4 bytes at offset 4.
        block = bytes([8, 3 << 2]) + b"abcd" + bytes([0b10 | (3 << 2), 4, 0])
        assert decompress(block) == b"abcdabcd"

    def test_a_copy_with_a_four_byte_offset(self) -> None:
        """A 4-byte-offset copy reads its offset little-endian."""
        # Length 8; literal "abcd"; copy of 4 bytes at offset 4.
        block = bytes([8, 3 << 2]) + b"abcd" + bytes([0b11 | (3 << 2)])
        block += (4).to_bytes(4, "little")
        assert decompress(block) == b"abcdabcd"

    def test_a_block_expanding_past_its_length_is_refused(self) -> None:
        """
        Copies that overrun the declared length are refused as soon as
        they do, before any later element is decoded.
        """
        # Length 1; literal "a"; a 64-byte copy overruns; then a copy
        # tag with its offset missing, which is only reached late.
        copy = bytes([0b10 | (63 << 2), 1, 0])
        block = bytes([1, 0]) + b"a" + copy + bytes([0b11])
        with pytest.raises(SnappyError, match="preamble claimed 1"):
            decompress(block)

    def test_a_truncated_literal_is_refused(self) -> None:
        """A literal shorter than its tag claims raises."""
        with pytest.raises(SnappyError, match="truncated literal"):
            decompress(bytes([4, 3 << 2]) + b"ab")

    def test_a_copy_before_any_output_is_refused(self) -> None:
        """A back-reference with nothing behind it raises."""
        with pytest.raises(SnappyError, match="outside decoded output"):
            decompress(bytes([4, 0b01, 1]))
