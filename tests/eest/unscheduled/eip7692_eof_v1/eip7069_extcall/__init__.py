"""
abstract: Test cases for [EIP-7069: Revamped CALL instructions](https://eips.ethereum.org/EIPS/eip-7069)
    EIP-7069 proposes modifications to `CALL` instructions to align with the structured EOF format.
    Opcodes introduced: `EXTCALL` (`0xF8`), `EXTDELEGATECALL` (`0xF9`), `EXTSTATICCALL` (`0xFB`), `RETURNDATALOAD` (`0xF7`).
"""  # noqa: E501

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-7069.md"
REFERENCE_SPEC_VERSION = "1795943aeacc86131d5ab6bb3d65824b3b1d4cad"
