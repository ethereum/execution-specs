"""
The algorithm abstract class, all algorithms implement this class.
"""

from abc import ABC, abstractmethod

from ethereum_types.numeric import U8, U32, U64

__all__ = ("Algorithm",)


class Algorithm(ABC):  # noqa: D101
    @property
    @abstractmethod
    def algorithm_type(self) -> U8:
        """
        The algorithm type / id that is prefixed to the
        start of signature data.
        """
        pass

    @property
    @abstractmethod
    def size(self) -> U32:
        """
        The size of all signatures produced by this
        algorithm.
        """
        pass

    @abstractmethod
    def gas_cost(self, signing_data: bytes) -> U64:
        """
        Get the gas cost of signing the data `signing_data`
        for this particular algorithm.
        """
        pass

    @abstractmethod
    def validate(self, signature: bytes) -> None:
        """
        Check whether the signature is valid. For some
        algorithms, this may be a no-op. This function
        must always be called before `verify`.

        Throws:
          - AlgorithmValidationError
        """
        pass

    @abstractmethod
    def verify(self, signature: bytes, signing_data: bytes) -> bytes:
        """
        Take the signature and signing_data and return the
        public key of the signer.

        Throws:
          - AlgorithmVerificationError
        """
        pass
