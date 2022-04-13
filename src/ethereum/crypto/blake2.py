"""
The Blake2 Implementation
^^^^^^^^^^^^^^^^^^^^^^^^^^
"""
import struct
from dataclasses import dataclass
from typing import List, Tuple

from ethereum.base_types import Uint


def get_words_from_le_bytes(data: bytes, start: int, num_words: int) -> List:
    """
    Extracts 8 byte words from a given data.

    Parameters
    ----------
    data :
        The data in bytes from which the words need to be extracted
    start :
        Position to start the extraction
    num_words:
        The number of words to be extracted
    """
    words = []
    for i in range(num_words):
        start_position = start + (i * 8)
        words.append(
            Uint.from_le_bytes(data[start_position : start_position + 8])
        )

    return words


@dataclass
class Blake2:
    """
    Implementation of the BLAKE2 cryptographic hashing algorithm.

    Please refer the following document for details:
    https://datatracker.ietf.org/doc/html/rfc7693
    """

    w: int
    mask_bits: int
    word_format: str

    R1: int
    R2: int
    R3: int
    R4: int

    @property
    def max_word(self) -> int:
        """
        Largest value for a given Blake2 flavor.
        """
        return 2**self.w

    @property
    def w_R1(self) -> int:
        """
        (w - R1) value for a given Blake2 flavor.
        Used in the function G
        """
        return self.w - self.R1

    @property
    def w_R2(self) -> int:
        """
        (w - R2) value for a given Blake2 flavor.
        Used in the function G
        """
        return self.w - self.R2

    @property
    def w_R3(self) -> int:
        """
        (w - R3) value for a given Blake2 flavor.
        Used in the function G
        """
        return self.w - self.R3

    @property
    def w_R4(self) -> int:
        """
        (w - R4) value for a given Blake2 flavor.
        Used in the function G
        """
        return self.w - self.R4

    sigma: Tuple = (
        (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15),
        (14, 10, 4, 8, 9, 15, 13, 6, 1, 12, 0, 2, 11, 7, 5, 3),
        (11, 8, 12, 0, 5, 2, 15, 13, 10, 14, 3, 6, 7, 1, 9, 4),
        (7, 9, 3, 1, 13, 12, 11, 14, 2, 6, 5, 10, 4, 0, 15, 8),
        (9, 0, 5, 7, 2, 4, 10, 15, 14, 1, 11, 12, 6, 8, 3, 13),
        (2, 12, 6, 10, 0, 11, 8, 3, 4, 13, 7, 5, 15, 14, 1, 9),
        (12, 5, 1, 15, 14, 13, 4, 10, 0, 7, 6, 3, 9, 2, 8, 11),
        (13, 11, 7, 14, 12, 1, 3, 9, 5, 0, 15, 4, 8, 6, 2, 10),
        (6, 15, 14, 9, 11, 3, 0, 8, 12, 2, 13, 7, 1, 4, 10, 5),
        (10, 2, 8, 4, 7, 6, 1, 5, 15, 11, 9, 14, 3, 12, 13, 0),
    )

    IV: Tuple = (
        0x6A09E667F3BCC908,
        0xBB67AE8584CAA73B,
        0x3C6EF372FE94F82B,
        0xA54FF53A5F1D36F1,
        0x510E527FADE682D1,
        0x9B05688C2B3E6C1F,
        0x1F83D9ABFB41BD6B,
        0x5BE0CD19137E2179,
    )

    @property
    def sigma_len(self) -> int:
        """
        Length of the sigma parameter.
        """
        return len(self.sigma)

    def get_blake2_parameters(self, data: bytes) -> Tuple:
        """
        Extract the parameters required in the Blake2 compression function
        from the provided bytes data.
        """
        rounds = Uint.from_be_bytes(data[:4])
        h = get_words_from_le_bytes(data, 4, 8)
        m = get_words_from_le_bytes(data, 68, 16)
        t_0, t_1 = get_words_from_le_bytes(data, 196, 2)
        f = Uint.from_be_bytes(data[212:])

        return (rounds, h, m, t_0, t_1, f)

    def G(
        self, v: List, a: int, b: int, c: int, d: int, x: int, y: int
    ) -> List:
        """
        The mixing function used in Blake2
        https://datatracker.ietf.org/doc/html/rfc7693#section-3.1
        """
        v[a] = (v[a] + v[b] + x) % self.max_word
        v[d] = ((v[d] ^ v[a]) >> self.R1) ^ (
            (v[d] ^ v[a]) << self.w_R1
        ) % self.max_word

        v[c] = (v[c] + v[d]) % self.max_word
        v[b] = ((v[b] ^ v[c]) >> self.R2) ^ (
            (v[b] ^ v[c]) << self.w_R2
        ) % self.max_word

        v[a] = (v[a] + v[b] + y) % self.max_word
        v[d] = ((v[d] ^ v[a]) >> self.R3) ^ (
            (v[d] ^ v[a]) << self.w_R3
        ) % self.max_word

        v[c] = (v[c] + v[d]) % self.max_word
        v[b] = ((v[b] ^ v[c]) >> self.R4) ^ (
            (v[b] ^ v[c]) << self.w_R4
        ) % self.max_word

        return v

    def compress(
        self, num_rounds: int, h: List, m: List, t_0: Uint, t_1: Uint, f: bool
    ) -> bytes:
        """
        'F Compression' from section 3.2 of RFC 7693:
        https://tools.ietf.org/html/rfc7693#section-3.2
        """
        # Initialize local work vector v[0..15]
        v = [0] * 16
        v[0:8] = h  # First half from state
        v[8:15] = self.IV  # Second half from IV

        v[12] = t_0 ^ self.IV[4]  # Low word of the offset
        v[13] = t_1 ^ self.IV[5]  # High word of the offset

        if f:
            v[14] = v[14] ^ self.mask_bits  # Invert all bits for last block

        # Mixing
        for r in range(num_rounds):
            # for more than sigma_len rounds, the schedule
            # wraps around to the beginning
            s = self.sigma[r % self.sigma_len]

            v = self.G(v, 0, 4, 8, 12, m[s[0]], m[s[1]])
            v = self.G(v, 1, 5, 9, 13, m[s[2]], m[s[3]])
            v = self.G(v, 2, 6, 10, 14, m[s[4]], m[s[5]])
            v = self.G(v, 3, 7, 11, 15, m[s[6]], m[s[7]])
            v = self.G(v, 0, 5, 10, 15, m[s[8]], m[s[9]])
            v = self.G(v, 1, 6, 11, 12, m[s[10]], m[s[11]])
            v = self.G(v, 2, 7, 8, 13, m[s[12]], m[s[13]])
            v = self.G(v, 3, 4, 9, 14, m[s[14]], m[s[15]])

        result_message_words = (h[i] ^ v[i] ^ v[i + 8] for i in range(8))
        return struct.pack("<8%s" % self.word_format, *result_message_words)


# Parameters specific to the Blake2b implementation
@dataclass
class Blake2b(Blake2):
    """
    The Blake2b flavor (64-bits) of Blake2.
    This version is used in the pre-compiled contract.
    """

    w: int = 64
    mask_bits: int = 0xFFFFFFFFFFFFFFFF
    word_format: str = "Q"

    R1: int = 32
    R2: int = 24
    R3: int = 16
    R4: int = 63
