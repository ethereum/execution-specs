"""
Helper functions for the EIP-198 ModExp precompile tests.
"""

from typing import Tuple

from ethereum_test_tools import Bytes, TestParameterGroup
from pydantic import Field


class ModExpInput(TestParameterGroup):
    """
    Helper class that defines the MODEXP precompile inputs and creates the call
    data from them.

    Attributes:
        base (str): The base value for the MODEXP precompile.
        exponent (str): The exponent value for the MODEXP precompile.
        modulus (str): The modulus value for the MODEXP precompile.
        extra_data (str): Defines extra padded data to be added at the end of
                          the calldata to the precompile.
                          Defaults to an empty string.

    """

    base: Bytes
    exponent: Bytes
    modulus: Bytes
    extra_data: Bytes = Field(default_factory=Bytes)
    raw_input: Bytes | None = None
    declared_base_length: int | None = None
    declared_exponent_length: int | None = None
    declared_modulus_length: int | None = None

    @property
    def length_base(self) -> Bytes:
        """Return the length of the base."""
        length = (
            self.declared_base_length
            if self.declared_base_length is not None
            else len(self.base)
        )
        return Bytes(length.to_bytes(32, "big"))

    @property
    def length_exponent(self) -> Bytes:
        """Return the length of the exponent."""
        length = (
            self.declared_exponent_length
            if self.declared_exponent_length is not None
            else len(self.exponent)
        )
        return Bytes(length.to_bytes(32, "big"))

    @property
    def length_modulus(self) -> Bytes:
        """Return the length of the modulus."""
        length = (
            self.declared_modulus_length
            if self.declared_modulus_length is not None
            else len(self.modulus)
        )
        return Bytes(length.to_bytes(32, "big"))

    def __bytes__(self) -> bytes:
        """Generate input for the MODEXP precompile."""
        if self.raw_input is not None:
            return self.raw_input
        return (
            self.length_base
            + self.length_exponent
            + self.length_modulus
            + self.base
            + self.exponent
            + self.modulus
            + self.extra_data
        )

    @classmethod
    def from_bytes(cls, input_data: Bytes | str) -> "ModExpInput":
        """
        Create a ModExpInput from a bytes object.

        Assumes correct formatting of the input data.
        """
        if isinstance(input_data, str):
            input_data = Bytes(input_data)
        assert not isinstance(input_data, str)
        padded_input_data = input_data
        if len(padded_input_data) < 96:
            padded_input_data = Bytes(padded_input_data.ljust(96, b"\0"))
        base_length = int.from_bytes(padded_input_data[0:32], byteorder="big")
        exponent_length = int.from_bytes(
            padded_input_data[32:64], byteorder="big"
        )
        modulus_length = int.from_bytes(
            padded_input_data[64:96], byteorder="big"
        )

        total_required_length = (
            96 + base_length + exponent_length + modulus_length
        )
        if len(padded_input_data) < total_required_length:
            padded_input_data = Bytes(
                padded_input_data.ljust(total_required_length, b"\0")
            )

        current_index = 96
        base = padded_input_data[current_index : current_index + base_length]
        current_index += base_length

        exponent = padded_input_data[
            current_index : current_index + exponent_length
        ]
        current_index += exponent_length

        modulus = padded_input_data[
            current_index : current_index + modulus_length
        ]

        return cls(
            base=base, exponent=exponent, modulus=modulus, raw_input=input_data
        )

    def get_declared_lengths(self) -> Tuple[int, int, int]:
        """Extract declared lengths from the raw input bytes."""
        raw = self.raw_input if self.raw_input is not None else bytes(self)
        if len(raw) < 96:
            raw = raw.ljust(96, b"\0")
        base_length = int.from_bytes(raw[0:32], byteorder="big")
        exponent_length = int.from_bytes(raw[32:64], byteorder="big")
        modulus_length = int.from_bytes(raw[64:96], byteorder="big")
        return base_length, exponent_length, modulus_length

    def get_exponent_head(self) -> int:
        """Get the first 32 bytes of the exponent as an integer."""
        raw = self.raw_input if self.raw_input is not None else bytes(self)
        base_length, exponent_length, _ = self.get_declared_lengths()
        exp_start = 96 + base_length

        # Extract up to 32 bytes of exponent data
        exp_head_bytes = raw[exp_start : exp_start + min(32, exponent_length)]

        # Pad with zeros if less than 32 bytes
        exp_head_bytes = exp_head_bytes.rjust(32, b"\0")

        return int.from_bytes(exp_head_bytes[:32], byteorder="big")


class ModExpOutput(TestParameterGroup):
    """
    Expected test result.

    Attributes:
      call_success (bool): The return_code from CALL, 0 indicates
                           unsuccessful call (out-of-gas), 1 indicates call
                           succeeded.
      returned_data(str): The output returnData is the expected
                          output of the call.

    """

    call_success: bool = True
    returned_data: Bytes
