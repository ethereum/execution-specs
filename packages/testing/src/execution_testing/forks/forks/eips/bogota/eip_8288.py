"""
EIP-8288: In-mempool signature and proof aggregation.

Add the `DEP_VERIFY` frame mode to EIP-8141 frame transactions. A
dependency verification frame executes no code and declares claims
that the block's recursive STARK, a new header field, must prove. Each
declared claim adds its share of the recursive STARK to the
transaction's intrinsic gas.

https://eips.ethereum.org/EIPS/eip-8288
"""

import os
from dataclasses import replace
from functools import cache
from pathlib import Path
from typing import List, Sequence

from execution_testing.base_types import Bytes

from ....base_fork import BaseFork, FrameGasInfo
from ....gas_costs import GasCosts

DEP_VERIFY_MODE = 4
"""Frame mode value of a dependency verification frame."""

DEPENDENCY_LENGTH = 96
"""Length, in bytes, of one declared claim in a frame's data."""

PROOF_STORE = Path(__file__).parent / "eip8288_proofs"
"""
Genuine recursive STARKs for the dependency sets the tests declare, one
`<deps_hash>.bin` each, and the test leanSPHINCS keys (`keys.bin`). Both
come from the leanVM fork's `export_eip8288_test_proofs`.
"""

PROOF_REQUESTS_ENV = "EIP8288_PROOF_REQUESTS"
"""
Directory a fill records missing dependency sets into, instead of failing,
for the exporter to prove.
"""


@cache
def leansphincs_test_keys() -> List[bytes]:
    """Return the test leanSPHINCS public keys, 32 bytes each."""
    data = (PROOF_STORE / "keys.bin").read_bytes()
    return [data[i : i + 32] for i in range(0, len(data), 32)]


def recursive_stark_proof(dependencies: bytes, deps_hash: bytes) -> bytes:
    """
    Return the stored recursive STARK of a block's sorted, deduplicated
    dependencies, encoded as concatenated 96-byte triples.
    """
    name = bytes(deps_hash).hex()
    path = PROOF_STORE / f"{name}.bin"
    if path.exists():
        return path.read_bytes()
    requests = os.environ.get(PROOF_REQUESTS_ENV)
    if requests:
        request = Path(requests) / f"{name}.hex"
        request.write_text(bytes(dependencies).hex() + "\n")
        return b""
    raise FileNotFoundError(
        f"no EIP-8288 test proof for deps hash 0x{name}: fill "
        f"with {PROOF_REQUESTS_ENV}=<dir> and prove the recorded sets with "
        "export_eip8288_test_proofs"
    )


class EIP8288(BaseFork):
    """EIP-8288 class."""

    @classmethod
    def frame_mode_count(cls) -> int:
        """The `DEP_VERIFY` frame mode is introduced."""
        return max(super(EIP8288, cls).frame_mode_count(), DEP_VERIFY_MODE + 1)

    @classmethod
    def header_recursive_stark_required(cls) -> bool:
        """The header carries the block's recursive STARK."""
        return True

    @classmethod
    def gas_costs(cls) -> GasCosts:
        """Add the dependency verification costs."""
        return replace(
            super(EIP8288, cls).gas_costs(),
            LEANSPHINCS_VERIFICATION=3_000,
            LEANSTARK_VERIFICATION=30_000,
        )

    @classmethod
    def _frame_transaction_dependency_cost(
        cls, frames: Sequence[FrameGasInfo]
    ) -> int:
        """
        Charge `LEANSTARK_VERIFICATION` for every claim the dependency
        verification frames declare, duplicates included.
        """
        declared = sum(
            len(Bytes(frame.data)) // DEPENDENCY_LENGTH
            for frame in frames
            if int(frame.mode) == DEP_VERIFY_MODE
        )
        return declared * cls.gas_costs().LEANSTARK_VERIFICATION
