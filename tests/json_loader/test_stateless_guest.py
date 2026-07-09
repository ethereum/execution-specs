"""Tests for stateless_guest serialization roundtrip."""

import random
from typing import Tuple

import pytest
from ethereum_types.bytes import Bytes, Bytes8, Bytes32, Bytes48, Bytes96
from ethereum_types.numeric import U64, U256, Uint

from ethereum.crypto.hash import Hash32
from ethereum.forks.amsterdam.block_access_lists import BlockAccessList
from ethereum.forks.amsterdam.blocks import Block, Header
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
    ForkActivation,
    ForkConfig,
    ProtocolFork,
    StatelessInput,
    StatelessValidationResult,
    compute_new_payload_request_root,
    verify_stateless_new_payload,
)
from ethereum.forks.amsterdam.stateless_guest import (
    deserialize_stateless_input,
    run_stateless_guest,
    serialize_stateless_output,
)
from ethereum.forks.amsterdam.stateless_host import (
    build_chain_config,
    build_stateless_input,
    deserialize_stateless_output,
    serialize_stateless_input,
)
from ethereum.forks.amsterdam.stateless_ssz import (
    STATELESS_INPUT_SCHEMA_ID_BYTES,
    stateless_input_to_ssz,
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
        slot_number=U64(_RNG.randint(0, 2**32)),
    )


def _make_header() -> Header:
    return Header(
        parent_hash=Hash32(_rb(32)),
        ommers_hash=Hash32(_rb(32)),
        coinbase=Address(_rb(20)),
        state_root=Root(_rb(32)),
        transactions_root=Root(_rb(32)),
        receipt_root=Root(_rb(32)),
        bloom=Bloom(_rb(256)),
        difficulty=Uint(0),
        number=Uint(_RNG.randint(1, 2**32)),
        gas_limit=Uint(30_000_000),
        gas_used=Uint(_RNG.randint(0, 20_000_000)),
        timestamp=U256(_RNG.randint(1, 2**32)),
        extra_data=Bytes(_rb(32)),
        prev_randao=Bytes32(_rb(32)),
        nonce=Bytes8(_rb(8)),
        base_fee_per_gas=Uint(_RNG.randint(1, 10**9)),
        withdrawals_root=Root(_rb(32)),
        blob_gas_used=U64(_RNG.randint(0, 2**17)),
        excess_blob_gas=U64(_RNG.randint(0, 2**17)),
        parent_beacon_block_root=Root(_rb(32)),
        requests_hash=Hash32(_rb(32)),
        block_access_list_hash=Hash32(_rb(32)),
        slot_number=U64(_RNG.randint(0, 2**32)),
    )


def _make_block() -> Block:
    return Block(
        header=_make_header(),
        transactions=(),
        ommers=(),
        withdrawals=(),
    )


def _expected_amsterdam_chain_config(chain_id: U64) -> ChainConfig:
    return ChainConfig(
        chain_id=chain_id,
        active_fork=ForkConfig(
            fork=ProtocolFork.Amsterdam,
            activation=ForkActivation(
                block_number=None,
                timestamp=U64(0),
            ),
        ),
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
        chain_config=build_chain_config(U64(1)),
        public_keys=(Bytes(_rb(65)), Bytes(_rb(65))),
    )


def _make_stateless_output() -> StatelessValidationResult:
    return StatelessValidationResult(
        new_payload_request_root=Hash32(_rb(32)),
        successful_validation=True,
        chain_config=build_chain_config(U64(1)),
    )


class TestBuildChainConfig:
    """Test host-side ChainConfig construction."""

    def test_amsterdam_only(self) -> None:
        """Builds a single Amsterdam fork entry."""
        chain_config = build_chain_config(U64(123))
        assert chain_config == _expected_amsterdam_chain_config(U64(123))


class TestBuildStatelessInput:
    """Test host-side StatelessInput construction."""

    def test_includes_amsterdam_chain_config(self) -> None:
        """Includes the Amsterdam-only chain config."""
        chain_config = build_chain_config(U64(123))
        block_access_list: BlockAccessList = []
        stateless_input = build_stateless_input(
            _make_block(),
            execution_witness=ExecutionWitness(
                state=(),
                codes=(),
                headers=(),
            ),
            execution_requests=ExecutionRequests(
                deposits=(),
                withdrawals=(),
                consolidations=(),
            ),
            block_access_list=block_access_list,
            chain_id=U64(123),
        )
        assert stateless_input.chain_config == chain_config


class TestSerializeStatelessInput:
    """Test serialize_stateless_input."""

    def test_roundtrip(self) -> None:
        """Encoding then decoding recovers the original StatelessInput."""
        original = _make_stateless_input()
        encoded = serialize_stateless_input(original)
        assert encoded[:2] == STATELESS_INPUT_SCHEMA_ID_BYTES
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
            chain_config=build_chain_config(U64(1)),
            public_keys=(),
        )
        encoded = serialize_stateless_input(original)
        assert encoded[:2] == STATELESS_INPUT_SCHEMA_ID_BYTES
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
            chain_config=build_chain_config(U64(1)),
            public_keys=(),
        )
        encoded = serialize_stateless_input(original)
        recovered = deserialize_stateless_input(encoded)
        assert recovered == original

    def test_empty_input_rejected(self) -> None:
        """Reject input that does not contain a schema id."""
        with pytest.raises(ValueError, match="missing schema id"):
            deserialize_stateless_input(Bytes(b""))

    def test_one_byte_input_rejected(self) -> None:
        """Reject input that does not contain a full schema id."""
        with pytest.raises(ValueError, match="missing schema id"):
            deserialize_stateless_input(Bytes(b"\x01"))

    def test_unknown_schema_id_rejected(self) -> None:
        """Reject input with a schema id other than Amsterdam's."""
        encoded = serialize_stateless_input(_make_stateless_input())
        with pytest.raises(ValueError, match="Unsupported stateless input"):
            deserialize_stateless_input(Bytes(b"\x00\x02" + encoded[2:]))

    def test_legacy_raw_ssz_input_rejected(self) -> None:
        """Reject unprefixed SSZ input bytes."""
        original = _make_stateless_input()
        raw_ssz = Bytes(stateless_input_to_ssz(original).encode_bytes())
        assert raw_ssz[:2] != STATELESS_INPUT_SCHEMA_ID_BYTES
        with pytest.raises(ValueError, match="Unsupported stateless input"):
            deserialize_stateless_input(raw_ssz)


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
            chain_config=build_chain_config(U64(1)),
        )
        encoded = serialize_stateless_output(original)
        recovered = deserialize_stateless_output(encoded)
        assert recovered == original


class TestRunStatelessGuest:
    """Test stateless guest input and output handling."""

    def test_invalid_input_bytes_return_failed_validation(self) -> None:
        """Malformed input returns a failed result with sentinel fields."""
        encoded = run_stateless_guest(Bytes(b""))
        result = deserialize_stateless_output(encoded)

        assert result.new_payload_request_root == Hash32(b"\0" * 32)
        assert not result.successful_validation
        assert result.chain_config.chain_id == U64(0)
        assert result.chain_config.active_fork.fork == ProtocolFork.Frontier
        assert result.chain_config.active_fork.activation.block_number is None
        assert result.chain_config.active_fork.activation.timestamp is None


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
