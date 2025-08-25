"""
abstract: Test cases for [EIP-663: SWAPN, DUPN and EXCHANGE instructions](https://eips.ethereum.org/EIPS/eip-663)
    EIP-663 defines new stack manipulation instructions that allow accessing the stack at higher depths.
    Opcodes introduced: `DUPN` (`0xE6`), `SWAPN` (`0xE7`), `EXCHANGEN` (`0xE8`).
"""  # noqa: E501

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-663.md"
REFERENCE_SPEC_VERSION = "b658bb87fe039d29e9475d5cfaebca9b92e0fca2"
