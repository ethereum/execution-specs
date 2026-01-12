"""
The exceptions that may be thrown during signature processing.
"""


class AlgorithmValidationError(BaseException):
    """
    Thrown when an algorithm has failed to
    validate a signature.
    """

    pass


class AlgorithmVerificationError(BaseException):
    """
    Thrown when an algorithm has failed to
    verify a signature.
    """

    pass
