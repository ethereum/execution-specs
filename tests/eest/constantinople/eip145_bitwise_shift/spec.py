"""Defines EIP-145 specification constants and functions."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """Defines the reference spec version and git path."""

    git_path: str
    version: str


ref_spec_145 = ReferenceSpec("EIPS/eip-145.md", "be0aca3e57f1eeb8ae265e58da6e2dffc5b67f81")


@dataclass(frozen=True)
class Spec:
    """
    Parameters from the EIP-145 specifications as defined at
    https://eips.ethereum.org/EIPS/eip-145.
    """

    # Below are GPT o4-mini-high implementation of shift functions
    # It can contain bugs, treat it with caution and refer to EVM implementations
    @staticmethod
    def sar(shift: int, value: int) -> int:
        """
        Simulate the EVM SAR (Signed Arithmetic Right shift) operation.

        Parameters
        ----------
        shift : int
            Number of bits to shift to the right (interpreted as full unsigned;
            no low-8-bit truncation here).
        value : int
            The 256-bit value to shift, interpreted as a signed integer.

        Returns
        -------
        int
            The result of the arithmetic right shift, pushed as an unsigned
            256-bit integer on the EVM stack.

        """
        mask256 = (1 << 256) - 1  # Clamp value to 256 bits

        # Interpret as signed
        v = value & mask256
        if v >> 255:
            v_signed = v - (1 << 256)
        else:
            v_signed = v

        # If shift >= 256, spec says:
        #   • result = 0   if v_signed >= 0
        #   • result = -1  if v_signed <  0
        if shift >= 256:
            result_signed = -1 if v_signed < 0 else 0
        else:
            # Normal arithmetic right shift
            result_signed = v_signed >> shift

        # Wrap back to unsigned 256-bit
        return result_signed & mask256

    @staticmethod
    def shl(shift: int, value: int) -> int:
        """
        Simulate the EVM SHL (Logical Left shift) operation.

        Parameters
        ----------
        shift : int
            Number of bits to shift to the left.
        value : int
            The 256-bit value to shift, interpreted as an unsigned integer.

        Returns
        -------
        int
            The result of the logical left shift, pushed as an unsigned
            256-bit integer on the EVM stack.

        """
        mask256 = (1 << 256) - 1
        # Clamp input to 256 bits
        v = value & mask256

        # If shift >= 256, spec returns 0
        if shift >= 256:
            return 0

        # Logical left shift and wrap to 256 bits
        return (v << shift) & mask256

    @staticmethod
    def shr(shift: int, value: int) -> int:
        """
        Simulate the EVM SHR (Logical Right shift) operation.

        Parameters
        ----------
        shift : int
            Number of bits to shift to the right.
        value : int
            The 256-bit value to shift, interpreted as an unsigned integer.

        Returns
        -------
        int
            The result of the logical right shift, pushed as an unsigned
            256-bit integer on the EVM stack.

        """
        mask256 = (1 << 256) - 1
        # Clamp input to 256 bits
        v = value & mask256

        # If shift >= 256, the EVM spec returns 0
        if shift >= 256:
            return 0

        # Logical right shift and mask back to 256 bits
        return (v >> shift) & mask256
