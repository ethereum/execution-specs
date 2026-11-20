"""Tests for stateless_guest serialization roundtrip."""

import random
from hashlib import sha256
from types import SimpleNamespace
from typing import Any, Tuple

import pytest
from ethereum_rlp import rlp
from ethereum_types.bytes import Bytes, Bytes8, Bytes32, Bytes48, Bytes96
from ethereum_types.numeric import U16, U64, U256, Uint

from ethereum.crypto.hash import Hash32
from ethereum.state import Address, Root
from ethereum.stateless.types import (
    MAX_BYTES_PER_CODE,
    MAX_BYTES_PER_HEADER,
    MAX_BYTES_PER_WITNESS_NODE,
    MAX_WITNESS_HEADERS,
    ExecutionWitness,
    ProtocolFork,
    StatelessValidationResult,
    deserialize_stateless_output,
    serialize_stateless_output,
    stateless_input_schema_id,
)

from .stateless_forks import STATELESS_FORKS

_RNG = random.Random(0xDEADBEEF)


@pytest.fixture(params=STATELESS_FORKS, ids=lambda fork: fork.short_name)
def spec(request: pytest.FixtureRequest) -> SimpleNamespace:
    """Return the modules that these tests use, for each fork."""
    fork = request.param
    return SimpleNamespace(
        fork=fork,
        blocks=fork.module("blocks"),
        fork_types=fork.module("fork_types"),
        transactions=fork.module("transactions"),
        requests=fork.module("execution_engine.requests"),
        engine_types=fork.module("execution_engine.types"),
        validation_helpers=fork.module("execution_engine.validation_helpers"),
        stateless=fork.module("stateless"),
        guest=fork.module("stateless_guest"),
        host=fork.module("stateless_host"),
    )


def test_protocol_fork_indices() -> None:
    """Retain the fork indices that schema ids are built from."""
    assert ProtocolFork.Amsterdam == 0x15
    assert ProtocolFork.Bogota == 0x16


def test_stateless_input_schema_id_identifies_fork_revision(
    spec: SimpleNamespace,
) -> None:
    """A fork's stateless input schema id is its own fork_index || revision."""
    fork_index = ProtocolFork[spec.fork.title_case_name.replace(" ", "")]
    stateless = spec.stateless
    assert stateless.STATELESS_INPUT_SCHEMA_FORK_INDEX is fork_index
    assert stateless.STATELESS_INPUT_SCHEMA_REVISION == 0x01
    assert stateless.STATELESS_INPUT_SCHEMA_ID == (fork_index << 8) | 0x01
    assert stateless.STATELESS_INPUT_SCHEMA_ID_BYTES == bytes(
        [fork_index, 0x01]
    )


def _rb(n: int) -> bytes:
    """Return ``n`` pseudo-random bytes."""
    return bytes(_RNG.getrandbits(8) for _ in range(n))


def _make_payload(spec: SimpleNamespace) -> Any:
    return spec.engine_types.ExecutionPayload(
        parent_hash=Hash32(_rb(32)),
        fee_recipient=Address(_rb(20)),
        state_root=Root(_rb(32)),
        receipts_root=Root(_rb(32)),
        logs_bloom=spec.fork_types.Bloom(_rb(256)),
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


def _make_header(spec: SimpleNamespace) -> Any:
    return spec.blocks.Header(
        parent_hash=Hash32(_rb(32)),
        ommers_hash=Hash32(_rb(32)),
        coinbase=Address(_rb(20)),
        state_root=Root(_rb(32)),
        transactions_root=Root(_rb(32)),
        receipt_root=Root(_rb(32)),
        bloom=spec.fork_types.Bloom(_rb(256)),
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


def _make_block(spec: SimpleNamespace) -> Any:
    return spec.blocks.Block(
        header=_make_header(spec),
        transactions=(),
        ommers=(),
        withdrawals=(),
    )


def _make_deposit_request(spec: SimpleNamespace) -> Any:
    return spec.requests.DepositRequest(
        pubkey=Bytes48(_rb(48)),
        withdrawal_credentials=Bytes32(_rb(32)),
        amount=U64(_RNG.randint(0, 2**64 - 1)),
        signature=Bytes96(_rb(96)),
        index=U64(_RNG.randint(0, 2**64 - 1)),
    )


def _make_builder_deposit_request(spec: SimpleNamespace) -> Any:
    return spec.requests.BuilderDepositRequest(
        pubkey=Bytes48(_rb(48)),
        withdrawal_credentials=Bytes32(_rb(32)),
        amount=U64(_RNG.randint(0, 2**64 - 1)),
        signature=Bytes96(_rb(96)),
    )


def _make_builder_exit_request(spec: SimpleNamespace) -> Any:
    return spec.requests.BuilderExitRequest(
        source_address=Address(_rb(20)),
        pubkey=Bytes48(_rb(48)),
    )


def _make_stateless_input(spec: SimpleNamespace) -> Any:
    versioned_hashes: Tuple[Hash32, ...] = (Hash32(_rb(32)), Hash32(_rb(32)))
    return spec.stateless.StatelessInput(
        new_payload_request=spec.engine_types.NewPayloadRequest(
            execution_payload=_make_payload(spec),
            versioned_hashes=versioned_hashes,
            parent_beacon_block_root=Root(_rb(32)),
            execution_requests=spec.requests.ExecutionRequests(
                deposits=(
                    _make_deposit_request(spec),
                    _make_deposit_request(spec),
                ),
                withdrawals=(),
                consolidations=(),
                builder_deposits=(_make_builder_deposit_request(spec),),
                builder_exits=(_make_builder_exit_request(spec),),
            ),
        ),
        witness=ExecutionWitness(
            state=(Bytes(_rb(64)), Bytes(_rb(64)), Bytes(_rb(32))),
            codes=(Bytes(_rb(48)), Bytes(_rb(96))),
            headers=(Bytes(_rb(512)), Bytes(_rb(512))),
        ),
        chain_id=U64(1),
    )


def _make_stateless_output(spec: SimpleNamespace) -> StatelessValidationResult:
    return StatelessValidationResult(
        new_payload_request_root=Hash32(_rb(32)),
        successful_validation=True,
        chain_id=U64(1),
        schema_id=U16(spec.stateless.STATELESS_INPUT_SCHEMA_ID),
    )


def _make_known_stateless_input(spec: SimpleNamespace) -> Any:
    """Return an order-independent input for the SSZ known-answer test."""
    state = _RNG.getstate()
    try:
        _RNG.seed(0xDEADBEEF)
        return _make_stateless_input(spec)
    finally:
        _RNG.setstate(state)


class TestBuildStatelessInput:
    """Test host-side StatelessInput construction."""

    def test_includes_chain_id(self, spec: SimpleNamespace) -> None:
        """Include the configured chain identifier."""
        stateless_input = spec.host.build_stateless_input(
            _make_block(spec),
            execution_witness=ExecutionWitness(
                state=(),
                codes=(),
                headers=(),
            ),
            execution_requests=spec.requests.ExecutionRequests(
                deposits=(),
                withdrawals=(),
                consolidations=(),
                builder_deposits=(),
                builder_exits=(),
            ),
            block_access_list=[],
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
    def test_rejected_transaction_is_preserved(
        self, spec: SimpleNamespace, v: int, r: int, s: int
    ) -> None:
        """Keep rejected transactions in the payload for guest validation."""
        tx = spec.transactions.LegacyTransaction(
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
        block = spec.blocks.Block(
            header=_make_header(spec),
            transactions=(tx,),
            ommers=(),
            withdrawals=(),
        )
        stateless_input = spec.host.build_stateless_input(
            block,
            execution_witness=ExecutionWitness(
                state=(),
                codes=(),
                headers=(),
            ),
            execution_requests=spec.requests.ExecutionRequests(
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

    def test_payload_round_trip_preserves_legacy_transaction_rlp(
        self, spec: SimpleNamespace
    ) -> None:
        """Preserve canonical legacy transaction RLP through the payload."""
        tx = spec.transactions.LegacyTransaction(
            nonce=U256(0),
            gas_price=Uint(1),
            gas=Uint(21_000),
            to=Address(b"\x00" * 20),
            value=U256(0),
            data=Bytes(b"\x00" * 200_000),
            v=U256(27),
            r=U256(0),
            s=U256(1),
        )
        block = spec.blocks.Block(
            header=_make_header(spec),
            transactions=(tx,),
            ommers=(),
            withdrawals=(),
        )
        execution_requests = spec.requests.ExecutionRequests(
            deposits=(),
            withdrawals=(),
            consolidations=(),
            builder_deposits=(),
            builder_exits=(),
        )
        stateless_input = spec.host.build_stateless_input(
            block,
            execution_witness=ExecutionWitness(
                state=(),
                codes=(),
                headers=(),
            ),
            execution_requests=execution_requests,
            block_access_list=[],
            chain_id=U64(1),
        )

        rebuilt_block = spec.validation_helpers._payload_block(
            stateless_input.new_payload_request.execution_payload,
            block.header.parent_beacon_block_root,
            execution_requests,
        )

        assert rebuilt_block.transactions == (tx,)
        assert rlp.encode(rebuilt_block.transactions) == rlp.encode(
            block.transactions
        )


class TestSerializeStatelessInput:
    """Test serialize_stateless_input."""

    def test_roundtrip(self, spec: SimpleNamespace) -> None:
        """Encoding then decoding recovers the original StatelessInput."""
        original = _make_stateless_input(spec)
        encoded = spec.host.serialize_stateless_input(original)
        assert encoded[:2] == spec.stateless.STATELESS_INPUT_SCHEMA_ID_BYTES
        recovered = spec.guest.deserialize_stateless_input(encoded)
        assert recovered == original

    def test_known_encoding_and_request_root(
        self, spec: SimpleNamespace
    ) -> None:
        """Retain the schema bytes and payload request hash-tree root."""
        original = _make_known_stateless_input(spec)
        encoded = spec.host.serialize_stateless_input(original)

        # Only the schema id differs between forks that share a payload.
        assert len(encoded) == 2938
        assert encoded[:2] == spec.stateless.STATELESS_INPUT_SCHEMA_ID_BYTES
        assert sha256(encoded[2:]).hexdigest() == (
            "bd8805d1d25b203bd305edef95bbbaaf4a8fd7c95f1b6a5cc02c611e6d8faf01"
        )
        root = spec.stateless.compute_new_payload_request_root(original)
        assert root == Hash32(
            bytes.fromhex(
                "43afdcfa2792c3fb237ddbf271fc3675"
                "e3dc06ec37283f7f6956c2da6e917dd7"
            )
        )

    def test_empty_witness(self, spec: SimpleNamespace) -> None:
        """Works with an empty witness."""
        original = spec.stateless.StatelessInput(
            new_payload_request=spec.engine_types.NewPayloadRequest(
                execution_payload=_make_payload(spec),
                versioned_hashes=(),
                parent_beacon_block_root=Root(_rb(32)),
                execution_requests=spec.requests.ExecutionRequests(
                    deposits=(),
                    withdrawals=(),
                    consolidations=(),
                    builder_deposits=(),
                    builder_exits=(),
                ),
            ),
            witness=ExecutionWitness(state=(), codes=(), headers=()),
            chain_id=U64(1),
        )
        encoded = spec.host.serialize_stateless_input(original)
        assert encoded[:2] == spec.stateless.STATELESS_INPUT_SCHEMA_ID_BYTES
        recovered = spec.guest.deserialize_stateless_input(encoded)
        assert recovered == original

    @pytest.mark.parametrize(
        "witness",
        [
            pytest.param(
                ExecutionWitness(
                    state=(Bytes(b"\0" * (MAX_BYTES_PER_WITNESS_NODE + 1)),),
                    codes=(),
                    headers=(),
                ),
                id="state-node",
            ),
            pytest.param(
                ExecutionWitness(
                    state=(),
                    codes=(Bytes(b"\0" * (MAX_BYTES_PER_CODE + 1)),),
                    headers=(),
                ),
                id="code",
            ),
            pytest.param(
                ExecutionWitness(
                    state=(),
                    codes=(),
                    headers=(Bytes(b"\0" * (MAX_BYTES_PER_HEADER + 1)),),
                ),
                id="header",
            ),
        ],
    )
    def test_rejects_oversized_witness_item(
        self,
        spec: SimpleNamespace,
        witness: ExecutionWitness,
    ) -> None:
        """Retain the structural byte limit for each witness item."""
        original = _make_stateless_input(spec)
        invalid = spec.stateless.StatelessInput(
            new_payload_request=original.new_payload_request,
            witness=witness,
            chain_id=original.chain_id,
        )

        with pytest.raises(Exception, match="cannot be more than limit"):
            spec.host.serialize_stateless_input(invalid)

    def test_rejects_more_than_256_headers(
        self, spec: SimpleNamespace
    ) -> None:
        """Retain the protocol-backed witness header count limit."""
        original = _make_stateless_input(spec)
        invalid = spec.stateless.StatelessInput(
            new_payload_request=original.new_payload_request,
            witness=ExecutionWitness(
                state=(),
                codes=(),
                headers=tuple(Bytes() for _ in range(MAX_WITNESS_HEADERS + 1)),
            ),
            chain_id=original.chain_id,
        )

        with pytest.raises(Exception, match="too many list inputs: 257"):
            spec.host.serialize_stateless_input(invalid)


class TestDeserializeStatelessInput:
    """Test deserialize_stateless_input."""

    def test_roundtrip(self, spec: SimpleNamespace) -> None:
        """Encoding then decoding recovers the original StatelessInput."""
        original = _make_stateless_input(spec)
        encoded = spec.host.serialize_stateless_input(original)
        recovered = spec.guest.deserialize_stateless_input(encoded)
        assert recovered == original
        payload = recovered.new_payload_request.execution_payload
        assert type(payload.block_number) is Uint
        assert type(payload.timestamp) is U256
        assert type(payload.transactions) is tuple
        assert type(recovered.witness.state) is tuple

    def test_empty_witness(self, spec: SimpleNamespace) -> None:
        """Works with an empty witness."""
        original = spec.stateless.StatelessInput(
            new_payload_request=spec.engine_types.NewPayloadRequest(
                execution_payload=_make_payload(spec),
                versioned_hashes=(),
                parent_beacon_block_root=Root(_rb(32)),
                execution_requests=spec.requests.ExecutionRequests(
                    deposits=(),
                    withdrawals=(),
                    consolidations=(),
                    builder_deposits=(),
                    builder_exits=(),
                ),
            ),
            witness=ExecutionWitness(state=(), codes=(), headers=()),
            chain_id=U64(1),
        )
        encoded = spec.host.serialize_stateless_input(original)
        recovered = spec.guest.deserialize_stateless_input(encoded)
        assert recovered == original

    def test_empty_input_rejected(self, spec: SimpleNamespace) -> None:
        """Reject input that does not contain a schema id."""
        with pytest.raises(ValueError, match="missing schema id"):
            spec.guest.deserialize_stateless_input(Bytes(b""))

    def test_one_byte_input_rejected(self, spec: SimpleNamespace) -> None:
        """Reject input that does not contain a full schema id."""
        schema_id_bytes = spec.stateless.STATELESS_INPUT_SCHEMA_ID_BYTES
        with pytest.raises(ValueError, match="missing schema id"):
            spec.guest.deserialize_stateless_input(Bytes(schema_id_bytes[:1]))

    def test_unsupported_schema_revision_rejected(
        self, spec: SimpleNamespace
    ) -> None:
        """Reject the next revision of the fork's own schema."""
        encoded = spec.host.serialize_stateless_input(
            _make_stateless_input(spec)
        )
        schema_id = stateless_input_schema_id(
            spec.stateless.STATELESS_INPUT_SCHEMA_FORK_INDEX,
            spec.stateless.STATELESS_INPUT_SCHEMA_REVISION + 1,
        )
        with pytest.raises(ValueError, match=f"0x{schema_id:04x}"):
            spec.guest.deserialize_stateless_input(
                Bytes(schema_id.to_bytes(2, "big") + encoded[2:])
            )

    def test_unsupported_schema_fork_rejected(
        self, spec: SimpleNamespace
    ) -> None:
        """Reject the schema id that any other fork has at this revision."""
        encoded = spec.host.serialize_stateless_input(
            _make_stateless_input(spec)
        )
        own_fork_index = spec.stateless.STATELESS_INPUT_SCHEMA_FORK_INDEX
        for fork_index in ProtocolFork:
            if fork_index == own_fork_index:
                continue
            schema_id = stateless_input_schema_id(
                fork_index, spec.stateless.STATELESS_INPUT_SCHEMA_REVISION
            )
            with pytest.raises(ValueError, match=f"0x{schema_id:04x}"):
                spec.guest.deserialize_stateless_input(
                    Bytes(schema_id.to_bytes(2, "big") + encoded[2:])
                )

    def test_legacy_raw_ssz_input_rejected(
        self, spec: SimpleNamespace
    ) -> None:
        """Reject unprefixed SSZ input bytes."""
        original = _make_stateless_input(spec)
        raw_ssz = Bytes(original.encode_bytes())
        assert raw_ssz[:2] != spec.stateless.STATELESS_INPUT_SCHEMA_ID_BYTES
        with pytest.raises(ValueError, match="Unsupported stateless input"):
            spec.guest.deserialize_stateless_input(raw_ssz)


class TestSerializeStatelessOutput:
    """Test serialize_stateless_output."""

    def test_roundtrip(self, spec: SimpleNamespace) -> None:
        """Encoding then decoding recovers the original result."""
        schema_id = spec.stateless.STATELESS_INPUT_SCHEMA_ID
        original = _make_stateless_output(spec)
        encoded = serialize_stateless_output(original)
        assert encoded[-2:] == schema_id.to_bytes(2, "little")
        recovered = deserialize_stateless_output(encoded)
        assert recovered == original
        assert recovered.chain_id == U64(1)
        assert recovered.schema_id == U16(schema_id)

    def test_known_encoding(self, spec: SimpleNamespace) -> None:
        """Retain the fixed SSZ output encoding."""
        schema_id = spec.stateless.STATELESS_INPUT_SCHEMA_ID
        original = StatelessValidationResult(
            new_payload_request_root=Hash32(
                bytes.fromhex(
                    "0d663a7de3d811fbc797f605a65d2745d"
                    "f3a97d9f1994dfb685ff66d2917009f"
                )
            ),
            successful_validation=True,
            chain_id=U64(1),
            schema_id=U16(schema_id),
        )
        assert serialize_stateless_output(original).hex() == (
            "0d663a7de3d811fbc797f605a65d2745df3a97d9f1994dfb685ff66d2917009f"
            "010100000000000000" + schema_id.to_bytes(2, "little").hex()
        )

    def test_failed_validation(self, spec: SimpleNamespace) -> None:
        """Preserve the input schema when later validation fails."""
        schema_id = spec.stateless.STATELESS_INPUT_SCHEMA_ID
        original = StatelessValidationResult(
            new_payload_request_root=Hash32(_rb(32)),
            successful_validation=False,
            chain_id=U64(1),
            schema_id=U16(schema_id),
        )
        encoded = serialize_stateless_output(original)
        recovered = deserialize_stateless_output(encoded)
        assert recovered == original
        assert recovered.schema_id == U16(schema_id)


class TestRunStatelessGuest:
    """Test stateless guest input and output handling."""

    def test_request_commitment_failure_returns_sentinel(
        self, spec: SimpleNamespace, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Failure to compute the public commitment must fail closed."""
        stateless_input = _make_stateless_input(spec)
        input_bytes = spec.host.serialize_stateless_input(stateless_input)

        def fail_hash_tree_root(self: Any) -> bytes:
            raise RuntimeError("Request commitment unavailable")

        monkeypatch.setattr(
            spec.engine_types.NewPayloadRequest,
            "hash_tree_root",
            fail_hash_tree_root,
        )
        result = deserialize_stateless_output(
            spec.guest.run_stateless_guest(input_bytes)
        )

        assert result == StatelessValidationResult(
            new_payload_request_root=Hash32(b"\0" * 32),
            successful_validation=False,
            chain_id=U64(0),
            schema_id=U16(0),
        )

    def test_noncanonical_ssz_returns_sentinel_failure(
        self, spec: SimpleNamespace
    ) -> None:
        """Reject shifted container offsets that leave trailing data unread."""
        stateless_input = _make_stateless_input(spec)
        encoded = bytearray(
            spec.host.serialize_stateless_input(stateless_input)
        )
        # After the schema prefix: request offset, witness offset, chain ID.
        # Shift both offsets by one byte.
        for offset in (2, 6):
            value = int.from_bytes(encoded[offset : offset + 4], "little")
            encoded[offset : offset + 4] = (value + 1).to_bytes(4, "little")
        encoded.append(0xFF)

        result = deserialize_stateless_output(
            spec.guest.run_stateless_guest(Bytes(encoded))
        )

        assert result == StatelessValidationResult(
            new_payload_request_root=Hash32(b"\0" * 32),
            successful_validation=False,
            chain_id=U64(0),
            schema_id=U16(0),
        )

    def test_invalid_input_bytes_return_failed_validation(
        self, spec: SimpleNamespace
    ) -> None:
        """Malformed input returns a failed result with sentinel fields."""
        encoded = spec.guest.run_stateless_guest(Bytes(b""))
        result = deserialize_stateless_output(encoded)

        assert result.new_payload_request_root == Hash32(b"\0" * 32)
        assert not result.successful_validation
        assert result.chain_id == U64(0)
        assert result.schema_id == U16(0)

    def test_decodable_input_reports_schema_on_validation_failure(
        self, spec: SimpleNamespace
    ) -> None:
        """Decoded input reports its schema after execution failure."""
        stateless_input = _make_stateless_input(spec)
        encoded = spec.guest.run_stateless_guest(
            spec.host.serialize_stateless_input(stateless_input)
        )
        result = deserialize_stateless_output(encoded)

        assert not result.successful_validation
        assert result.chain_id == stateless_input.chain_id
        assert result.schema_id == U16(
            spec.stateless.STATELESS_INPUT_SCHEMA_ID
        )


class TestComputeNewPayloadRequestRoot:
    """Test compute_new_payload_request_root."""

    def test_hash_tree_root_is_deterministic(
        self, spec: SimpleNamespace
    ) -> None:
        """Same input produces the same root."""
        si = _make_stateless_input(spec)
        root_a = spec.stateless.compute_new_payload_request_root(si)
        root_b = spec.stateless.compute_new_payload_request_root(si)
        assert root_a == root_b

    def test_hash_tree_root_is_32_bytes(self, spec: SimpleNamespace) -> None:
        """Root is always 32 bytes."""
        si = _make_stateless_input(spec)
        root = spec.stateless.compute_new_payload_request_root(si)
        assert len(root) == 32
