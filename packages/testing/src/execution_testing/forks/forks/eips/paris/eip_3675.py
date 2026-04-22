"""
EIP-3675: Upgrade consensus to Proof-of-Stake.

Deprecate Proof-of-Work and upgrade the consensus mechanism to
Proof-of-Stake.

https://eips.ethereum.org/EIPS/eip-3675
"""

from ....base_fork import BaseFork


class EIP3675(
    BaseFork,
    engine_new_payload_version_bump=True,
    engine_forkchoice_updated_version_bump=True,
    engine_get_payload_version_bump=True,
):
    """EIP-3675 class."""

    @classmethod
    def header_prev_randao_required(cls) -> bool:
        """Prev Randao is required."""
        return True

    @classmethod
    def header_zero_difficulty_required(cls) -> bool:
        """Zero difficulty is required."""
        return True

    @classmethod
    def get_reward(cls) -> int:
        """Block reward is removed."""
        return 0
