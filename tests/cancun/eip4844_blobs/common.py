"""Common constants, classes & functions local to EIP-4844 tests."""

from typing import Literal

INF_POINT = (0xC0 << 376).to_bytes(48, byteorder="big")
# BLS12-381 G1 generator in compressed form (48 bytes, big-endian).
G1_GENERATOR = bytes.fromhex(
    "97f1d3a73197d7942695638c4fa9ac0fc3688c4f9774b905a14e3a3f171bac58"
    "6c55e83ff97a1aeffb3af00adb22c6bb"
)
# Negation flips the y-sign bit (0x20) in the leading byte.
NEG_G1_GENERATOR = bytes([G1_GENERATOR[0] ^ 0x20]) + G1_GENERATOR[1:]
Z = 0x623CE31CF9759A5C8DAF3A357992F9F3DD7F9339D8998BC8E68373E54F00B75E
Z_Y_INVALID_ENDIANNESS: Literal["little", "big"] = "little"
Z_Y_VALID_ENDIANNESS: Literal["little", "big"] = "big"
