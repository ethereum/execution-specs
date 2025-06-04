"""Helper functions for the EIP-198 ModExp precompile tests."""

from pydantic import Field

from ethereum_test_tools import Bytes, TestParameterGroup


class ModExpInput(TestParameterGroup):
    """
    Helper class that defines the MODEXP precompile inputs and creates the
    call data from them.

    Attributes:
        base (str): The base value for the MODEXP precompile.
        exponent (str): The exponent value for the MODEXP precompile.
        modulus (str): The modulus value for the MODEXP precompile.
        extra_data (str): Defines extra padded data to be added at the end of the calldata
            to the precompile. Defaults to an empty string.

    """

    base: Bytes
    exponent: Bytes
    modulus: Bytes
    extra_data: Bytes = Field(default_factory=Bytes)

    @property
    def length_base(self) -> Bytes:
        """Return the length of the base."""
        return Bytes(len(self.base).to_bytes(32, "big"))

    @property
    def length_exponent(self) -> Bytes:
        """Return the length of the exponent."""
        return Bytes(len(self.exponent).to_bytes(32, "big"))

    @property
    def length_modulus(self) -> Bytes:
        """Return the length of the modulus."""
        return Bytes(len(self.modulus).to_bytes(32, "big"))

    def __bytes__(self):
        """Generate input for the MODEXP precompile."""
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
        base_length = int.from_bytes(input_data[0:32], byteorder="big")
        exponent_length = int.from_bytes(input_data[32:64], byteorder="big")
        modulus_length = int.from_bytes(input_data[64:96], byteorder="big")

        current_index = 96
        base = input_data[current_index : current_index + base_length]
        current_index += base_length

        exponent = input_data[current_index : current_index + exponent_length]
        current_index += exponent_length

        modulus = input_data[current_index : current_index + modulus_length]

        return cls(base=base, exponent=exponent, modulus=modulus)


class ModExpOutput(TestParameterGroup):
    """
    Expected test result.

    Attributes:
        call_success (bool): The return_code from CALL, 0 indicates unsuccessful call
            (out-of-gas), 1 indicates call succeeded.
        returned_data (str): The output returnData is the expected output of the call

    """

    call_success: bool = True
    returned_data: Bytes
