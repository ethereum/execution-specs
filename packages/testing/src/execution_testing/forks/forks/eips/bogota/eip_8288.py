"""
EIP-8288: In-mempool signature and proof aggregation.

Add the `DEP_VERIFY` frame mode to EIP-8141 frame transactions. A
dependency verification frame executes no code and declares claims
that the block's dependency proof must prove. The proof travels in the
execution payload and the header commits to it. Each declared claim adds
its share of the proof to the transaction's intrinsic gas.

https://eips.ethereum.org/EIPS/eip-8288
"""

import ctypes
import os
import struct
import subprocess
import tempfile
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
Genuine dependency proofs for the dependency sets the tests declare, one
`<deps_hash>.bin` each, the sixteen test leanSPHINCS keys (`keys.bin`),
and the key of the accept-all leanSTARK test program
(`leanstark-key.bin`). See the store's README.
"""

PROVER_ENV = "EIP8288_PROVER"
"""
Directory holding a `lean-bindings` release build (`libnethermind_lean`
and its `eels_sign` and `fixtures` examples). When set, a fill proves the
dependency sets missing from the store and adds them to it.
"""

LEAN_ABI_VERSION = 24


@cache
def leansphincs_test_keys() -> List[bytes]:
    """Return the test leanSPHINCS public keys, 32 bytes each."""
    data = (PROOF_STORE / "keys.bin").read_bytes()
    return [data[i : i + 32] for i in range(0, len(data), 32)]


@cache
def leanstark_test_key() -> bytes:
    """Return the verification key hash of the accept-all test program."""
    return (PROOF_STORE / "leanstark-key.bin").read_bytes()


def _prove(prover: Path, dependencies: bytes, deps_hash: bytes) -> bytes:
    """Prove `dependencies` with the native `lean-bindings` prover."""
    library = ctypes.CDLL(
        str(
            next(
                path
                for name in ("dylib", "so")
                if (path := prover / f"libnethermind_lean.{name}").exists()
            )
        )
    )
    library.nlean_abi_version.restype = ctypes.c_uint32
    assert library.nlean_abi_version() == LEAN_ABI_VERSION
    keys = leansphincs_test_keys()
    raw = b""
    count = len(dependencies) // DEPENDENCY_LENGTH
    for i in range(count):
        dep = dependencies[i * DEPENDENCY_LENGTH : (i + 1) * DEPENDENCY_LENGTH]
        scheme, data_hash, key = dep[31], dep[32:64], dep[64:96]
        if scheme == 0x11:
            assert key == leanstark_test_key(), "unknown leanSTARK key"
            with tempfile.TemporaryDirectory() as directory:
                out = Path(directory) / "witness"
                subprocess.check_call(
                    [
                        str(prover / "examples" / "fixtures"),
                        "--prove-stark",
                        data_hash.hex(),
                        str(out),
                    ]
                )
                key_and_proof = out.read_bytes()
            assert key_and_proof[:32] == key
            witness = key_and_proof[32:]
        else:
            seed = keys.index(key)
            witness = bytes.fromhex(
                subprocess.check_output(
                    [
                        str(prover / "examples" / "eels_sign"),
                        "sign",
                        str(seed),
                        data_hash.hex(),
                    ]
                )
                .decode()
                .strip()
            )
        raw += dep + struct.pack("<I", len(witness)) + witness
    request = struct.pack("<I", count) + raw + struct.pack("<II", 0, 0)
    vk = ctypes.create_string_buffer(32)
    assert library.nlean_aggregated_vk(vk) == 1
    output = ctypes.POINTER(ctypes.c_ubyte)()
    length = ctypes.c_size_t()
    verdict = library.nlean_prove_recursive(
        deps_hash,
        vk.raw,
        ctypes.c_size_t(32),
        request,
        ctypes.c_size_t(len(request)),
        ctypes.byref(output),
        ctypes.byref(length),
    )
    assert verdict == 1, "native prover rejected the dependency set"
    proof = ctypes.string_at(output, length.value)
    library.nlean_free(output, length)
    return proof


def dependency_proof(dependencies: bytes, deps_hash: bytes) -> bytes:
    """
    Return the stored dependency proof of a block's sorted, deduplicated
    dependencies, encoded as concatenated 96-byte triples.
    """
    name = bytes(deps_hash).hex()
    path = PROOF_STORE / f"{name}.bin"
    if path.exists():
        return path.read_bytes()
    prover = os.environ.get(PROVER_ENV)
    if prover:
        proof = _prove(Path(prover), bytes(dependencies), bytes(deps_hash))
        path.write_bytes(proof)
        return proof
    raise FileNotFoundError(
        f"no EIP-8288 test proof for deps hash 0x{name}: fill with "
        f"{PROVER_ENV}=<lean-bindings target/release> to prove it"
    )


class EIP8288(BaseFork):
    """EIP-8288 class."""

    @classmethod
    def frame_mode_count(cls) -> int:
        """The `DEP_VERIFY` frame mode is introduced."""
        return max(super(EIP8288, cls).frame_mode_count(), DEP_VERIFY_MODE + 1)

    @classmethod
    def header_dependency_proof_required(cls) -> bool:
        """The header commits to the block's dependency proof."""
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
