"""
EIP-7805: Fork-choice enforced Inclusion Lists (FOCIL).

Adds an ``inclusionListTransactions`` parameter to ``engine_newPayloadV6`` and
bumps ``engine_forkchoiceUpdated`` to V5 so the CL can pass per-committee ILs
to the EL on the forkchoice-update path.

https://eips.ethereum.org/EIPS/eip-7805
"""

from ....base_fork import BaseFork


class EIP7805(
    BaseFork,
    # Engine API method version bumps
    # New `inclusionListTransactions` parameter on newPayload, and
    # `engine_getInclusionListV1` introduced on the GET side.
    engine_new_payload_version_bump=True,
    engine_forkchoice_updated_version_bump=True,
):
    """EIP-7805 class."""
