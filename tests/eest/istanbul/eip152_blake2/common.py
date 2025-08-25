"""Common classes used in the BLAKE2b precompile tests."""

from dataclasses import dataclass

from ethereum_test_base_types import Bytes
from ethereum_test_types.helpers import TestParameterGroup

from .spec import Spec, SpecTestVectors


class Blake2bInput(TestParameterGroup):
    """
    Helper class that defines the BLAKE2b precompile inputs and creates the
    call data from them. Returns all inputs encoded as bytes.

    Attributes:
        rounds_length (int): An optional integer representing the bytes length
            for the number of rounds. Defaults to the expected length of 4.
        rounds (int | str): A hex string or integer value representing the number of rounds.
        h (str): A hex string that represents the state vector.
        m (str): A hex string that represents the message block vector.
        t_0 (int | str): A hex string or integer value that represents the first offset counter.
        t_1 (int | str): A hex string or integer value that represents the second offset counter.
        f (bool): An optional boolean that represents the final block indicator flag.
            Defaults to True.

    """

    rounds_length: int = Spec.BLAKE2_PRECOMPILE_ROUNDS_LENGTH
    rounds: int = Spec.BLAKE2B_PRECOMPILE_ROUNDS
    h: Bytes = SpecTestVectors.BLAKE2_STATE_VECTOR  # type: ignore
    m: Bytes = SpecTestVectors.BLAKE2_MESSAGE_BLOCK_VECTOR  # type: ignore
    t_0: int | Bytes = SpecTestVectors.BLAKE2_OFFSET_COUNTER_0
    t_1: int | Bytes = SpecTestVectors.BLAKE2_OFFSET_COUNTER_1
    f: bool | int = True

    def create_blake2b_tx_data(self):
        """Generate input for the BLAKE2b precompile."""
        _rounds = self.rounds.to_bytes(length=self.rounds_length, byteorder="big")
        _t_0 = (
            self.t_0
            if isinstance(self.t_0, bytes)
            else self.t_0.to_bytes(length=Spec.BLAKE2_PRECOMPILE_T_0_LENGTH, byteorder="little")
        )
        _t_1 = (
            self.t_1
            if isinstance(self.t_1, bytes)
            else self.t_1.to_bytes(length=Spec.BLAKE2_PRECOMPILE_T_1_LENGTH, byteorder="little")
        )
        _f = int(self.f).to_bytes(length=Spec.BLAKE2_PRECOMPILE_F_LENGTH, byteorder="big")

        return _rounds + self.h + self.m + _t_0 + _t_1 + _f


@dataclass(kw_only=True, frozen=True, repr=False)
class ExpectedOutput(TestParameterGroup):
    """
    Expected test result.

    Attributes:
        call_succeeds (str | bool): A hex string or boolean to indicate whether the call was
            successful or not.
        data_1 (str): String value of the first updated state vector.
        data_2 (str): String value of the second updated state vector.

    """

    call_succeeds: str | bool
    data_1: str
    data_2: str
