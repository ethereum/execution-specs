"""
Snappy raw-block codec for RLPx frame payloads (p2p v5).

Compression emits literal elements only, without searching for
back-references, which is a valid Snappy encoding of any input.
Decompression implements the full format, because the remote end really
compresses. Pure Python keeps the peer dependency free and is fast
enough for the payloads RLPx carries.

Format reference: google/snappy `format_description.txt`.
"""

_MAX_LITERAL_LENGTH = 1 << 16
"""Payload bytes carried per literal element when compressing."""


class SnappyError(Exception):
    """Raised when a Snappy block cannot be decoded."""


def _encode_length(length: int) -> bytes:
    """Encode a payload length as the preamble's little-endian varint."""
    out = bytearray()
    while length >= 0x80:
        out.append((length & 0x7F) | 0x80)
        length >>= 7
    out.append(length)
    return bytes(out)


def _decode_length(data: bytes) -> tuple[int, int]:
    """Return the preamble's payload length and the offset after it."""
    length = 0
    shift = 0
    for position, byte in enumerate(data):
        length |= (byte & 0x7F) << shift
        if byte < 0x80:
            return length, position + 1
        shift += 7
        if shift > 31:
            break
    raise SnappyError("malformed length preamble")


def decompressed_length(data: bytes) -> int:
    """
    Return the decompressed size a Snappy block claims.

    Read without decompressing anything, which lets a reader enforce
    its size limit before allocating.
    """
    return _decode_length(data)[0]


def compress(data: bytes) -> bytes:
    """Encode `data` as a Snappy block of literal elements."""
    out = bytearray(_encode_length(len(data)))
    for start in range(0, len(data), _MAX_LITERAL_LENGTH):
        chunk = data[start : start + _MAX_LITERAL_LENGTH]
        stored = len(chunk) - 1
        if stored < 60:
            out.append(stored << 2)
        elif stored < (1 << 8):
            out.append(60 << 2)
            out.append(stored)
        else:
            out.append(61 << 2)
            out += stored.to_bytes(2, "little")
        out += chunk
    return bytes(out)


def decompress(data: bytes) -> bytes:
    """Decode one Snappy block."""
    expected_length, position = _decode_length(data)
    out = bytearray()
    while position < len(data):
        if len(out) > expected_length:
            # Checked as the output grows, so a block whose copies
            # expand far past its declared length is refused early
            # rather than after building all of it.
            break
        tag = data[position]
        position += 1
        element_type = tag & 0b11
        if element_type == 0b00:  # Literal.
            size = tag >> 2
            if size >= 60:
                extra = size - 59
                if position + extra > len(data):
                    raise SnappyError("truncated literal length")
                size = int.from_bytes(
                    data[position : position + extra], "little"
                )
                position += extra
            size += 1
            if position + size > len(data):
                raise SnappyError("truncated literal")
            out += data[position : position + size]
            position += size
            continue
        if element_type == 0b01:  # Copy with a 1 byte offset.
            if position >= len(data):
                raise SnappyError("truncated copy offset")
            size = ((tag >> 2) & 0b111) + 4
            offset = ((tag >> 5) << 8) | data[position]
            position += 1
        elif element_type == 0b10:  # Copy with a 2 byte offset.
            if position + 2 > len(data):
                raise SnappyError("truncated copy offset")
            size = (tag >> 2) + 1
            offset = int.from_bytes(data[position : position + 2], "little")
            position += 2
        else:  # Copy with a 4 byte offset.
            if position + 4 > len(data):
                raise SnappyError("truncated copy offset")
            size = (tag >> 2) + 1
            offset = int.from_bytes(data[position : position + 4], "little")
            position += 4
        if offset == 0 or offset > len(out):
            raise SnappyError("copy offset outside decoded output")
        # A copy may overlap its own output (offset < size), which is
        # how the format expresses run length encoding; appending byte
        # by byte reproduces that semantic exactly.
        for _ in range(size):
            out.append(out[-offset])
    if len(out) != expected_length:
        raise SnappyError(
            f"decompressed to {len(out)} bytes, preamble claimed "
            f"{expected_length}"
        )
    return bytes(out)
