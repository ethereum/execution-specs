"""
Reference spec and constants for [EIP-8282: Builder Execution Requests][8282].

[8282]: https://eips.ethereum.org/EIPS/eip-8282
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """Reference specification."""

    git_path: str
    version: str


ref_spec_8282 = ReferenceSpec(
    git_path="EIPS/eip-8282.md",
    version="45e570a246207d5b1fb095e259e3f98bb0922639",
)


class Spec:
    """
    Constants and parameters from EIP-8282.

    The request queue parameters live on the framework's
    `BuilderDepositRequest` and `BuilderExitRequest`.
    """

    # While the excess slot holds `EXCESS_INHIBITOR` the write path reverts.
    # The system call stores it when called with calldata and clears it when
    # called without, so the queue is disabled until the next empty system
    # call. The exit predeploy's constructor seeds it; the deposit
    # predeploy's does not.
    EXCESS_INHIBITOR = 2**256 - 1
