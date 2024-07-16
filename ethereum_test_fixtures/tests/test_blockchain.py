"""
Test the blockchain test types.
"""

from typing import Any, Dict

import pytest

from ethereum_test_base_types import (
    Address,
    Bloom,
    Bytes,
    Hash,
    HeaderNonce,
    ZeroPaddedHexNumber,
    to_json,
)
from ethereum_test_exceptions import BlockException, EngineAPIError, TransactionException
from ethereum_test_types import AccessList, Transaction, Withdrawal

from ..blockchain import (
    FixtureBlockBase,
    FixtureEngineNewPayload,
    FixtureExecutionPayload,
    FixtureHeader,
    FixtureTransaction,
    InvalidFixtureBlock,
)

fixture_header_ones = FixtureHeader(
    parent_hash=Hash(1),
    ommers_hash=Hash(1),
    fee_recipient=Address(1),
    state_root=Hash(1),
    transactions_trie=Hash(1),
    receipts_root=Hash(1),
    logs_bloom=Bloom(1),
    difficulty=1,
    number=1,
    gas_limit=1,
    gas_used=1,
    timestamp=1,
    extra_data=Bytes([1]),
    prev_randao=Hash(1),
    nonce=HeaderNonce(1),
    base_fee_per_gas=1,
    withdrawals_root=Hash(1),
    blob_gas_used=1,
    excess_blob_gas=1,
    # hash=Hash(1),
)


@pytest.mark.parametrize(
    ["can_be_deserialized", "model_instance", "json"],
    [
        pytest.param(
            True,
            FixtureTransaction.from_transaction(Transaction().with_signature_and_sender()),
            {
                "type": "0x00",
                "chainId": "0x01",
                "nonce": "0x00",
                "to": "0x00000000000000000000000000000000000000aa",
                "value": "0x00",
                "data": "0x",
                "gasLimit": "0x5208",
                "gasPrice": "0x0a",
                "v": "0x26",
                "r": "0xcc61d852649c34cc0b71803115f38036ace257d2914f087bf885e6806a664fbd",
                "s": "0x2020cb35f5d7731ab540d62614503a7f2344301a86342f67daf011c1341551ff",
                "sender": "0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b",
            },
            id="fixture_transaction_type_0_default_values",
        ),
        pytest.param(
            True,
            FixtureTransaction.from_transaction(Transaction(to=None).with_signature_and_sender()),
            {
                "type": "0x00",
                "chainId": "0x01",
                "to": "",
                "nonce": "0x00",
                "value": "0x00",
                "data": "0x",
                "gasLimit": "0x5208",
                "gasPrice": "0x0a",
                "v": "0x25",
                "r": "0x1cfe2cbb0c3577f74d9ae192a7f1ee2d670fe806a040f427af9cb768be3d07ce",
                "s": "0x0cbe2d029f52dbf93ade486625bed0603945d2c7358b31de99fe8786c00f13da",
                "sender": "0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b",
            },
            id="fixture_transaction_type_0_contract_creation",
        ),
        pytest.param(
            True,
            FixtureTransaction.from_transaction(Transaction(ty=1).with_signature_and_sender()),
            {
                "type": "0x01",
                "chainId": "0x01",
                "nonce": "0x00",
                "to": "0x00000000000000000000000000000000000000aa",
                "value": "0x00",
                "data": "0x",
                "gasLimit": "0x5208",
                "gasPrice": "0x0a",
                "accessList": [],
                "v": "0x01",
                "r": "0x58b4ddaa529492d32b6bc8327eb8ee0bc8b535c3bfc0f4f1db3d7c16b51d1851",
                "s": "0x5ef19167661b14d06dfc785bf62693e6f9e5a44e7c11e0320efed27b27294970",
                "sender": "0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b",
            },
            id="fixture_transaction_type_1_default_values",
        ),
        pytest.param(
            True,
            FixtureTransaction.from_transaction(
                Transaction(ty=2, max_fee_per_gas=7).with_signature_and_sender()
            ),
            {
                "type": "0x02",
                "chainId": "0x01",
                "nonce": "0x00",
                "to": "0x00000000000000000000000000000000000000aa",
                "value": "0x00",
                "data": "0x",
                "gasLimit": "0x5208",
                "maxPriorityFeePerGas": "0x00",
                "maxFeePerGas": "0x07",
                "accessList": [],
                "v": "0x00",
                "r": "0x33fc39081d01f8e7f0ce5426d4a00a7b07c2edea064d24a8cac8e4b1f0c08298",
                "s": "0x4635e1c45238697db38e37070d4fce27fb5684f9dec4046466ea42a9834bad0a",
                "sender": "0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b",
            },
            id="fixture_transaction_type_2_default_values",
        ),
        pytest.param(
            True,
            FixtureTransaction.from_transaction(
                Transaction(
                    ty=3,
                    max_fee_per_gas=7,
                    max_fee_per_blob_gas=1,
                    blob_versioned_hashes=[],
                ).with_signature_and_sender()
            ),
            {
                "type": "0x03",
                "chainId": "0x01",
                "nonce": "0x00",
                "to": "0x00000000000000000000000000000000000000aa",
                "value": "0x00",
                "data": "0x",
                "gasLimit": "0x5208",
                "maxPriorityFeePerGas": "0x00",
                "maxFeePerGas": "0x07",
                "maxFeePerBlobGas": "0x01",
                "accessList": [],
                "blobVersionedHashes": [],
                "v": "0x01",
                "r": "0x8978475a00bf155bf5687dfda89c2df55ef6c341cdfd689aeaa6c519569a530a",
                "s": "0x66fc34935cdd191441a12a2e7b1f224cb40b928afb9bc89c8ddb2b78c19342cc",
                "sender": "0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b",
            },
            id="fixture_transaction_type_3_default_values",
        ),
        pytest.param(
            True,
            FixtureTransaction.from_transaction(
                Transaction(
                    to=0x1234,
                    data=b"\x01\x00",
                    access_list=[
                        AccessList(
                            address=0x1234,
                            storage_keys=[0, 1],
                        )
                    ],
                    max_priority_fee_per_gas=10,
                    max_fee_per_gas=20,
                    max_fee_per_blob_gas=30,
                    blob_versioned_hashes=[0, 1],
                ).with_signature_and_sender()
            ),
            {
                "type": "0x03",
                "chainId": "0x01",
                "nonce": "0x00",
                "to": "0x0000000000000000000000000000000000001234",
                "accessList": [
                    {
                        "address": "0x0000000000000000000000000000000000001234",
                        "storageKeys": [
                            "0x0000000000000000000000000000000000000000000000000000000000000000",
                            "0x0000000000000000000000000000000000000000000000000000000000000001",
                        ],
                    }
                ],
                "value": "0x00",
                "data": "0x0100",
                "gasLimit": "0x5208",
                "maxPriorityFeePerGas": "0x0a",
                "maxFeePerGas": "0x14",
                "maxFeePerBlobGas": "0x1e",
                "blobVersionedHashes": [
                    "0x0000000000000000000000000000000000000000000000000000000000000000",
                    "0x0000000000000000000000000000000000000000000000000000000000000001",
                ],
                "v": "0x00",
                "r": "0x418bb557c43262375f80556cb09dac5e67396acf0eaaf2c2540523d1ce54b280",
                "s": "0x4fa36090ea68a1138043d943ced123c0b0807d82ff3342a6977cbc09230e927c",
                "sender": "0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b",
            },
            id="fixture_transaction_3",
        ),
        pytest.param(
            True,
            FixtureHeader(
                parent_hash=Hash(0),
                ommers_hash=Hash(1),
                fee_recipient=Address(2),
                state_root=Hash(3),
                transactions_trie=Hash(4),
                receipts_root=Hash(5),
                logs_bloom=Bloom(6),
                difficulty=7,
                number=8,
                gas_limit=9,
                gas_used=10,
                timestamp=11,
                extra_data=Bytes([12]),
                prev_randao=Hash(13),
                nonce=HeaderNonce(14),
            ),
            {
                "parentHash": Hash(0).hex(),
                "uncleHash": Hash(1).hex(),
                "coinbase": Address(2).hex(),
                "stateRoot": Hash(3).hex(),
                "transactionsTrie": Hash(4).hex(),
                "receiptTrie": Hash(5).hex(),
                "bloom": Bloom(6).hex(),
                "difficulty": ZeroPaddedHexNumber(7).hex(),
                "number": ZeroPaddedHexNumber(8).hex(),
                "gasLimit": ZeroPaddedHexNumber(9).hex(),
                "gasUsed": ZeroPaddedHexNumber(10).hex(),
                "timestamp": ZeroPaddedHexNumber(11).hex(),
                "extraData": Bytes([12]).hex(),
                "mixHash": Hash(13).hex(),
                "nonce": HeaderNonce(14).hex(),
                "hash": "0x1dc087517148c2d6a1dd1ea5de107bc5f728414f9d210ed18286d305abe6ba5e",
            },
            id="fixture_header_1",
        ),
        pytest.param(
            True,
            FixtureHeader(
                parent_hash=Hash(0),
                ommers_hash=Hash(1),
                fee_recipient=Address(2),
                state_root=Hash(3),
                transactions_trie=Hash(4),
                receipts_root=Hash(5),
                logs_bloom=Bloom(6),
                difficulty=7,
                number=8,
                gas_limit=9,
                gas_used=10,
                timestamp=11,
                extra_data=Bytes([12]),
                prev_randao=Hash(13),
                nonce=HeaderNonce(14),
                base_fee_per_gas=15,
                withdrawals_root=Hash(16),
                blob_gas_used=17,
                excess_blob_gas=18,
                # hash=Hash(19),
            ),
            {
                "parentHash": Hash(0).hex(),
                "uncleHash": Hash(1).hex(),
                "coinbase": Address(2).hex(),
                "stateRoot": Hash(3).hex(),
                "transactionsTrie": Hash(4).hex(),
                "receiptTrie": Hash(5).hex(),
                "bloom": Bloom(6).hex(),
                "difficulty": ZeroPaddedHexNumber(7).hex(),
                "number": ZeroPaddedHexNumber(8).hex(),
                "gasLimit": ZeroPaddedHexNumber(9).hex(),
                "gasUsed": ZeroPaddedHexNumber(10).hex(),
                "timestamp": ZeroPaddedHexNumber(11).hex(),
                "extraData": Bytes([12]).hex(),
                "mixHash": Hash(13).hex(),
                "nonce": HeaderNonce(14).hex(),
                "baseFeePerGas": ZeroPaddedHexNumber(15).hex(),
                "withdrawalsRoot": Hash(16).hex(),
                "blobGasUsed": ZeroPaddedHexNumber(17).hex(),
                "excessBlobGas": ZeroPaddedHexNumber(18).hex(),
                "hash": "0xd90115b7fde329f64335763a446af150ab67e639281dccdb07a007d18bb80211",
            },
            id="fixture_header_2",
        ),
        pytest.param(
            True,
            FixtureBlockBase(
                header=FixtureHeader(
                    parent_hash=Hash(0),
                    ommers_hash=Hash(1),
                    fee_recipient=Address(2),
                    state_root=Hash(3),
                    transactions_trie=Hash(4),
                    receipts_root=Hash(5),
                    logs_bloom=Bloom(6),
                    difficulty=7,
                    number=8,
                    gas_limit=9,
                    gas_used=10,
                    timestamp=11,
                    extra_data=Bytes([12]),
                    prev_randao=Hash(13),
                    nonce=HeaderNonce(14),
                    base_fee_per_gas=15,
                    withdrawals_root=Hash(16),
                    blob_gas_used=17,
                    excess_blob_gas=18,
                    # hash=Hash(19),
                ),
                transactions=[
                    FixtureTransaction.from_transaction(Transaction().with_signature_and_sender())
                ],
            ),
            {
                "blockHeader": {
                    "parentHash": Hash(0).hex(),
                    "uncleHash": Hash(1).hex(),
                    "coinbase": Address(2).hex(),
                    "stateRoot": Hash(3).hex(),
                    "transactionsTrie": Hash(4).hex(),
                    "receiptTrie": Hash(5).hex(),
                    "bloom": Bloom(6).hex(),
                    "difficulty": ZeroPaddedHexNumber(7).hex(),
                    "number": ZeroPaddedHexNumber(8).hex(),
                    "gasLimit": ZeroPaddedHexNumber(9).hex(),
                    "gasUsed": ZeroPaddedHexNumber(10).hex(),
                    "timestamp": ZeroPaddedHexNumber(11).hex(),
                    "extraData": Bytes([12]).hex(),
                    "mixHash": Hash(13).hex(),
                    "nonce": HeaderNonce(14).hex(),
                    "baseFeePerGas": ZeroPaddedHexNumber(15).hex(),
                    "withdrawalsRoot": Hash(16).hex(),
                    "blobGasUsed": ZeroPaddedHexNumber(17).hex(),
                    "excessBlobGas": ZeroPaddedHexNumber(18).hex(),
                    "hash": "0xd90115b7fde329f64335763a446af150ab67e639281dccdb07a007d18bb80211",
                },
                "blocknumber": "8",
                "uncleHeaders": [],
                "transactions": [
                    {
                        "type": "0x00",
                        "chainId": "0x01",
                        "nonce": "0x00",
                        "to": "0x00000000000000000000000000000000000000aa",
                        "value": "0x00",
                        "data": "0x",
                        "gasLimit": "0x5208",
                        "gasPrice": "0x0a",
                        "v": "0x26",
                        "r": "0xcc61d852649c34cc0b71803115f38036ace257d2914f087bf885e6806a664fbd",
                        "s": "0x2020cb35f5d7731ab540d62614503a7f2344301a86342f67daf011c1341551ff",
                        "sender": "0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b",
                    }
                ],
            },
            id="fixture_block_1",
        ),
        pytest.param(
            True,
            FixtureBlockBase(
                header=FixtureHeader(
                    parent_hash=Hash(0),
                    ommers_hash=Hash(1),
                    fee_recipient=Address(2),
                    state_root=Hash(3),
                    transactions_trie=Hash(4),
                    receipts_root=Hash(5),
                    logs_bloom=Bloom(6),
                    difficulty=7,
                    number=8,
                    gas_limit=9,
                    gas_used=10,
                    timestamp=11,
                    extra_data=Bytes([12]),
                    prev_randao=Hash(13),
                    nonce=HeaderNonce(14),
                    base_fee_per_gas=15,
                    withdrawals_root=Hash(16),
                    blob_gas_used=17,
                    excess_blob_gas=18,
                    # hash=Hash(19),
                ),
                transactions=[
                    FixtureTransaction.from_transaction(
                        Transaction(to=None).with_signature_and_sender()
                    )
                ],
            ),
            {
                "blockHeader": {
                    "parentHash": Hash(0).hex(),
                    "uncleHash": Hash(1).hex(),
                    "coinbase": Address(2).hex(),
                    "stateRoot": Hash(3).hex(),
                    "transactionsTrie": Hash(4).hex(),
                    "receiptTrie": Hash(5).hex(),
                    "bloom": Bloom(6).hex(),
                    "difficulty": ZeroPaddedHexNumber(7).hex(),
                    "number": ZeroPaddedHexNumber(8).hex(),
                    "gasLimit": ZeroPaddedHexNumber(9).hex(),
                    "gasUsed": ZeroPaddedHexNumber(10).hex(),
                    "timestamp": ZeroPaddedHexNumber(11).hex(),
                    "extraData": Bytes([12]).hex(),
                    "mixHash": Hash(13).hex(),
                    "nonce": HeaderNonce(14).hex(),
                    "baseFeePerGas": ZeroPaddedHexNumber(15).hex(),
                    "withdrawalsRoot": Hash(16).hex(),
                    "blobGasUsed": ZeroPaddedHexNumber(17).hex(),
                    "excessBlobGas": ZeroPaddedHexNumber(18).hex(),
                    "hash": "0xd90115b7fde329f64335763a446af150ab67e639281dccdb07a007d18bb80211",
                },
                "blocknumber": "8",
                "uncleHeaders": [],
                "transactions": [
                    {
                        "type": "0x00",
                        "chainId": "0x01",
                        "to": "",
                        "nonce": "0x00",
                        "value": "0x00",
                        "data": "0x",
                        "gasLimit": "0x5208",
                        "gasPrice": "0x0a",
                        "v": "0x25",
                        "r": "0x1cfe2cbb0c3577f74d9ae192a7f1ee2d670fe806a040f427af9cb768be3d07ce",
                        "s": "0x0cbe2d029f52dbf93ade486625bed0603945d2c7358b31de99fe8786c00f13da",
                        "sender": "0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b",
                    }
                ],
            },
            id="fixture_block_2",
        ),
        pytest.param(
            True,
            InvalidFixtureBlock(
                rlp="0x00",
                expect_exception=BlockException.RLP_STRUCTURES_ENCODING,
            ),
            {
                "rlp": "0x00",
                "expectException": "BlockException.RLP_STRUCTURES_ENCODING",
            },
            id="invalid_fixture_block_1",
        ),
        pytest.param(
            True,
            InvalidFixtureBlock(
                rlp="0x00",
                expect_exception=TransactionException.INTRINSIC_GAS_TOO_LOW,
            ),
            {
                "rlp": "0x00",
                "expectException": "TransactionException.INTRINSIC_GAS_TOO_LOW",
            },
            id="invalid_fixture_block_2",
        ),
        pytest.param(
            False,  # Can not be deserialized: A single expect_exception str will not be
            # deserialized as a list and therefore will not match the model_instance definition.
            InvalidFixtureBlock(
                rlp="0x00",
                expect_exception=[TransactionException.INTRINSIC_GAS_TOO_LOW],
            ),
            {
                "rlp": "0x00",
                "expectException": "TransactionException.INTRINSIC_GAS_TOO_LOW",
            },
            id="invalid_fixture_block_3",
        ),
        pytest.param(
            True,
            InvalidFixtureBlock(
                rlp="0x00",
                expect_exception=[
                    BlockException.RLP_STRUCTURES_ENCODING,
                    TransactionException.INTRINSIC_GAS_TOO_LOW,
                ],
            ),
            {
                "rlp": "0x00",
                "expectException": "BlockException.RLP_STRUCTURES_ENCODING|"
                "TransactionException.INTRINSIC_GAS_TOO_LOW",
            },
            id="invalid_fixture_block_4",
        ),
        pytest.param(
            True,
            FixtureExecutionPayload.from_fixture_header(
                header=FixtureHeader(
                    parent_hash=Hash(0),
                    ommers_hash=Hash(1),
                    fee_recipient=Address(2),
                    state_root=Hash(3),
                    transactions_trie=Hash(4),
                    receipts_root=Hash(5),
                    logs_bloom=Bloom(6),
                    difficulty=7,
                    number=8,
                    gas_limit=9,
                    gas_used=10,
                    timestamp=11,
                    extra_data=Bytes([12]),
                    prev_randao=Hash(13),
                    nonce=HeaderNonce(14),
                    base_fee_per_gas=15,
                    withdrawals_root=Hash(16),
                    blob_gas_used=17,
                    excess_blob_gas=18,
                    # hash=Hash(19),
                ),
                transactions=[
                    Transaction(
                        to=0x1234,
                        data=b"\x01\x00",
                        access_list=[
                            AccessList(
                                address=0x1234,
                                storage_keys=[0, 1],
                            )
                        ],
                        max_priority_fee_per_gas=10,
                        max_fee_per_gas=20,
                        max_fee_per_blob_gas=30,
                        blob_versioned_hashes=[0, 1],
                    ).with_signature_and_sender(),
                ],
                withdrawals=[Withdrawal(index=0, validator_index=1, address=0x1234, amount=2)],
                requests=None,
            ),
            {
                "parentHash": Hash(0).hex(),
                "feeRecipient": Address(2).hex(),
                "stateRoot": Hash(3).hex(),
                "receiptsRoot": Hash(5).hex(),
                "logsBloom": Bloom(6).hex(),
                "blockNumber": hex(8),
                "gasLimit": hex(9),
                "gasUsed": hex(10),
                "timestamp": hex(11),
                "extraData": Bytes([12]).hex(),
                "prevRandao": Hash(13).hex(),
                "baseFeePerGas": hex(15),
                "blobGasUsed": hex(17),
                "excessBlobGas": hex(18),
                "blockHash": "0xd90115b7fde329f64335763a446af150ab67e639281dccdb07a007d18bb80211",
                "transactions": [
                    "0x"
                    + Transaction(
                        to=0x1234,
                        data=b"\x01\x00",
                        access_list=[
                            AccessList(
                                address=0x1234,
                                storage_keys=[0, 1],
                            )
                        ],
                        max_priority_fee_per_gas=10,
                        max_fee_per_gas=20,
                        max_fee_per_blob_gas=30,
                        blob_versioned_hashes=[0, 1],
                    )
                    .with_signature_and_sender()
                    .rlp.hex()
                ],
                "withdrawals": [
                    to_json(Withdrawal(index=0, validator_index=1, address=0x1234, amount=2))
                ],
            },
            id="fixture_execution_payload_1",
        ),
        pytest.param(
            True,
            FixtureEngineNewPayload(
                execution_payload=FixtureExecutionPayload.from_fixture_header(
                    header=FixtureHeader(
                        parent_hash=Hash(0),
                        ommers_hash=Hash(1),
                        fee_recipient=Address(2),
                        state_root=Hash(3),
                        transactions_trie=Hash(4),
                        receipts_root=Hash(5),
                        logs_bloom=Bloom(6),
                        difficulty=7,
                        number=8,
                        gas_limit=9,
                        gas_used=10,
                        timestamp=11,
                        extra_data=Bytes([12]),
                        prev_randao=Hash(13),
                        nonce=HeaderNonce(14),
                        base_fee_per_gas=15,
                        withdrawals_root=Hash(16),
                        blob_gas_used=17,
                        excess_blob_gas=18,
                        hash=Hash(19),
                    ),
                    transactions=[
                        Transaction(
                            to=0x1234,
                            data=b"\x01\x00",
                            access_list=[
                                AccessList(
                                    address=0x1234,
                                    storage_keys=[0, 1],
                                )
                            ],
                            max_priority_fee_per_gas=10,
                            max_fee_per_gas=20,
                            max_fee_per_blob_gas=30,
                            blob_versioned_hashes=[0, 1],
                        ).with_signature_and_sender(),
                    ],
                    withdrawals=[
                        Withdrawal(
                            index=0,
                            validator_index=1,
                            address=0x1234,
                            amount=2,
                        )
                    ],
                    requests=None,
                ),
                validation_error=TransactionException.INTRINSIC_GAS_TOO_LOW,
                version=1,
            ),
            {
                "executionPayload": {
                    "parentHash": Hash(0).hex(),
                    "feeRecipient": Address(2).hex(),
                    "stateRoot": Hash(3).hex(),
                    "receiptsRoot": Hash(5).hex(),
                    "logsBloom": Bloom(6).hex(),
                    "blockNumber": hex(8),
                    "gasLimit": hex(9),
                    "gasUsed": hex(10),
                    "timestamp": hex(11),
                    "extraData": Bytes([12]).hex(),
                    "prevRandao": Hash(13).hex(),
                    "baseFeePerGas": hex(15),
                    "blobGasUsed": hex(17),
                    "excessBlobGas": hex(18),
                    "blockHash": (
                        "0xd90115b7fde329f64335763a446af150ab67e639281dccdb07a007d18bb80211"
                    ),
                    "transactions": [
                        "0x"
                        + Transaction(
                            to=0x1234,
                            data=b"\x01\x00",
                            access_list=[
                                AccessList(
                                    address=0x1234,
                                    storage_keys=[0, 1],
                                )
                            ],
                            max_priority_fee_per_gas=10,
                            max_fee_per_gas=20,
                            max_fee_per_blob_gas=30,
                            blob_versioned_hashes=[0, 1],
                        )
                        .with_signature_and_sender()
                        .rlp.hex()
                    ],
                    "withdrawals": [
                        to_json(
                            Withdrawal(
                                index=0,
                                validator_index=1,
                                address=0x1234,
                                amount=2,
                            )
                        )
                    ],
                },
                "validationError": "TransactionException.INTRINSIC_GAS_TOO_LOW",
                "version": "1",
            },
            id="fixture_engine_new_payload_1",
        ),
        pytest.param(
            True,
            FixtureEngineNewPayload(
                execution_payload=FixtureExecutionPayload.from_fixture_header(
                    header=FixtureHeader(
                        parent_hash=Hash(0),
                        ommers_hash=Hash(1),
                        fee_recipient=Address(2),
                        state_root=Hash(3),
                        transactions_trie=Hash(4),
                        receipts_root=Hash(5),
                        logs_bloom=Bloom(6),
                        difficulty=7,
                        number=8,
                        gas_limit=9,
                        gas_used=10,
                        timestamp=11,
                        extra_data=Bytes([12]),
                        prev_randao=Hash(13),
                        nonce=HeaderNonce(14),
                        base_fee_per_gas=15,
                        withdrawals_root=Hash(16),
                        blob_gas_used=17,
                        excess_blob_gas=18,
                    ),
                    transactions=[
                        Transaction(
                            to=0x1234,
                            data=b"\x01\x00",
                            access_list=[
                                AccessList(
                                    address=0x1234,
                                    storage_keys=[0, 1],
                                )
                            ],
                            max_priority_fee_per_gas=10,
                            max_fee_per_gas=20,
                            max_fee_per_blob_gas=30,
                            blob_versioned_hashes=[0, 1],
                        ).with_signature_and_sender(),
                    ],
                    withdrawals=[Withdrawal(index=0, validator_index=1, address=0x1234, amount=2)],
                    requests=None,
                ),
                version=1,
                validation_error=[
                    BlockException.INCORRECT_BLOCK_FORMAT,
                    TransactionException.INTRINSIC_GAS_TOO_LOW,
                ],
                blob_versioned_hashes=[bytes([0]), bytes([1])],
                error_code=EngineAPIError.InvalidRequest,
            ),
            {
                "executionPayload": {
                    "parentHash": Hash(0).hex(),
                    "feeRecipient": Address(2).hex(),
                    "stateRoot": Hash(3).hex(),
                    "receiptsRoot": Hash(5).hex(),
                    "logsBloom": Bloom(6).hex(),
                    "blockNumber": hex(8),
                    "gasLimit": hex(9),
                    "gasUsed": hex(10),
                    "timestamp": hex(11),
                    "extraData": Bytes([12]).hex(),
                    "prevRandao": Hash(13).hex(),
                    "baseFeePerGas": hex(15),
                    "blobGasUsed": hex(17),
                    "excessBlobGas": hex(18),
                    "blockHash": (
                        "0xd90115b7fde329f64335763a446af150ab67e639281dccdb07a007d18bb80211"
                    ),
                    "transactions": [
                        "0x"
                        + Transaction(
                            to=0x1234,
                            data=b"\x01\x00",
                            access_list=[
                                AccessList(
                                    address=0x1234,
                                    storage_keys=[0, 1],
                                )
                            ],
                            max_priority_fee_per_gas=10,
                            max_fee_per_gas=20,
                            max_fee_per_blob_gas=30,
                            blob_versioned_hashes=[0, 1],
                        )
                        .with_signature_and_sender()
                        .rlp.hex()
                    ],
                    "withdrawals": [
                        to_json(
                            Withdrawal(
                                index=0,
                                validator_index=1,
                                address=0x1234,
                                amount=2,
                            )
                        )
                    ],
                },
                "version": "1",
                "validationError": "BlockException.INCORRECT_BLOCK_FORMAT"
                "|TransactionException.INTRINSIC_GAS_TOO_LOW",
                "expectedBlobVersionedHashes": [
                    "0x0000000000000000000000000000000000000000000000000000000000000000",
                    "0x0000000000000000000000000000000000000000000000000000000000000001",
                ],
                "errorCode": "-32600",
            },
            id="fixture_engine_new_payload_2",
        ),
    ],
)
class TestPydanticModelConversion:
    """
    Test that Pydantic models are converted to and from JSON correctly.
    """

    def test_json_serialization(
        self, can_be_deserialized: bool, model_instance: Any, json: str | Dict[str, Any]
    ):
        """
        Test that to_json returns the expected JSON for the given object.
        """
        assert to_json(model_instance) == json

    def test_json_deserialization(
        self, can_be_deserialized: bool, model_instance: Any, json: str | Dict[str, Any]
    ):
        """
        Test that to_json returns the expected JSON for the given object.
        """
        if not can_be_deserialized:
            pytest.skip(reason="The model instance in this case can not be deserialized")
        model_type = type(model_instance)
        assert model_type(**json) == model_instance
