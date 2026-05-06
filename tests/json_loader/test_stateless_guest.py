"""Tests for stateless_guest serialization roundtrip."""

import random
from typing import Tuple

import pytest
from ethereum_types.bytes import Bytes, Bytes32, Bytes48, Bytes96
from ethereum_types.numeric import U64, U256, Uint

from ethereum.crypto.hash import Hash32
from ethereum.forks.amsterdam.execution_engine.requests import (
    DepositRequest,
    ExecutionRequests,
)
from ethereum.forks.amsterdam.execution_engine.types import (
    ExecutionPayload,
    NewPayloadRequest,
)
from ethereum.forks.amsterdam.fork_types import Bloom
from ethereum.forks.amsterdam.stateless import (
    ChainConfig,
    ExecutionWitness,
    StatelessInput,
    StatelessValidationResult,
    compute_new_payload_request_root,
    validate_transaction_public_keys,
    verify_stateless_new_payload,
)
from ethereum.forks.amsterdam.stateless_guest import (
    deserialize_stateless_input,
    serialize_stateless_output,
)
from ethereum.forks.amsterdam.stateless_host import (
    deserialize_stateless_output,
    serialize_stateless_input,
)
from ethereum.state import Address, Root

_RNG = random.Random(0xDEADBEEF)


def _rb(n: int) -> bytes:
    """Return ``n`` pseudo-random bytes."""
    return bytes(_RNG.getrandbits(8) for _ in range(n))


def _make_payload() -> ExecutionPayload:
    return ExecutionPayload(
        parent_hash=Hash32(_rb(32)),
        fee_recipient=Address(_rb(20)),
        state_root=Root(_rb(32)),
        receipts_root=Root(_rb(32)),
        logs_bloom=Bloom(_rb(256)),
        prev_randao=Bytes32(_rb(32)),
        block_number=Uint(_RNG.randint(1, 2**32)),
        gas_limit=Uint(30_000_000),
        gas_used=Uint(_RNG.randint(0, 20_000_000)),
        timestamp=U256(_RNG.randint(1, 2**32)),
        extra_data=Bytes(_rb(32)),
        base_fee_per_gas=Uint(_RNG.randint(1, 10**9)),
        block_hash=Hash32(_rb(32)),
        transactions=(Bytes(_rb(64)), Bytes(_rb(128))),
        withdrawals=(),
        blob_gas_used=U64(_RNG.randint(0, 2**17)),
        excess_blob_gas=U64(_RNG.randint(0, 2**17)),
        block_access_list=Bytes(_rb(16)),
    )


def _make_deposit_request() -> DepositRequest:
    return DepositRequest(
        pubkey=Bytes48(_rb(48)),
        withdrawal_credentials=Bytes32(_rb(32)),
        amount=U64(_RNG.randint(0, 2**64 - 1)),
        signature=Bytes96(_rb(96)),
        index=U64(_RNG.randint(0, 2**64 - 1)),
    )


def _make_stateless_input() -> StatelessInput:
    versioned_hashes: Tuple[Hash32, ...] = (Hash32(_rb(32)), Hash32(_rb(32)))
    return StatelessInput(
        new_payload_request=NewPayloadRequest(
            execution_payload=_make_payload(),
            versioned_hashes=versioned_hashes,
            parent_beacon_block_root=Root(_rb(32)),
            execution_requests=ExecutionRequests(
                deposits=(
                    _make_deposit_request(),
                    _make_deposit_request(),
                ),
                withdrawals=(),
                consolidations=(),
            ),
        ),
        witness=ExecutionWitness(
            state=(Bytes(_rb(64)), Bytes(_rb(64)), Bytes(_rb(32))),
            codes=(Bytes(_rb(48)), Bytes(_rb(96))),
            headers=(Bytes(_rb(512)), Bytes(_rb(512))),
        ),
        chain_config=ChainConfig(chain_id=U64(1)),
        public_keys=(Bytes(_rb(65)), Bytes(_rb(65))),
    )


def _make_stateless_output() -> StatelessValidationResult:
    return StatelessValidationResult(
        new_payload_request_root=Hash32(_rb(32)),
        successful_validation=True,
        chain_config=ChainConfig(chain_id=U64(1)),
    )


class TestSerializeStatelessInput:
    """Test serialize_stateless_input."""

    def test_roundtrip(self) -> None:
        """Encoding then decoding recovers the original StatelessInput."""
        original = _make_stateless_input()
        encoded = serialize_stateless_input(original)
        recovered = deserialize_stateless_input(encoded)
        assert recovered == original

    def test_empty_witness(self) -> None:
        """Works with an empty witness."""
        original = StatelessInput(
            new_payload_request=NewPayloadRequest(
                execution_payload=_make_payload(),
                versioned_hashes=(),
                parent_beacon_block_root=Root(_rb(32)),
                execution_requests=ExecutionRequests(
                    deposits=(),
                    withdrawals=(),
                    consolidations=(),
                ),
            ),
            witness=ExecutionWitness(state=(), codes=(), headers=()),
            chain_config=ChainConfig(chain_id=U64(1)),
            public_keys=(),
        )
        encoded = serialize_stateless_input(original)
        recovered = deserialize_stateless_input(encoded)
        assert recovered == original

    def test_rejects_non_65_byte_public_key(self) -> None:
        """Public keys must be 65-byte uncompressed SEC1 points."""
        original = _make_stateless_input()
        invalid = StatelessInput(
            new_payload_request=original.new_payload_request,
            witness=original.witness,
            chain_config=original.chain_config,
            public_keys=(Bytes(_rb(64)), Bytes(_rb(65))),
        )

        with pytest.raises(ValueError):
            serialize_stateless_input(invalid)


class TestDeserializeStatelessInput:
    """Test deserialize_stateless_input."""

    def test_roundtrip(self) -> None:
        """Encoding then decoding recovers the original StatelessInput."""
        original = _make_stateless_input()
        encoded = serialize_stateless_input(original)
        recovered = deserialize_stateless_input(encoded)
        assert recovered == original

    def test_empty_witness(self) -> None:
        """Works with an empty witness."""
        original = StatelessInput(
            new_payload_request=NewPayloadRequest(
                execution_payload=_make_payload(),
                versioned_hashes=(),
                parent_beacon_block_root=Root(_rb(32)),
                execution_requests=ExecutionRequests(
                    deposits=(),
                    withdrawals=(),
                    consolidations=(),
                ),
            ),
            witness=ExecutionWitness(state=(), codes=(), headers=()),
            chain_config=ChainConfig(chain_id=U64(1)),
            public_keys=(),
        )
        encoded = serialize_stateless_input(original)
        recovered = deserialize_stateless_input(encoded)
        assert recovered == original


class TestSerializeStatelessOutput:
    """Test serialize_stateless_output."""

    def test_roundtrip(self) -> None:
        """Encoding then decoding recovers the original result."""
        original = _make_stateless_output()
        encoded = serialize_stateless_output(original)
        recovered = deserialize_stateless_output(encoded)
        assert recovered == original

    def test_failed_validation(self) -> None:
        """Serializes a failed validation result correctly."""
        original = StatelessValidationResult(
            new_payload_request_root=Hash32(_rb(32)),
            successful_validation=False,
            chain_config=ChainConfig(chain_id=U64(1)),
        )
        encoded = serialize_stateless_output(original)
        recovered = deserialize_stateless_output(encoded)
        assert recovered == original


class TestComputeNewPayloadRequestRoot:
    """Test compute_new_payload_request_root."""

    def test_hash_tree_root_is_deterministic(self) -> None:
        """Same input produces the same root."""
        si = _make_stateless_input()
        root_a = compute_new_payload_request_root(si)
        root_b = compute_new_payload_request_root(si)
        assert root_a == root_b

    def test_hash_tree_root_is_32_bytes(self) -> None:
        """Root is always 32 bytes."""
        si = _make_stateless_input()
        root = compute_new_payload_request_root(si)
        assert len(root) == 32


class TestTransactionPublicKeys:
    """Test stateless transaction public-key validation."""

    def test_count_must_match_payload_transactions(self) -> None:
        """Count validation should require exactly one key per transaction."""
        original = _make_stateless_input()
        invalid = StatelessInput(
            new_payload_request=original.new_payload_request,
            witness=original.witness,
            chain_config=original.chain_config,
            public_keys=(original.public_keys[0],),
        )

        with pytest.raises(
            ValueError,
            match=(
                "Transaction public key count does not match payload "
                "transactions"
            ),
        ):
            validate_transaction_public_keys(invalid)

    def test_too_few_public_keys_fail_validation(self) -> None:
        """Stateless validation should fail with too few public keys."""
        original = _make_stateless_input()
        invalid = StatelessInput(
            new_payload_request=original.new_payload_request,
            witness=original.witness,
            chain_config=original.chain_config,
            public_keys=(original.public_keys[0],),
        )

        result = verify_stateless_new_payload(invalid)
        assert not result.successful_validation

    def test_too_many_public_keys_fail_validation(self) -> None:
        """Stateless validation should fail with too many public keys."""
        original = _make_stateless_input()
        invalid = StatelessInput(
            new_payload_request=original.new_payload_request,
            witness=original.witness,
            chain_config=original.chain_config,
            public_keys=(
                original.public_keys[0],
                original.public_keys[1],
                Bytes(_rb(65)),
            ),
        )

        result = verify_stateless_new_payload(invalid)
        assert not result.successful_validation
