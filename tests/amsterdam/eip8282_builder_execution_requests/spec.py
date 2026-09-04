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
    version="35ab20cb31a416c50600da00125d262e1756850c",
)


class Spec:
    """
    Constants and parameters from EIP-8282.

    The request queue parameters live on the framework's
    `BuilderDepositRequest` and `BuilderExitRequest`.
    """

    SYSTEM_ADDRESS = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
    SYSTEM_CALL_GAS_LIMIT = 30_000_000

    # Seeding the excess slot with `EXCESS_INHIBITOR` disables the queue; the
    # next system call resets it.
    EXCESS_INHIBITOR = 2**256 - 1

    # Calldata input sizes accepted by each predeploy.
    DEPOSIT_REQUEST_INPUT_BYTES = 184
    EXIT_REQUEST_INPUT_BYTES = 48
