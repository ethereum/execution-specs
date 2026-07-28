"""
EIP-7805: Fork-choice enforced Inclusion Lists (FOCIL).

Allow a committee of validators to force-include a set of transactions in
every block.

https://eips.ethereum.org/EIPS/eip-7805
"""

from ....base_fork import BaseFork


class EIP7805(
    BaseFork,
    # Engine API method version bumps
    # New parameter `inclusionListTransactions` in engine_newPayload
    engine_new_payload_version_bump=True,
    engine_forkchoice_updated_version_bump=True,
):
    """EIP-7805 class."""

    @classmethod
    def engine_new_payload_inclusion_list_transactions(cls) -> bool:
        """Payload attributes include the slot number."""
        return True
