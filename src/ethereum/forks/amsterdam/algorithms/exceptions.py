"""
The exceptions that may be thrown during signature processing.
"""


class AlgorithmValidationError(Exception):
    """
    Thrown when an algorithm has failed to
    validate a signature.
    """

    pass


class AlgorithmVerificationError(Exception):
    """
    Thrown when an algorithm has failed to
    verify a signature.
    """

    pass
