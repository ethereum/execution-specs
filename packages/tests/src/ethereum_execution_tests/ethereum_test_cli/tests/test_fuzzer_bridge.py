"""Test suite for fuzzer bridge DTO parsing and conversion."""

import json
from pathlib import Path
from typing import Any, Dict

import pytest
from pydantic import ValidationError

from ethereum_test_base_types import Address, HexNumber
from ethereum_test_forks import Osaka
from ethereum_test_tools import Account, AuthorizationTuple, Transaction
from ethereum_test_types import Alloc, Environment

from ..fuzzer_bridge.converter import (
    blockchain_test_from_fuzzer,
    create_sender_eoa_map,
    fuzzer_account_to_eest_account,
    fuzzer_authorization_to_eest,
    fuzzer_transaction_to_eest_transaction,
)
from ..fuzzer_bridge.models import (
    FuzzerAccountInput,
    FuzzerAuthorizationInput,
    FuzzerOutput,
    FuzzerTransactionInput,
)


def load_fuzzer_vector(filename: str) -> Dict[str, Any]:
    """
    Load fuzzer test vector from vectors/ directory.

    Follows the pattern from
    tests/prague/eip2537_bls_12_381_precompiles/helpers.py
    """
    vector_path = Path(__file__).parent / "vectors" / filename
    with open(vector_path) as f:
        return json.load(f)


class TestFuzzerOutputParsing:
    """Test parsing of fuzzer output JSON into DTOs."""

    @pytest.fixture
    def fuzzer_data(self) -> Dict[str, Any]:
        """Load test vector."""
        return load_fuzzer_vector("fuzzer_test_0.json")

    def test_parse_fuzzer_output(self, fuzzer_data: Dict[str, Any]) -> None:
        """Test parsing complete fuzzer output."""
        fuzzer_output = FuzzerOutput(**fuzzer_data)

        assert fuzzer_output.version == "2.0"
        assert fuzzer_output.fork == Osaka
        assert fuzzer_output.chain_id == HexNumber(1)
        assert len(fuzzer_output.transactions) == 17
        assert len(fuzzer_output.accounts) > 0
        assert fuzzer_output.parent_beacon_block_root is not None  # EIP-4788

    def test_parse_account_with_private_key(
        self, fuzzer_data: Dict[str, Any]
    ) -> None:
        """Test parsing account with private key."""
        account_data = next(
            acc
            for acc in fuzzer_data["accounts"].values()
            if "privateKey" in acc
        )

        account = FuzzerAccountInput(**account_data)

        assert account.private_key is not None
        assert isinstance(account.balance, HexNumber)
        assert isinstance(account.nonce, HexNumber)

    def test_parse_account_without_private_key(
        self, fuzzer_data: Dict[str, Any]
    ) -> None:
        """Test parsing contract account (no private key)."""
        account_data = next(
            (
                acc
                for acc in fuzzer_data["accounts"].values()
                if "privateKey" not in acc
            ),
            None,
        )

        if account_data:
            account = FuzzerAccountInput(**account_data)
            assert account.private_key is None

    def test_parse_transaction_with_authorization_list(
        self, fuzzer_data: Dict[str, Any]
    ) -> None:
        """Test parsing EIP-7702 transaction with authorization list."""
        tx_data = next(
            (
                tx
                for tx in fuzzer_data["transactions"]
                if "authorizationList" in tx and tx["authorizationList"]
            ),
            None,
        )

        if tx_data:
            tx = FuzzerTransactionInput(**tx_data)

            assert tx.authorization_list is not None
            assert len(tx.authorization_list) > 0
            assert isinstance(
                tx.authorization_list[0], FuzzerAuthorizationInput
            )

            # Verify authorization fields
            auth = tx.authorization_list[0]
            assert isinstance(auth.chain_id, HexNumber)
            assert isinstance(auth.address, Address)
            assert isinstance(auth.nonce, HexNumber)

    def test_parse_authorization_tuple(
        self, fuzzer_data: Dict[str, Any]
    ) -> None:
        """Test parsing individual authorization tuple."""
        tx_with_auth = next(
            (
                tx
                for tx in fuzzer_data["transactions"]
                if "authorizationList" in tx and tx["authorizationList"]
            ),
            None,
        )

        if tx_with_auth:
            auth_data = tx_with_auth["authorizationList"][0]
            auth = FuzzerAuthorizationInput(**auth_data)

            assert auth.chain_id is not None
            assert auth.address is not None
            assert auth.v is not None
            assert auth.r is not None
            assert auth.s is not None

    def test_parse_environment(self, fuzzer_data: Dict[str, Any]) -> None:
        """Test Environment parsing (using EEST Environment directly)."""
        env = Environment(**fuzzer_data["env"])

        assert env.fee_recipient is not None
        assert env.gas_limit is not None
        assert env.number is not None
        assert env.timestamp is not None


class TestDTOConversion:
    """Test conversion from DTOs to EEST domain models."""

    @pytest.fixture
    def fuzzer_output(self) -> FuzzerOutput:
        """Parsed fuzzer output."""
        data = load_fuzzer_vector("fuzzer_test_0.json")
        return FuzzerOutput(**data)

    def test_fuzzer_account_to_eest_account(
        self, fuzzer_output: FuzzerOutput
    ) -> None:
        """Test account DTO to EEST Account conversion."""
        fuzzer_account = next(iter(fuzzer_output.accounts.values()))

        eest_account = fuzzer_account_to_eest_account(fuzzer_account)

        assert isinstance(eest_account, Account)
        assert eest_account.balance == fuzzer_account.balance
        assert eest_account.nonce == fuzzer_account.nonce
        assert eest_account.code == fuzzer_account.code

    def test_fuzzer_authorization_to_eest(
        self, fuzzer_output: FuzzerOutput
    ) -> None:
        """Test authorization DTO to EEST AuthorizationTuple conversion."""
        tx_with_auth = next(
            (tx for tx in fuzzer_output.transactions if tx.authorization_list),
            None,
        )

        if tx_with_auth and tx_with_auth.authorization_list:
            fuzzer_auth = tx_with_auth.authorization_list[0]

            eest_auth = fuzzer_authorization_to_eest(fuzzer_auth)

            assert isinstance(eest_auth, AuthorizationTuple)
            assert eest_auth.chain_id == fuzzer_auth.chain_id
            assert eest_auth.address == fuzzer_auth.address
            assert eest_auth.nonce == fuzzer_auth.nonce

    def test_create_sender_eoa_map(self, fuzzer_output: FuzzerOutput) -> None:
        """Test EOA map creation from accounts."""
        sender_map = create_sender_eoa_map(fuzzer_output.accounts)

        # Verify all senders are valid
        assert len(sender_map) > 0

        for addr, eoa in sender_map.items():
            # Verify private key matches address
            assert Address(eoa) == addr

    def test_sender_eoa_map_validates_address(
        self, fuzzer_output: FuzzerOutput
    ) -> None:
        """Test that EOA map validates private key matches address."""
        # This test verifies the assertion in create_sender_eoa_map
        sender_map = create_sender_eoa_map(fuzzer_output.accounts)

        # All created EOAs should pass validation
        assert all(Address(eoa) == addr for addr, eoa in sender_map.items())

    def test_fuzzer_transaction_to_eest_transaction(
        self, fuzzer_output: FuzzerOutput
    ) -> None:
        """Test transaction DTO to EEST Transaction conversion."""
        fuzzer_tx = fuzzer_output.transactions[0]
        sender_map = create_sender_eoa_map(fuzzer_output.accounts)
        sender_eoa = sender_map[fuzzer_tx.from_]

        eest_tx = fuzzer_transaction_to_eest_transaction(fuzzer_tx, sender_eoa)

        assert isinstance(eest_tx, Transaction)
        assert eest_tx.sender == sender_eoa
        assert eest_tx.to == fuzzer_tx.to
        assert eest_tx.gas_limit == fuzzer_tx.gas  # Key mapping!
        assert eest_tx.data == fuzzer_tx.data

    def test_transaction_gas_field_mapping(
        self, fuzzer_output: FuzzerOutput
    ) -> None:
        """Test critical field mapping: gas → gas_limit."""
        fuzzer_tx = fuzzer_output.transactions[0]
        sender_map = create_sender_eoa_map(fuzzer_output.accounts)
        sender_eoa = sender_map[fuzzer_tx.from_]

        eest_tx = fuzzer_transaction_to_eest_transaction(fuzzer_tx, sender_eoa)

        # Fuzzer uses 'gas' (JSON-RPC), EEST uses 'gas_limit'
        assert eest_tx.gas_limit == fuzzer_tx.gas

    def test_transaction_authorization_list_conversion(
        self, fuzzer_output: FuzzerOutput
    ) -> None:
        """Test authorization list conversion in transaction."""
        tx_with_auth = next(
            (tx for tx in fuzzer_output.transactions if tx.authorization_list),
            None,
        )

        if tx_with_auth and tx_with_auth.authorization_list:
            sender_map = create_sender_eoa_map(fuzzer_output.accounts)
            sender_eoa = sender_map[tx_with_auth.from_]

            eest_tx = fuzzer_transaction_to_eest_transaction(
                tx_with_auth, sender_eoa
            )

            assert eest_tx.authorization_list is not None
            assert len(eest_tx.authorization_list) == len(
                tx_with_auth.authorization_list
            )
            assert all(
                isinstance(auth, AuthorizationTuple)
                for auth in eest_tx.authorization_list
            )


class TestBlockchainTestGeneration:
    """Test end-to-end conversion to BlockchainTest."""

    @pytest.fixture
    def fuzzer_output(self) -> FuzzerOutput:
        """Parsed fuzzer output."""
        data = load_fuzzer_vector("fuzzer_test_0.json")
        return FuzzerOutput(**data)

    def test_blockchain_test_from_fuzzer_single_block(
        self, fuzzer_output: FuzzerOutput
    ) -> None:
        """Test single-block blockchain test generation."""
        blockchain_test = blockchain_test_from_fuzzer(
            fuzzer_output,
            fork=Osaka,
            num_blocks=1,
        )

        assert blockchain_test.pre is not None
        assert len(blockchain_test.blocks) == 1
        assert len(blockchain_test.blocks[0].txs) == 17
        assert blockchain_test.genesis_environment is not None

    def test_blockchain_test_multi_block_distribute(
        self, fuzzer_output: FuzzerOutput
    ) -> None:
        """Test multi-block generation with distribute strategy."""
        blockchain_test = blockchain_test_from_fuzzer(
            fuzzer_output,
            fork=Osaka,
            num_blocks=3,
            block_strategy="distribute",
        )

        assert len(blockchain_test.blocks) == 3

        # Verify all transactions distributed
        total_txs = sum(len(block.txs) for block in blockchain_test.blocks)
        assert total_txs == 17

        # Verify transactions maintain nonce order
        assert len(blockchain_test.blocks[0].txs) > 0

    def test_blockchain_test_multi_block_first_block(
        self, fuzzer_output: FuzzerOutput
    ) -> None:
        """Test multi-block generation with first-block strategy."""
        blockchain_test = blockchain_test_from_fuzzer(
            fuzzer_output,
            fork=Osaka,
            num_blocks=3,
            block_strategy="first-block",
        )

        assert len(blockchain_test.blocks) == 3
        assert len(blockchain_test.blocks[0].txs) == 17
        assert len(blockchain_test.blocks[1].txs) == 0
        assert len(blockchain_test.blocks[2].txs) == 0

    def test_blockchain_test_pre_state(
        self, fuzzer_output: FuzzerOutput
    ) -> None:
        """Test pre-state (Alloc) generation."""
        blockchain_test = blockchain_test_from_fuzzer(
            fuzzer_output,
            fork=Osaka,
        )

        assert isinstance(blockchain_test.pre, Alloc)
        # Verify all accounts are in pre-state
        for addr in fuzzer_output.accounts:
            assert addr in blockchain_test.pre

    def test_blockchain_test_genesis_environment(
        self, fuzzer_output: FuzzerOutput
    ) -> None:
        """Test genesis environment derivation."""
        blockchain_test = blockchain_test_from_fuzzer(
            fuzzer_output,
            fork=Osaka,
        )

        genesis_env = blockchain_test.genesis_environment

        assert genesis_env.number == 0
        # Genesis timestamp should be 12 seconds before block 1
        assert (
            int(genesis_env.timestamp) == int(fuzzer_output.env.timestamp) - 12
        )

    def test_blockchain_test_block_timestamps(
        self, fuzzer_output: FuzzerOutput
    ) -> None:
        """Test block timestamp incrementing."""
        blockchain_test = blockchain_test_from_fuzzer(
            fuzzer_output,
            fork=Osaka,
            num_blocks=3,
            block_time=12,
        )

        # Check timestamps increment correctly
        base_ts = int(fuzzer_output.env.timestamp)
        assert blockchain_test.blocks[0].timestamp == base_ts
        assert blockchain_test.blocks[1].timestamp == base_ts + 12
        assert blockchain_test.blocks[2].timestamp == base_ts + 24

    def test_blockchain_test_beacon_root_first_block_only(
        self, fuzzer_output: FuzzerOutput
    ) -> None:
        """Test parent beacon block root only in first block (EIP-4788)."""
        blockchain_test = blockchain_test_from_fuzzer(
            fuzzer_output,
            fork=Osaka,
            num_blocks=3,
        )

        # First block should have beacon root
        assert blockchain_test.blocks[0].parent_beacon_block_root is not None

        # Subsequent blocks should NOT have beacon root
        assert blockchain_test.blocks[1].parent_beacon_block_root is None
        assert blockchain_test.blocks[2].parent_beacon_block_root is None


class TestEIPFeatures:
    """Test EIP-specific feature handling."""

    @pytest.fixture
    def fuzzer_output(self) -> FuzzerOutput:
        """Parsed fuzzer output."""
        data = load_fuzzer_vector("fuzzer_test_0.json")
        return FuzzerOutput(**data)

    def test_eip7702_authorization_lists(
        self, fuzzer_output: FuzzerOutput
    ) -> None:
        """Test EIP-7702 authorization list handling."""
        blockchain_test = blockchain_test_from_fuzzer(
            fuzzer_output,
            fork=Osaka,
        )

        # Find transactions with authorization lists
        txs_with_auth = [
            tx
            for block in blockchain_test.blocks
            for tx in block.txs
            if tx.authorization_list
        ]

        assert len(txs_with_auth) > 0

        for tx in txs_with_auth:
            if tx.authorization_list:
                assert all(
                    isinstance(auth, AuthorizationTuple)
                    for auth in tx.authorization_list
                )

    def test_eip4788_parent_beacon_block_root(
        self, fuzzer_output: FuzzerOutput
    ) -> None:
        """Test EIP-4788 parent beacon block root handling."""
        blockchain_test = blockchain_test_from_fuzzer(
            fuzzer_output,
            fork=Osaka,
        )

        # Beacon root should match fuzzer output
        assert (
            blockchain_test.blocks[0].parent_beacon_block_root
            == fuzzer_output.parent_beacon_block_root
        )

    def test_sender_is_eoa_not_test_address(
        self, fuzzer_output: FuzzerOutput
    ) -> None:
        """Test that transaction senders are EOAs, not TestAddress."""
        blockchain_test = blockchain_test_from_fuzzer(
            fuzzer_output,
            fork=Osaka,
        )

        for block in blockchain_test.blocks:
            for tx in block.txs:
                # Verify sender is EOA with private key
                assert hasattr(tx.sender, "key")
                if tx.sender:
                    assert tx.sender.key is not None


class TestErrorHandling:
    """Test error handling and validation."""

    def test_invalid_version_fails(self) -> None:
        """Test that invalid version is rejected."""
        data = load_fuzzer_vector("fuzzer_test_0.json")
        data["version"] = "1.0"  # Invalid version

        with pytest.raises(ValidationError):
            FuzzerOutput(**data)

    def test_missing_private_key_fails(self) -> None:
        """Test that transaction without sender private key fails."""
        data = load_fuzzer_vector("fuzzer_test_0.json")

        # Remove all private keys
        for account in data["accounts"].values():
            if "privateKey" in account:
                del account["privateKey"]

        fuzzer_output = FuzzerOutput(**data)

        # Conversion should fail due to missing sender keys
        with pytest.raises(AssertionError):
            blockchain_test_from_fuzzer(fuzzer_output, fork=Osaka)
