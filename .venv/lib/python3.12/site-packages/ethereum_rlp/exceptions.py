"""
Exceptions that can be thrown while serializing/deserializing RLP.
"""

from typing_extensions import override


class RLPException(Exception):
    """
    Common base class for all RLP exceptions.
    """


class DecodingError(RLPException):
    """
    Indicates that RLP decoding failed.
    """

    @override
    def __str__(self) -> str:
        message = [super().__str__()]
        current: BaseException = self
        while isinstance(current, DecodingError) and current.__cause__:
            current = current.__cause__
            if isinstance(current, DecodingError):
                as_str = super(DecodingError, current).__str__()
            else:
                as_str = str(current)
            message.append(f"\tbecause {as_str}")
        return "\n".join(message)


class EncodingError(RLPException):
    """
    Indicates that RLP encoding failed.
    """
