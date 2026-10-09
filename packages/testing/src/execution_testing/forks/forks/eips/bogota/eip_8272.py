"""
EIP-8272: Recent Roots for Frame Transactions.

Add the recent root contract, an ordinary contract deployed by a
pre-signed creation transaction, that stores application roots by source
and slot and lets a frame transaction verify recent roots through a
`VERIFY` frame targeting it. The transaction payload, gas rules and
opcodes are unchanged.

https://eips.ethereum.org/EIPS/eip-8272
"""

from typing import Mapping

from ....base_fork import BaseFork

RECENT_ROOT_ADDRESS = 0x8272D9679689EA2F307140CDF9002D27DC00FFFF
RECENT_ROOT_BYTECODE = bytes.fromhex(
    "346100ba57366040146100c05736604836066100ba5780156100ba57610480"
    "81116100ba574b60005b602081013560c01c828110156100ba578083036120"
    "0011156100ba577f8f42481679c8e6fefa040974b3c905e0ce3f2e464ba93a"
    "cdb074a41181617efc60005260488260203760686000207fbdc897da2177d2"
    "60ff5f4be5d4b2aad43f89c3347a305b584fa5a2546d053daa60005290611f"
    "ff1660c01b60405260486000205414156100ba5760480182811061002857005b"
    "60006000fd5b33600052602060006020376034600c20807f8f42481679c8e6"
    "fefa040974b3c905e0ce3f2e464ba93acdb074a41181617efc6040524b6068"
    "52606052602060206088376068604020817fbdc897da2177d260ff5f4be5d4"
    "b2aad43f89c3347a305b584fa5a2546d053daa60a852611fff4b1660d05260"
    "c852604860a8205500"
)
RECENT_ROOT_NONCE = 1


class EIP8272(BaseFork):
    """EIP-8272 class."""

    @classmethod
    def pre_allocation(cls) -> Mapping:
        """Pre-allocate the recent root contract."""
        return {
            RECENT_ROOT_ADDRESS: {
                "nonce": RECENT_ROOT_NONCE,
                "code": RECENT_ROOT_BYTECODE,
            }
        } | super(EIP8272, cls).pre_allocation()  # type: ignore

    @classmethod
    def pre_allocation_blockchain(cls) -> Mapping:
        """Pre-allocate the recent root contract."""
        return {
            RECENT_ROOT_ADDRESS: {
                "nonce": RECENT_ROOT_NONCE,
                "code": RECENT_ROOT_BYTECODE,
            }
        } | super(EIP8272, cls).pre_allocation_blockchain()  # type: ignore
