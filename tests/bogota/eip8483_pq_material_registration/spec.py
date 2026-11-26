"""
Reference spec and constants for
[EIP-8483: Post-Quantum Material Registration][8483].

[8483]: https://eips.ethereum.org/EIPS/eip-8483
"""

from dataclasses import dataclass

from execution_testing import Address
from execution_testing.forks.forks.eips.bogota.eip_8483 import (
    OTHER_CHAIN_PROOFS_OF_POSSESSION,
    PROOF_OF_POSSESSION_VERIFIER_ADDRESS,
    PROOFS_OF_POSSESSION,
    ProofOfPossession,
)

__all__ = [
    "OTHER_CHAIN_PROOFS_OF_POSSESSION",
    "PROOFS_OF_POSSESSION",
    "ProofOfPossession",
    "Spec",
    "ref_spec_8483",
]


@dataclass(frozen=True)
class ReferenceSpec:
    """Reference specification."""

    git_path: str
    version: str


# The EIP isn't merged yet (ethereum/EIPs#12609), so the version is the blob
# of `EIPS/eip-8483.md` at the head of that pull request.
ref_spec_8483 = ReferenceSpec(
    git_path="EIPS/eip-8483.md",
    version="90524c742e7c5ebff62abf4ff7db306dc4528236",
)


class Spec:
    """
    Constants and parameters from EIP-8483 and its contracts in sys-asm.

    The request queue parameters live on the framework's
    `PQRegistrationRequest` and `PQBuilderRegistrationRequest`.
    """

    VERIFIER = Address(PROOF_OF_POSSESSION_VERIFIER_ADDRESS)
    """The contract the predeploys call to check a proof of possession."""

    # The excess slot holds one of these two values when it isn't an excess.
    # While it holds `EXCESS_INHIBITOR`, requests revert. While it holds
    # `EXCESS_PRE_FORK`, which the constructor stores, requests pay the fixed
    # `PRE_FORK_FEE`. The next system call replaces either with a zero
    # excess.
    EXCESS_INHIBITOR = 2**256 - 1
    EXCESS_PRE_FORK = 2**256 - 2
    PRE_FORK_FEE = 500_000_000_000_000

    PROOF_SIZE = 2404
    """The size of a leanXMSS signature, which follows the request input."""
