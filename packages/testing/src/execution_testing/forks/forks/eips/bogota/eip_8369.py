"""EIP-8369: bounded frame-prefix replay for omission claims."""

from ....base_fork import BaseFork


class EIP8369(BaseFork, engine_get_payload_version_bump=True):
    """Enable membership and omission claims on the combined FOCIL fork."""

    @classmethod
    def engine_new_payload_omission_claims(cls) -> bool:
        """Require membership and claims in engine_newPayloadV6."""
        return True
