"""Tests for stateless_guest serialization roundtrip."""

import random
from typing import Tuple

import pytest
from ethereum_rlp import rlp
from ethereum_types.bytes import Bytes, Bytes8, Bytes32, Bytes48, Bytes96
from ethereum_types.numeric import U8, U64, U256, Uint

from ethereum.crypto.hash import Hash32
from ethereum.forks.amsterdam.block_access_lists import BlockAccessList
from ethereum.forks.amsterdam.blocks import Block, Header
from ethereum.forks.amsterdam.execution_engine.requests import (
    BuilderDepositRequest,
    BuilderExitRequest,
    DepositRequest,
    ExecutionRequests,
)
from ethereum.forks.amsterdam.execution_engine.types import (
    ExecutionPayload,
    NewPayloadRequest,
)
from ethereum.forks.amsterdam.fork_types import Bloom
from ethereum.forks.amsterdam.stateless import (
    ExecutionWitness,
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
    build_stateless_input,
    deserialize_stateless_output,
    serialize_stateless_input,
)
from ethereum.forks.amsterdam.stateless_ssz import (
    STATELESS_INPUT_SCHEMA_FORK_INDEX,
    STATELESS_INPUT_SCHEMA_ID,
    STATELESS_INPUT_SCHEMA_ID_BYTES,
    STATELESS_INPUT_SCHEMA_REVISION,
    stateless_input_to_ssz,
)
from ethereum.forks.amsterdam.transactions import LegacyTransaction
from ethereum.state import Address, Root

_RNG = random.Random(0xDEADBEEF)


def test_stateless_input_schema_id_identifies_amsterdam_revision() -> None:
    """Amsterdam stateless input schema id is fork_index || revision."""
    assert STATELESS_INPUT_SCHEMA_FORK_INDEX is ProtocolFork.Amsterdam
    assert STATELESS_INPUT_SCHEMA_FORK_INDEX == 0x15
    assert STATELESS_INPUT_SCHEMA_REVISION == 0x01
    assert STATELESS_INPUT_SCHEMA_ID == 0x1501
    assert STATELESS_INPUT_SCHEMA_ID_BYTES == b"\x15\x01"


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


def _make_deposit_request() -> DepositRequest:
    return DepositRequest(
        pubkey=Bytes48(_rb(48)),
        withdrawal_credentials=Bytes32(_rb(32)),
        amount=U64(_RNG.randint(0, 2**64 - 1)),
        signature=Bytes96(_rb(96)),
        index=U64(_RNG.randint(0, 2**64 - 1)),
    )


def _make_builder_deposit_request() -> BuilderDepositRequest:
    return BuilderDepositRequest(
        pubkey=Bytes48(_rb(48)),
        withdrawal_credentials=Bytes32(_rb(32)),
        amount=U64(_RNG.randint(0, 2**64 - 1)),
        signature=Bytes96(_rb(96)),
    )


def _make_builder_exit_request() -> BuilderExitRequest:
    return BuilderExitRequest(
        source_address=Address(_rb(20)),
        pubkey=Bytes48(_rb(48)),
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
                builder_deposits=(_make_builder_deposit_request(),),
                builder_exits=(_make_builder_exit_request(),),
            ),
        ),
        witness=ExecutionWitness(
            state=(Bytes(_rb(64)), Bytes(_rb(64)), Bytes(_rb(32))),
            codes=(Bytes(_rb(48)), Bytes(_rb(96))),
            headers=(Bytes(_rb(512)), Bytes(_rb(512))),
        ),
        chain_id=U64(1),
        public_keys=(Bytes(_rb(65)), Bytes(_rb(65))),
    )


def _make_stateless_output() -> StatelessValidationResult:
    return StatelessValidationResult(
        new_payload_request_root=Hash32(_rb(32)),
        successful_validation=True,
        chain_id=U64(1),
        schema_fork_index=U8(0x15),
    )


class TestBuildStatelessInput:
    """Test host-side StatelessInput construction."""

    def test_includes_chain_id(self) -> None:
        """Include the configured chain identifier."""
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
                builder_deposits=(),
                builder_exits=(),
            ),
            block_access_list=block_access_list,
            chain_id=U64(123),
        )
        assert stateless_input.chain_id == U64(123)

    @pytest.mark.parametrize(
        ("v", "r", "s"),
        [
            pytest.param(27, 0, 1, id="invalid-signature"),
            pytest.param(39, 1, 1, id="wrong-chain-id"),
        ],
    )
    def test_rejected_transaction_omits_public_key(
        self, v: int, r: int, s: int
    ) -> None:
        """Keep rejected transactions without requiring a public key."""
        tx = LegacyTransaction(
            nonce=U256(0),
            gas_price=Uint(1),
            gas=Uint(21_000),
            to=Address(b"\x00" * 20),
            value=U256(0),
            data=Bytes(b""),
            v=U256(v),
            r=U256(r),
            s=U256(s),
        )
        block = Block(
            header=_make_header(),
            transactions=(tx,),
            ommers=(),
            withdrawals=(),
        )
        stateless_input = build_stateless_input(
            block,
            execution_witness=ExecutionWitness(
                state=(),
                codes=(),
                headers=(),
            ),
            execution_requests=ExecutionRequests(
                deposits=(),
                withdrawals=(),
                consolidations=(),
                builder_deposits=(),
                builder_exits=(),
            ),
            block_access_list=[],
            chain_id=U64(1),
        )

        payload = stateless_input.new_payload_request.execution_payload
        assert payload.transactions == (Bytes(rlp.encode(tx)),)
        assert stateless_input.public_keys == ()


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
                    builder_deposits=(),
                    builder_exits=(),
                ),
            ),
            witness=ExecutionWitness(state=(), codes=(), headers=()),
            chain_id=U64(1),
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
            chain_id=original.chain_id,
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
                    builder_deposits=(),
                    builder_exits=(),
                ),
            ),
            witness=ExecutionWitness(state=(), codes=(), headers=()),
            chain_id=U64(1),
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
            deserialize_stateless_input(Bytes(b"\x15"))

    def test_unsupported_schema_revision_rejected(self) -> None:
        """Reject an unsupported Amsterdam schema revision."""
        encoded = serialize_stateless_input(_make_stateless_input())
        with pytest.raises(ValueError, match="0x1502"):
            deserialize_stateless_input(Bytes(b"\x15\x02" + encoded[2:]))

    def test_unsupported_schema_fork_rejected(self) -> None:
        """Reject an unsupported stateless input schema fork."""
        encoded = serialize_stateless_input(_make_stateless_input())
        with pytest.raises(ValueError, match="0x1601"):
            deserialize_stateless_input(Bytes(b"\x16\x01" + encoded[2:]))

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
        assert recovered.chain_id == U64(1)
        assert recovered.schema_fork_index == U8(0x15)

    def test_failed_validation(self) -> None:
        """Preserve the executed fork when later validation fails."""
        original = StatelessValidationResult(
            new_payload_request_root=Hash32(_rb(32)),
            successful_validation=False,
            chain_id=U64(1),
            schema_fork_index=U8(0x15),
        )
        encoded = serialize_stateless_output(original)
        recovered = deserialize_stateless_output(encoded)
        assert recovered == original
        assert recovered.schema_fork_index == U8(0x15)


class TestRunStatelessGuest:
    """Test stateless guest input and output handling."""

    def test_invalid_input_bytes_return_failed_validation(self) -> None:
        """Malformed input returns a failed result with sentinel fields."""
        encoded = run_stateless_guest(Bytes(b""))
        result = deserialize_stateless_output(encoded)

        assert result.new_payload_request_root == Hash32(b"\0" * 32)
        assert not result.successful_validation
        assert result.chain_id == U64(0)
        assert result.schema_fork_index == U8(0)

    def test_decodable_input_reports_amsterdam_on_validation_failure(
        self,
    ) -> None:
        """Decoded Amsterdam input reports its fork after execution failure."""
        stateless_input = _make_stateless_input()
        encoded = run_stateless_guest(
            serialize_stateless_input(stateless_input)
        )
        result = deserialize_stateless_output(encoded)

        assert not result.successful_validation
        assert result.chain_id == stateless_input.chain_id
        assert result.schema_fork_index == U8(0x15)


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
            chain_id=original.chain_id,
            public_keys=(original.public_keys[0],),
        )

        result = verify_stateless_new_payload(invalid)
        assert not result.successful_validation
        assert result.schema_fork_index == U8(0x15)

    def test_too_many_public_keys_fail_validation(self) -> None:
        """Stateless validation should fail with too many public keys."""
        original = _make_stateless_input()
        invalid = StatelessInput(
            new_payload_request=original.new_payload_request,
            witness=original.witness,
            chain_id=original.chain_id,
            public_keys=(
                original.public_keys[0],
                original.public_keys[1],
                Bytes(_rb(65)),
            ),
        )

        result = verify_stateless_new_payload(invalid)
        assert not result.successful_validation
        assert result.schema_fork_index == U8(0x15)
