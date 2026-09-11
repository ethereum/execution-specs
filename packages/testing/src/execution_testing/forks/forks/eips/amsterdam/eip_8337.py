"""
EIP-8337: Validated EVM Code.

Code prefixed with MAGIC bytes is validated at CREATE time to have fully
static control flow and never underflow the data stack. No new opcodes.

https://eips.ethereum.org/EIPS/eip-8337
"""

from ....base_fork import BaseFork


class EIP8337(BaseFork):
    """EIP-8337 class."""

    pass
