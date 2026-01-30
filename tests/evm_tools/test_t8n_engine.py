"""
Tests for T8N engine mode functionality.

This module tests the T8N tool's Engine API payload validation mode.
Unit tests for PayloadStatus can run without engine modules.
Integration tests require engine modules from the .worktrees/engine-newpayload/
directory and will be skipped if those modules are unavailable.
"""

import json
import os
import sys
import tempfile
from typing import Any, Dict

import pytest

from ethereum.crypto.hash import Hash32
from ethereum_spec_tools.evm_tools.t8n.payload_status import PayloadStatus


# Check if engine modules are available
def engine_modules_available() -> bool:
    """Check if the engine modules are available for import."""
    try:
        import importlib

        importlib.import_module("ethereum.forks.paris.engine")
        return True
    except ImportError:
        return False


ENGINE_MODULES_AVAILABLE = engine_modules_available()

# Skip marker for tests requiring engine modules
requires_engine_modules = pytest.mark.skipif(
    not ENGINE_MODULES_AVAILABLE,
    reason="Engine modules not available (only in .worktrees/engine-newpayload/)",
)


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def sample_block_hash() -> Hash32:
    """Create a sample 32-byte block hash for testing."""
    return Hash32(bytes.fromhex(
        "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
    ))


@pytest.fixture
def sample_parent_hash() -> Hash32:
    """Create a sample 32-byte parent hash for testing."""
    return Hash32(bytes.fromhex(
        "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
    ))


@pytest.fixture
def v1_payload_json() -> Dict[str, Any]:
    """Create a minimal V1 (Paris) execution payload JSON."""
    return {
        "parentHash": "0x" + "00" * 32,
        "feeRecipient": "0x" + "00" * 20,
        "stateRoot": "0x" + "00" * 32,
        "receiptsRoot": "0x" + "00" * 32,
        "logsBloom": "0x" + "00" * 256,
        "prevRandao": "0x" + "00" * 32,
        "blockNumber": "0x1",
        "gasLimit": "0x1000000",
        "gasUsed": "0x0",
        "timestamp": "0x64",
        "extraData": "0x",
        "baseFeePerGas": "0x7",
        "blockHash": "0x" + "00" * 32,
        "transactions": [],
    }


@pytest.fixture
def v2_payload_json(v1_payload_json: Dict[str, Any]) -> Dict[str, Any]:
    """Create a V2 (Shanghai) execution payload JSON with withdrawals."""
    payload = v1_payload_json.copy()
    payload["withdrawals"] = [
        {
            "index": "0x0",
            "validatorIndex": "0x1",
            "address": "0x" + "ab" * 20,
            "amount": "0x10",
        }
    ]
    return payload


@pytest.fixture
def v3_payload_json(v2_payload_json: Dict[str, Any]) -> Dict[str, Any]:
    """Create a V3 (Cancun) execution payload JSON with blob fields."""
    payload = v2_payload_json.copy()
    payload["blobGasUsed"] = "0x0"
    payload["excessBlobGas"] = "0x0"
    return payload


# =============================================================================
# PayloadStatus Unit Tests (no engine module dependency)
# =============================================================================


class TestPayloadStatusClass:
    """Unit tests for the PayloadStatus class."""

    @pytest.mark.evm_tools
    def test_valid_factory(self, sample_block_hash: Hash32) -> None:
        """Test PayloadStatus.valid() factory creates correct status."""
        status = PayloadStatus.valid(sample_block_hash)

        assert status.status == "VALID"
        assert status.latest_valid_hash == sample_block_hash
        assert status.validation_error is None

    @pytest.mark.evm_tools
    def test_invalid_factory_with_error(
        self, sample_parent_hash: Hash32
    ) -> None:
        """Test PayloadStatus.invalid() factory with error message."""
        error_msg = "block hash mismatch"
        status = PayloadStatus.invalid(error_msg, sample_parent_hash)

        assert status.status == "INVALID"
        assert status.latest_valid_hash == sample_parent_hash
        assert status.validation_error == error_msg

    @pytest.mark.evm_tools
    def test_invalid_factory_no_latest_valid_hash(self) -> None:
        """Test PayloadStatus.invalid() with no latest_valid_hash."""
        error_msg = "unknown error"
        status = PayloadStatus.invalid(error_msg)

        assert status.status == "INVALID"
        assert status.latest_valid_hash is None
        assert status.validation_error == error_msg

    @pytest.mark.evm_tools
    def test_to_json_valid(self, sample_block_hash: Hash32) -> None:
        """Test to_json() for VALID status."""
        status = PayloadStatus.valid(sample_block_hash)
        json_output = status.to_json()

        assert json_output["status"] == "VALID"
        assert json_output["latestValidHash"] == "0x" + sample_block_hash.hex()
        assert json_output["validationError"] is None

    @pytest.mark.evm_tools
    def test_to_json_invalid(self, sample_parent_hash: Hash32) -> None:
        """Test to_json() for INVALID status."""
        error_msg = "state root mismatch"
        status = PayloadStatus.invalid(error_msg, sample_parent_hash)
        json_output = status.to_json()

        assert json_output["status"] == "INVALID"
        assert json_output["latestValidHash"] == "0x" + sample_parent_hash.hex()
        assert json_output["validationError"] == error_msg

    @pytest.mark.evm_tools
    def test_to_json_invalid_no_hash(self) -> None:
        """Test to_json() for INVALID status with no latest_valid_hash."""
        error_msg = "transaction decode failed"
        status = PayloadStatus.invalid(error_msg)
        json_output = status.to_json()

        assert json_output["status"] == "INVALID"
        assert json_output["latestValidHash"] is None
        assert json_output["validationError"] == error_msg

    @pytest.mark.evm_tools
    def test_json_serializable(self, sample_block_hash: Hash32) -> None:
        """Test that to_json() output is JSON serializable."""
        status = PayloadStatus.valid(sample_block_hash)
        json_output = status.to_json()

        # Should not raise
        serialized = json.dumps(json_output)
        deserialized = json.loads(serialized)

        assert deserialized["status"] == "VALID"
        assert deserialized["latestValidHash"].startswith("0x")


# =============================================================================
# Payload Class Unit Tests
# =============================================================================


class TestPayloadFixtures:
    """Unit tests to verify test fixture JSON structure."""

    @pytest.mark.evm_tools
    def test_v1_fixture_structure(
        self, v1_payload_json: Dict[str, Any]
    ) -> None:
        """Verify V1 fixture has no V2/V3 fields."""
        # V1 has no withdrawals or blob fields
        assert "withdrawals" not in v1_payload_json
        assert "blobGasUsed" not in v1_payload_json

    @pytest.mark.evm_tools
    def test_v2_fixture_structure(
        self, v2_payload_json: Dict[str, Any]
    ) -> None:
        """Verify V2 fixture has withdrawals but no blob fields."""
        # V2 has withdrawals but no blob fields
        assert "withdrawals" in v2_payload_json
        assert "blobGasUsed" not in v2_payload_json

    @pytest.mark.evm_tools
    def test_v3_fixture_structure(
        self, v3_payload_json: Dict[str, Any]
    ) -> None:
        """Verify V3 fixture has both withdrawals and blob fields."""
        # V3 has both withdrawals and blob fields
        assert "withdrawals" in v3_payload_json
        assert "blobGasUsed" in v3_payload_json
        assert "excessBlobGas" in v3_payload_json


# =============================================================================
# Integration Tests (require engine modules)
# =============================================================================


@requires_engine_modules
class TestT8NEngineIntegration:
    """Integration tests for T8N engine mode."""

    @pytest.mark.evm_tools
    def test_invalid_block_hash_returns_invalid(
        self, v1_payload_json: Dict[str, Any]
    ) -> None:
        """Test that an invalid block hash returns INVALID status."""
        from ethereum_spec_tools.evm_tools import create_parser
        from ethereum_spec_tools.evm_tools.t8n import ForkCache, T8N

        # Create a payload with mismatched block hash
        # The block hash won't match because we use all zeros
        payload = v1_payload_json.copy()
        payload["blockHash"] = "0x" + "ff" * 32  # Wrong hash

        with tempfile.TemporaryDirectory() as tmpdir:
            # Write payload file
            payload_path = os.path.join(tmpdir, "payload.json")
            with open(payload_path, "w") as f:
                json.dump(payload, f)

            # Write minimal alloc file
            alloc_path = os.path.join(tmpdir, "alloc.json")
            with open(alloc_path, "w") as f:
                json.dump({}, f)

            # Create T8N instance
            parser = create_parser()
            args = parser.parse_args([
                "t8n",
                "--state.fork", "Paris",
                "--input.alloc", alloc_path,
                "--input.payload", payload_path,
                "--output.basedir", tmpdir,
                "--output.result", "result.json",
            ])

            with ForkCache() as cache:
                t8n = T8N(args, sys.stdout, sys.stdin, cache)

                # Run engine validation
                status = t8n.run_engine_validation()

                # Should be INVALID due to block hash mismatch
                assert status.status == "INVALID"
                assert "hash" in status.validation_error.lower()

    @pytest.mark.evm_tools
    def test_valid_empty_block_returns_valid(
        self, v1_payload_json: Dict[str, Any]
    ) -> None:
        """Test that a valid empty block returns VALID status."""
        from ethereum_rlp import rlp

        from ethereum.crypto.hash import keccak256
        from ethereum.forks.paris.engine import payload_to_header, ExecutionPayloadV1
        from ethereum.forks.paris.fork_types import Address, Bloom
        from ethereum.forks.paris.state import State, state_root
        from ethereum.forks.paris.trie import Trie, root as trie_root
        from ethereum_spec_tools.evm_tools import create_parser
        from ethereum_spec_tools.evm_tools.t8n import ForkCache, T8N
        from ethereum_types.bytes import Bytes, Bytes32
        from ethereum_types.numeric import U256, Uint

        # Create a valid empty block payload
        # Empty state root
        empty_state = State()
        empty_state_root = state_root(empty_state)

        # Empty receipts trie root
        empty_receipts_trie: Trie[Bytes, Bytes] = Trie(
            secured=False, default=b""
        )
        empty_receipts_root = trie_root(empty_receipts_trie)

        # Build ExecutionPayloadV1 with correct values
        execution_payload = ExecutionPayloadV1(
            parent_hash=bytes(32),
            fee_recipient=Address(bytes(20)),
            state_root=empty_state_root,
            receipts_root=empty_receipts_root,
            logs_bloom=Bloom(bytes(256)),
            prev_randao=Bytes32(bytes(32)),
            block_number=Uint(1),
            gas_limit=Uint(0x1000000),
            gas_used=Uint(0),
            timestamp=U256(100),
            extra_data=b"",
            base_fee_per_gas=Uint(7),
            block_hash=bytes(32),  # Placeholder, will compute
            transactions=(),
        )

        # Compute correct block hash
        header = payload_to_header(execution_payload)
        correct_block_hash = keccak256(rlp.encode(header))

        # Create payload with correct hash
        execution_payload = ExecutionPayloadV1(
            parent_hash=execution_payload.parent_hash,
            fee_recipient=execution_payload.fee_recipient,
            state_root=execution_payload.state_root,
            receipts_root=execution_payload.receipts_root,
            logs_bloom=execution_payload.logs_bloom,
            prev_randao=execution_payload.prev_randao,
            block_number=execution_payload.block_number,
            gas_limit=execution_payload.gas_limit,
            gas_used=execution_payload.gas_used,
            timestamp=execution_payload.timestamp,
            extra_data=execution_payload.extra_data,
            base_fee_per_gas=execution_payload.base_fee_per_gas,
            block_hash=correct_block_hash,
            transactions=(),
        )

        # Convert to JSON format
        payload_json = {
            "parentHash": "0x" + execution_payload.parent_hash.hex(),
            "feeRecipient": "0x" + bytes(execution_payload.fee_recipient).hex(),
            "stateRoot": "0x" + bytes(execution_payload.state_root).hex(),
            "receiptsRoot": "0x" + bytes(execution_payload.receipts_root).hex(),
            "logsBloom": "0x" + bytes(execution_payload.logs_bloom).hex(),
            "prevRandao": "0x" + bytes(execution_payload.prev_randao).hex(),
            "blockNumber": hex(execution_payload.block_number),
            "gasLimit": hex(execution_payload.gas_limit),
            "gasUsed": hex(execution_payload.gas_used),
            "timestamp": hex(execution_payload.timestamp),
            "extraData": "0x",
            "baseFeePerGas": hex(execution_payload.base_fee_per_gas),
            "blockHash": "0x" + execution_payload.block_hash.hex(),
            "transactions": [],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            # Write payload file
            payload_path = os.path.join(tmpdir, "payload.json")
            with open(payload_path, "w") as f:
                json.dump(payload_json, f)

            # Write empty alloc file
            alloc_path = os.path.join(tmpdir, "alloc.json")
            with open(alloc_path, "w") as f:
                json.dump({}, f)

            # Create T8N instance
            parser = create_parser()
            args = parser.parse_args([
                "t8n",
                "--state.fork", "Paris",
                "--input.alloc", alloc_path,
                "--input.payload", payload_path,
                "--output.basedir", tmpdir,
                "--output.result", "result.json",
            ])

            with ForkCache() as cache:
                t8n = T8N(args, sys.stdout, sys.stdin, cache)

                # Run engine validation
                status = t8n.run_engine_validation()

                # Should be VALID
                assert status.status == "VALID", f"Expected VALID, got {status.status}: {status.validation_error}"
                assert status.validation_error is None
                assert status.latest_valid_hash == correct_block_hash

    @pytest.mark.evm_tools
    def test_v2_payload_with_withdrawals(
        self, v2_payload_json: Dict[str, Any]
    ) -> None:
        """Test V2 payload with withdrawals field."""
        from ethereum_spec_tools.evm_tools import create_parser
        from ethereum_spec_tools.evm_tools.t8n import ForkCache, T8N

        # V2 payload should be parsed with withdrawals
        payload = v2_payload_json.copy()

        with tempfile.TemporaryDirectory() as tmpdir:
            # Write payload file
            payload_path = os.path.join(tmpdir, "payload.json")
            with open(payload_path, "w") as f:
                json.dump(payload, f)

            # Write minimal alloc file
            alloc_path = os.path.join(tmpdir, "alloc.json")
            with open(alloc_path, "w") as f:
                json.dump({}, f)

            # Create T8N instance with Shanghai fork
            parser = create_parser()
            args = parser.parse_args([
                "t8n",
                "--state.fork", "Shanghai",
                "--input.alloc", alloc_path,
                "--input.payload", payload_path,
                "--output.basedir", tmpdir,
                "--output.result", "result.json",
            ])

            with ForkCache() as cache:
                t8n = T8N(args, sys.stdout, sys.stdin, cache)

                # Check that payload was parsed with withdrawals
                assert t8n.payload is not None
                assert t8n.payload.withdrawals is not None
                assert len(t8n.payload.withdrawals) == 1
                assert t8n.payload.get_version() == 2

    @pytest.mark.evm_tools
    def test_v3_payload_with_blob_fields(
        self, v3_payload_json: Dict[str, Any]
    ) -> None:
        """Test V3 payload with blob gas fields."""
        from ethereum_spec_tools.evm_tools import create_parser
        from ethereum_spec_tools.evm_tools.t8n import ForkCache, T8N

        # V3 payload should be parsed with blob fields
        payload = v3_payload_json.copy()

        with tempfile.TemporaryDirectory() as tmpdir:
            # Write payload file
            payload_path = os.path.join(tmpdir, "payload.json")
            with open(payload_path, "w") as f:
                json.dump(payload, f)

            # Write minimal alloc file
            alloc_path = os.path.join(tmpdir, "alloc.json")
            with open(alloc_path, "w") as f:
                json.dump({}, f)

            # Create T8N instance with Cancun fork
            parser = create_parser()
            args = parser.parse_args([
                "t8n",
                "--state.fork", "Cancun",
                "--input.alloc", alloc_path,
                "--input.payload", payload_path,
                "--output.basedir", tmpdir,
                "--output.result", "result.json",
            ])

            with ForkCache() as cache:
                t8n = T8N(args, sys.stdout, sys.stdin, cache)

                # Check that payload was parsed with blob fields
                assert t8n.payload is not None
                assert t8n.payload.blob_gas_used is not None
                assert t8n.payload.excess_blob_gas is not None
                assert t8n.payload.get_version() == 3


# =============================================================================
# T8N CLI Integration Tests
# =============================================================================


@requires_engine_modules
class TestT8NEngineModeCLI:
    """Test T8N tool CLI behavior in engine mode."""

    @pytest.mark.evm_tools
    def test_engine_mode_enabled_with_payload_arg(
        self, v1_payload_json: Dict[str, Any]
    ) -> None:
        """Test that --input.payload enables engine mode."""
        from ethereum_spec_tools.evm_tools import create_parser
        from ethereum_spec_tools.evm_tools.t8n import ForkCache, T8N

        with tempfile.TemporaryDirectory() as tmpdir:
            # Write payload file
            payload_path = os.path.join(tmpdir, "payload.json")
            with open(payload_path, "w") as f:
                json.dump(v1_payload_json, f)

            # Write minimal alloc file
            alloc_path = os.path.join(tmpdir, "alloc.json")
            with open(alloc_path, "w") as f:
                json.dump({}, f)

            parser = create_parser()
            args = parser.parse_args([
                "t8n",
                "--state.fork", "Paris",
                "--input.alloc", alloc_path,
                "--input.payload", payload_path,
                "--output.basedir", tmpdir,
            ])

            with ForkCache() as cache:
                t8n = T8N(args, sys.stdout, sys.stdin, cache)

                # Engine mode should be enabled
                assert t8n.engine_mode is True
                assert t8n.payload is not None
                # Standard mode attributes should be None
                assert t8n.env is None
                assert t8n.txs is None
                assert t8n.result is None

    @pytest.mark.evm_tools
    def test_standard_mode_without_payload_arg(self) -> None:
        """Test that without --input.payload, standard mode is used."""
        from ethereum_spec_tools.evm_tools import create_parser
        from ethereum_spec_tools.evm_tools.t8n import ForkCache, T8N

        with tempfile.TemporaryDirectory() as tmpdir:
            # Write minimal alloc file
            alloc_path = os.path.join(tmpdir, "alloc.json")
            with open(alloc_path, "w") as f:
                json.dump({}, f)

            # Write minimal env file
            env_path = os.path.join(tmpdir, "env.json")
            with open(env_path, "w") as f:
                json.dump({
                    "currentCoinbase": "0x" + "00" * 20,
                    "currentGasLimit": "0x1000000",
                    "currentNumber": "0x1",
                    "currentTimestamp": "0x64",
                    "currentBaseFee": "0x7",
                    "currentRandom": "0x" + "00" * 32,
                }, f)

            # Write minimal txs file
            txs_path = os.path.join(tmpdir, "txs.json")
            with open(txs_path, "w") as f:
                json.dump([], f)

            parser = create_parser()
            args = parser.parse_args([
                "t8n",
                "--state.fork", "Paris",
                "--input.alloc", alloc_path,
                "--input.env", env_path,
                "--input.txs", txs_path,
                "--output.basedir", tmpdir,
            ])

            with ForkCache() as cache:
                t8n = T8N(args, sys.stdout, sys.stdin, cache)

                # Standard mode should be used
                assert t8n.engine_mode is False
                assert t8n.payload is None
                # Standard mode attributes should be set
                assert t8n.env is not None
                assert t8n.txs is not None
                assert t8n.result is not None

    @pytest.mark.evm_tools
    def test_engine_mode_output_format(
        self, v1_payload_json: Dict[str, Any]
    ) -> None:
        """Test that engine mode outputs PayloadStatus JSON format."""
        from io import StringIO

        from ethereum_spec_tools.evm_tools import create_parser
        from ethereum_spec_tools.evm_tools.t8n import ForkCache, T8N

        with tempfile.TemporaryDirectory() as tmpdir:
            # Write payload file
            payload_path = os.path.join(tmpdir, "payload.json")
            with open(payload_path, "w") as f:
                json.dump(v1_payload_json, f)

            # Write minimal alloc file
            alloc_path = os.path.join(tmpdir, "alloc.json")
            with open(alloc_path, "w") as f:
                json.dump({}, f)

            parser = create_parser()
            args = parser.parse_args([
                "t8n",
                "--state.fork", "Paris",
                "--input.alloc", alloc_path,
                "--input.payload", payload_path,
                "--output.basedir", tmpdir,
                "--output.result", "stdout",
            ])

            out_buffer = StringIO()
            with ForkCache() as cache:
                t8n = T8N(args, out_buffer, sys.stdin, cache)
                exit_code = t8n.run()

                # Should complete without error
                assert exit_code == 0

                # Output should contain payloadStatus
                output = out_buffer.getvalue()
                result = json.loads(output)

                assert "payloadStatus" in result
                payload_status = result["payloadStatus"]
                assert "status" in payload_status
                assert "latestValidHash" in payload_status
                assert "validationError" in payload_status
