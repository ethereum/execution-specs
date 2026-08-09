"""
Exceptions specific to this fork.
"""

from ethereum_types.numeric import U64

from ethereum.exceptions import InvalidTransaction


class WrongChainIdError(InvalidTransaction):
    """
    Chain identifier from a transaction does not match the executing chain. See
    [EIP-155].

    [EIP-155]: https://eips.ethereum.org/EIPS/eip-155
    """

    def __init__(self, expected: U64, actual: U64):
        super().__init__(f"expected chain_id `{expected}` but got `{actual}`")
        self.expected = expected
        self.actual = actual
