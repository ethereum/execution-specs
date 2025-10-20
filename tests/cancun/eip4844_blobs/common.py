"""Common constants, classes & functions local to EIP-4844 tests."""

from typing import Literal

INF_POINT = (0xC0 << 376).to_bytes(48, byteorder="big")
Z = 0x623CE31CF9759A5C8DAF3A357992F9F3DD7F9339D8998BC8E68373E54F00B75E
Z_Y_INVALID_ENDIANNESS: Literal["little", "big"] = "little"
Z_Y_VALID_ENDIANNESS: Literal["little", "big"] = "big"
