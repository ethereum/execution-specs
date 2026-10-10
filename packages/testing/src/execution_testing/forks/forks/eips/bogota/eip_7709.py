"""
EIP-7709: Read BLOCKHASH from storage and update cost.

Serve the BLOCKHASH opcode from the EIP-2935 history storage contract and
charge the cold or warm storage access cost of the slot it reads.

https://eips.ethereum.org/EIPS/eip-7709
"""

from ....base_fork import BaseFork


class EIP7709(BaseFork):
    """EIP-7709 class."""

    pass
