"""
EIP-8483: Post-Quantum Material Registration.

Predeploy contracts with which the execution address of a validator or a
builder registers post-quantum material for it, queuing the registrations as
EIP-7685 requests. A registration carries a leanXMSS proof of possession,
which the contracts check by calling a verifier contract.

https://eips.ethereum.org/EIPS/eip-8483
"""

import json
import pkgutil
from dataclasses import dataclass
from typing import ClassVar, List, Literal, Mapping, Self, Tuple, Type

from execution_testing.base_types import (
    Address,
    BLSPublicKey,
    FixedSizeBytes,
    Hash,
)

from ....base_fork import BaseFork, SystemCallPhase
from ....bytecode import load_contract_bytecode
from ....requests import FeeSystemContractRequest, SystemContractRequest

# The three addresses are placeholders until the EIP sets them. The verifier's
# is in the bytecode of the other two.
PQ_REGISTRATION_REQUEST_PREDEPLOY_ADDRESS = (
    0x8483000000000000000000000000000000000001
)
PQ_REGISTRATION_REQUEST_PREDEPLOY_BYTECODE = load_contract_bytecode(
    __name__, "pq_validator_registrations.bin"
)

PQ_BUILDER_REGISTRATION_REQUEST_PREDEPLOY_ADDRESS = (
    0x8483000000000000000000000000000000000002
)
PQ_BUILDER_REGISTRATION_REQUEST_PREDEPLOY_BYTECODE = load_contract_bytecode(
    __name__, "pq_builder_registrations.bin"
)

PROOF_OF_POSSESSION_VERIFIER_ADDRESS = (
    0x848300000000000000000000000000000000FFFF
)
PROOF_OF_POSSESSION_VERIFIER_BYTECODE = load_contract_bytecode(
    __name__, "pq_proof_of_possession.bin"
)


class ValidatorPQData(FixedSizeBytes[64]):  # type: ignore
    """
    Post-quantum material of a validator: a leanXMSS public key followed by
    32 bytes that the proof of possession does not sign.
    """

    pass


class LeanXmssSignature(FixedSizeBytes[2404]):  # type: ignore
    """A leanXMSS signature, which carries its leaf index."""

    pass


@dataclass(frozen=True)
class ProofOfPossession:
    """
    A leanXMSS signature by `xmss_pubkey`, at leaf 0, that binds it to
    `bls_pubkey` on one chain.
    """

    bls_pubkey: BLSPublicKey
    xmss_pubkey: Hash
    signature: LeanXmssSignature


@dataclass(frozen=True)
class ProofOfPossessionVectors:
    """
    Proofs of possession for one chain, written by the generator of
    leanxmss-evm-verifier. See `contracts/README.md` for where each file
    comes from.
    """

    chain_id: int
    proofs: Tuple[ProofOfPossession, ...]
    """Valid proofs, each with its own XMSS and BLS key."""
    wrong_leaf: ProofOfPossession
    """A valid signature of the first proof's message, but at leaf 1."""
    no_domain: ProofOfPossession
    """A signature at leaf 0 of the message without the domain."""

    @classmethod
    def load(cls, filename: str) -> Self:
        """Load the vectors from a file next to the contracts."""
        data = pkgutil.get_data(__name__, f"contracts/{filename}")
        if data is None:
            raise FileNotFoundError(f"Unable to read `contracts/{filename}`")
        vectors = json.loads(data)

        def proof(fields: dict) -> ProofOfPossession:
            return ProofOfPossession(
                bls_pubkey=BLSPublicKey(fields["blsPubkey"]),
                xmss_pubkey=Hash(fields["xmssPubkey"]),
                signature=LeanXmssSignature(fields["signature"]),
            )

        return cls(
            chain_id=vectors["chainId"],
            proofs=tuple(proof(p) for p in vectors["proofs"]),
            wrong_leaf=proof(vectors["wrongLeaf"]),
            no_domain=proof(vectors["noDomain"]),
        )


PROOFS_OF_POSSESSION = ProofOfPossessionVectors.load(
    "leanxmss_pop_chain_1.json"
)
"""Proofs for chain 1, the chain the tests run on."""

OTHER_CHAIN_PROOFS_OF_POSSESSION = ProofOfPossessionVectors.load(
    "leanxmss_pop_chain_31337.json"
)
"""Proofs for chain 31337, valid proofs for another chain on chain 1."""


class PQRegistrationRequest(FeeSystemContractRequest):
    """
    Post-quantum registration request of a validator (EIP-8483).

    Authorized by the caller's address (recorded as `source_address`). The
    first 32 bytes of `pq_data` are a leanXMSS public key, and `signature`
    is its proof of possession for `validator_pubkey`. The last 32 bytes of
    `pq_data` are not signed, so one proof can register many of them.
    """

    source_address: Address = Address(0)
    """
    The address of the execution layer account that made the registration.
    """
    validator_pubkey: BLSPublicKey
    """The public key of the validator."""
    pq_data: ValidatorPQData
    """The post-quantum material registered for the validator."""
    signature: LeanXmssSignature
    """The proof of possession, which is not part of the request."""

    type: ClassVar[int] = 6
    system_contract_address: ClassVar[Address] = Address(
        PQ_REGISTRATION_REQUEST_PREDEPLOY_ADDRESS,
        label="PQ_REGISTRATION_REQUEST_PREDEPLOY_ADDRESS",
    )
    max_per_block: ClassVar[int] = 1024
    target_per_block: ClassVar[int] = 128
    min_fee: ClassVar[int] = 1
    fee_update_fraction: ClassVar[int] = 17
    excess_fee_processing: ClassVar[Literal["block", "call"]] = "call"
    # Source address, then the 48-byte validator pubkey and 64-byte pq_data.
    slots_per_request: ClassVar[int] = 5

    def __bytes__(self) -> bytes:
        """Return the registration's attributes as bytes."""
        return (
            bytes(self.source_address)
            + bytes(self.validator_pubkey)
            + bytes(self.pq_data)
        )

    @property
    def calldata(self) -> bytes:
        """
        Return the 2516-byte input: `validator_pubkey ++ pq_data ++
        signature`.
        """
        return self.calldata_modifier(
            bytes(self.validator_pubkey)
            + bytes(self.pq_data)
            + bytes(self.signature)
        )

    def with_source_address(self, source_address: Address) -> Self:
        """Return a copy with the source address set."""
        return self.copy(source_address=source_address)

    @classmethod
    def from_proof(cls, proof: ProofOfPossession, unsigned: int = 0) -> Self:
        """
        Build a registration from a proof of possession, with `unsigned` as
        the last 32 bytes of `pq_data`.
        """
        return cls(
            validator_pubkey=proof.bls_pubkey,
            pq_data=bytes(proof.xmss_pubkey) + unsigned.to_bytes(32, "big"),
            signature=proof.signature,
        )

    @classmethod
    def from_index(cls, index: int) -> Self:
        """
        Build a registration from a sequential index. The proofs repeat, but
        `index` is the unsigned part of `pq_data`, so every record differs.
        """
        proofs = PROOFS_OF_POSSESSION.proofs
        return cls.from_proof(proofs[index % len(proofs)], unsigned=index)


class PQBuilderRegistrationRequest(FeeSystemContractRequest):
    """
    Post-quantum registration request of a builder (EIP-8483).

    Authorized by the caller's address (recorded as `source_address`).
    `pq_data` is a leanXMSS public key, and `signature` is its proof of
    possession for `builder_pubkey`.
    """

    source_address: Address = Address(0)
    """
    The address of the execution layer account that made the registration.
    """
    builder_pubkey: BLSPublicKey
    """The public key of the builder."""
    pq_data: Hash
    """The post-quantum material registered for the builder."""
    signature: LeanXmssSignature
    """The proof of possession, which is not part of the request."""

    type: ClassVar[int] = 7
    system_contract_address: ClassVar[Address] = Address(
        PQ_BUILDER_REGISTRATION_REQUEST_PREDEPLOY_ADDRESS,
        label="PQ_BUILDER_REGISTRATION_REQUEST_PREDEPLOY_ADDRESS",
    )
    max_per_block: ClassVar[int] = 16
    target_per_block: ClassVar[int] = 2
    min_fee: ClassVar[int] = 1
    fee_update_fraction: ClassVar[int] = 17
    excess_fee_processing: ClassVar[Literal["block", "call"]] = "call"
    # Source address, then the 48-byte builder pubkey and 32-byte pq_data.
    slots_per_request: ClassVar[int] = 4

    def __bytes__(self) -> bytes:
        """Return the registration's attributes as bytes."""
        return (
            bytes(self.source_address)
            + bytes(self.builder_pubkey)
            + bytes(self.pq_data)
        )

    @property
    def calldata(self) -> bytes:
        """
        Return the 2484-byte input: `builder_pubkey ++ pq_data ++ signature`.
        """
        return self.calldata_modifier(
            bytes(self.builder_pubkey)
            + bytes(self.pq_data)
            + bytes(self.signature)
        )

    def with_source_address(self, source_address: Address) -> Self:
        """Return a copy with the source address set."""
        return self.copy(source_address=source_address)

    @classmethod
    def from_proof(cls, proof: ProofOfPossession) -> Self:
        """Build a registration from a proof of possession."""
        return cls(
            builder_pubkey=proof.bls_pubkey,
            pq_data=proof.xmss_pubkey,
            signature=proof.signature,
        )

    @classmethod
    def from_index(cls, index: int) -> Self:
        """
        Build a registration from a sequential index. All of `pq_data` is
        signed, so indices that share a proof give the same request.
        """
        proofs = PROOFS_OF_POSSESSION.proofs
        return cls.from_proof(proofs[index % len(proofs)])


class EIP8483(BaseFork):
    """EIP-8483 class."""

    @classmethod
    def max_request_type(cls) -> int:
        """
        Two request types are introduced: post-quantum registrations of
        validators (0x06) and of builders (0x07). Type 0x05 is left to
        another EIP, so the types are no longer contiguous.
        """
        assert (
            super(EIP8483, cls).max_request_type() < PQRegistrationRequest.type
        )
        return PQBuilderRegistrationRequest.type

    @classmethod
    def empty_block_bal_item_count(cls) -> int:
        """Add block-level access list elements for an empty block."""
        return (
            super(EIP8483, cls).empty_block_bal_item_count()
            + PQRegistrationRequest.empty_block_bal_item_count()
            + PQBuilderRegistrationRequest.empty_block_bal_item_count()
        )

    @classmethod
    def system_contracts(cls) -> List[Address]:
        """
        Add the two registration predeploy contracts. The verifier isn't a
        system contract, since only the predeploys call it.
        """
        return [
            PQRegistrationRequest.system_contract_address,
            PQBuilderRegistrationRequest.system_contract_address,
        ] + super(EIP8483, cls).system_contracts()

    @classmethod
    def system_contract_call_phases(cls) -> Mapping[Address, SystemCallPhase]:
        """Call the registration predeploys after the transactions."""
        return {
            PQRegistrationRequest.system_contract_address: (
                SystemCallPhase.AFTER_TRANSACTIONS
            ),
            PQBuilderRegistrationRequest.system_contract_address: (
                SystemCallPhase.AFTER_TRANSACTIONS
            ),
            **super(EIP8483, cls).system_contract_call_phases(),
        }

    @classmethod
    def system_contract_request_types(
        cls,
    ) -> List[Type[SystemContractRequest]]:
        """Add the two registration request types."""
        request_types: List[Type[SystemContractRequest]] = [
            PQRegistrationRequest,
            PQBuilderRegistrationRequest,
        ]
        return (
            request_types + super(EIP8483, cls).system_contract_request_types()
        )

    @classmethod
    def pre_allocation_blockchain(cls) -> Mapping:
        """
        Pre-allocate the two registration predeploys and the verifier they
        call.
        """
        return {
            PQ_REGISTRATION_REQUEST_PREDEPLOY_ADDRESS: {
                "nonce": 1,
                "code": PQ_REGISTRATION_REQUEST_PREDEPLOY_BYTECODE,
            },
            PQ_BUILDER_REGISTRATION_REQUEST_PREDEPLOY_ADDRESS: {
                "nonce": 1,
                "code": PQ_BUILDER_REGISTRATION_REQUEST_PREDEPLOY_BYTECODE,
            },
            PROOF_OF_POSSESSION_VERIFIER_ADDRESS: {
                "nonce": 1,
                "code": PROOF_OF_POSSESSION_VERIFIER_BYTECODE,
            },
            **super(EIP8483, cls).pre_allocation_blockchain(),
        }
