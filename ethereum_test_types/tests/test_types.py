"""
Test suite for `ethereum_test` module.
"""

from typing import Any, Dict, List

import pytest
from pydantic import TypeAdapter

from ethereum_test_base_types import Address, TestAddress, TestAddress2, TestPrivateKey, to_json
from ethereum_test_base_types.pydantic import CopyValidateModel
from ethereum_test_vm import Opcodes as Op

from ..eof.v1 import Container
from ..types import (
    AccessList,
    Account,
    Alloc,
    DepositRequest,
    Environment,
    Requests,
    Storage,
    Transaction,
    Withdrawal,
)


def test_storage():
    """
    Test `ethereum_test.types.storage` parsing.
    """
    s = Storage({"10": "0x10"})

    assert 10 in s
    assert s[10] == 16

    s = Storage({"10": "10"})

    assert 10 in s
    assert s[10] == 10

    s = Storage({10: 10})

    assert 10 in s
    assert s[10] == 10

    iter_s = iter(Storage({10: 20, "11": "21"}))
    assert next(iter_s) == 10
    assert next(iter_s) == 11

    s["10"] = "0x10"
    s["0x10"] = "10"
    assert s[10] == 16
    assert s[16] == 10

    assert "10" in s
    assert "0xa" in s
    assert 10 in s

    del s[10]
    assert "10" not in s
    assert "0xa" not in s
    assert 10 not in s

    s = Storage({-1: -1, -2: -2})
    assert s[-1] == 2**256 - 1
    assert s[-2] == 2**256 - 2
    d = to_json(s)
    assert (
        d["0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"]
        == "0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
    )
    assert (
        d["0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe"]
        == "0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe"
    )
    # Try to add a duplicate key (negative and positive number at the same
    # time)
    # same value, ok
    s[2**256 - 1] = 2**256 - 1
    to_json(s)

    # Check store counter
    s = Storage({})
    s.store_next(0x100)
    s.store_next("0x200")
    s.store_next(b"\x03\x00".rjust(32, b"\x00"))
    d = to_json(s)
    assert d == {
        "0x00": ("0x0100"),
        "0x01": ("0x0200"),
        "0x02": ("0x0300"),
    }


@pytest.mark.parametrize(
    ["account"],
    [
        pytest.param(
            Account(),
            id="no_fields",
        ),
        pytest.param(
            Account(
                nonce=0,
            ),
            id="zero_nonce",
        ),
        pytest.param(
            Account(
                balance=0,
            ),
            id="zero_balance",
        ),
        pytest.param(
            Account(
                code="",
            ),
            id="empty_code",
        ),
        pytest.param(
            Account(
                storage={},
            ),
            id="empty_storage",
        ),
        pytest.param(
            Account(
                nonce=0,
                balance=0,
                code="",
                storage={
                    1: 0,
                },
            ),
            id="only_zero_storage_values",
        ),
    ],
)
def test_empty_accounts(account: Account):
    """
    Test `ethereum_test.types.account` parsing.
    """
    assert not bool(account)


@pytest.mark.parametrize(
    ["account", "alloc_dict", "should_pass"],
    [
        # All None: Pass
        (
            Account(),
            {"nonce": "1", "code": "0x123", "balance": "1", "storage": {0: 1}},
            True,
        ),
        # Storage must be empty: Fail
        (
            Account(storage={}),
            {"nonce": "1", "code": "0x123", "balance": "1", "storage": {0: 1}},
            False,
        ),
        # Storage must be empty: Pass
        (
            Account(storage={}),
            {"nonce": "1", "code": "0x123", "balance": "1", "storage": {}},
            True,
        ),
        # Storage must be empty: Pass
        (
            Account(storage={}),
            {
                "nonce": "1",
                "code": "0x123",
                "balance": "1",
                "storage": {0: 0, 1: 0},
            },
            True,
        ),
        # Storage must be empty: Pass
        (
            Account(storage={0: 0}),
            {
                "nonce": "1",
                "code": "0x123",
                "balance": "1",
                "storage": {},
            },
            True,
        ),
        # Storage must not be empty: Pass
        (
            Account(storage={1: 1}),
            {
                "nonce": "1",
                "code": "0x123",
                "balance": "1",
                "storage": {0: 0, 1: 1},
            },
            True,
        ),
        # Storage must not be empty: Fail
        (
            Account(storage={1: 1}),
            {
                "nonce": "1",
                "code": "0x123",
                "balance": "1",
                "storage": {0: 0, 1: 1, 2: 2},
            },
            False,
        ),
        # Code must be empty: Fail
        (
            Account(code=""),
            {
                "nonce": "0",
                "code": "0x123",
                "balance": "0",
                "storage": {},
            },
            False,
        ),
        # Code must be empty: Pass
        (
            Account(code=""),
            {
                "nonce": "1",
                "code": "0x",
                "balance": "1",
                "storage": {0: 0, 1: 1},
            },
            True,
        ),
        # Nonce must be empty: Fail
        (
            Account(nonce=0),
            {
                "nonce": "1",
                "code": "0x",
                "balance": "0",
                "storage": {},
            },
            False,
        ),
        # Nonce must be empty: Pass
        (
            Account(nonce=0),
            {
                "nonce": "0",
                "code": "0x1234",
                "balance": "1",
                "storage": {0: 0, 1: 1},
            },
            True,
        ),
        # Nonce must not be empty: Fail
        (
            Account(nonce=1),
            {
                "code": "0x1234",
                "balance": "1",
                "storage": {0: 0, 1: 1},
            },
            False,
        ),
        # Nonce must not be empty: Pass
        (
            Account(nonce=1),
            {
                "nonce": "1",
                "code": "0x",
                "balance": "0",
                "storage": {},
            },
            True,
        ),
        # Balance must be empty: Fail
        (
            Account(balance=0),
            {
                "nonce": "0",
                "code": "0x",
                "balance": "1",
                "storage": {},
            },
            False,
        ),
        # Balance must be empty: Pass
        (
            Account(balance=0),
            {
                "nonce": "1",
                "code": "0x1234",
                "balance": "0",
                "storage": {0: 0, 1: 1},
            },
            True,
        ),
        # Balance must not be empty: Fail
        (
            Account(balance=1),
            {
                "nonce": "1",
                "code": "0x1234",
                "storage": {0: 0, 1: 1},
            },
            False,
        ),
        # Balance must not be empty: Pass
        (
            Account(balance=1),
            {
                "nonce": "0",
                "code": "0x",
                "balance": "1",
                "storage": {},
            },
            True,
        ),
    ],
)
def test_account_check_alloc(account: Account, alloc_dict: Dict[Any, Any], should_pass: bool):
    """
    Test `Account.check_alloc` method.
    """
    alloc_account = Account(**alloc_dict)
    if should_pass:
        account.check_alloc(Address(1), alloc_account)
    else:
        with pytest.raises(Exception) as _:
            account.check_alloc(Address(1), alloc_account)


@pytest.mark.parametrize(
    ["alloc_1", "alloc_2", "expected_alloc"],
    [
        pytest.param(
            Alloc(),
            Alloc(),
            Alloc(),
            id="empty_alloc",
        ),
        pytest.param(
            Alloc({0x1: {"nonce": 1}}),  # type: ignore
            Alloc({0x2: {"nonce": 2}}),  # type: ignore
            Alloc({0x1: Account(nonce=1), 0x2: Account(nonce=2)}),  # type: ignore
            id="alloc_different_accounts",
        ),
        pytest.param(
            Alloc({0x2: {"nonce": 1}}),  # type: ignore
            Alloc({"0x02": {"nonce": 2}}),  # type: ignore
            Alloc({0x2: Account(nonce=2)}),  # type: ignore
            id="overwrite_account",
        ),
        pytest.param(
            Alloc({0x2: {"balance": 1}}),  # type: ignore
            Alloc({"0x02": {"nonce": 1}}),  # type: ignore
            Alloc({0x2: Account(balance=1, nonce=1)}),  # type: ignore
            id="mix_account",
        ),
    ],
)
def test_alloc_append(alloc_1: Alloc, alloc_2: Alloc, expected_alloc: Alloc):
    """
    Test `ethereum_test.types.alloc` merging.
    """
    assert Alloc.merge(alloc_1, alloc_2) == expected_alloc


def test_alloc_deploy_contract():
    """
    Test `Alloc.deploy_contract` functionallity.
    """
    alloc = Alloc()
    contract_1 = alloc.deploy_contract(Op.SSTORE(0, 1) + Op.STOP)
    contract_2 = alloc.deploy_contract(Op.SSTORE(0, 2) + Op.STOP)
    assert contract_1 != contract_2
    assert contract_1 in alloc
    assert contract_2 in alloc
    assert alloc[contract_1].code == bytes.fromhex("600160005500")
    assert alloc[contract_2].code == bytes.fromhex("600260005500")


def test_alloc_fund_sender():
    """
    Test `Alloc.fund_eoa` functionallity.
    """
    alloc = Alloc()
    sender_1 = alloc.fund_eoa(10**18)
    sender_2 = alloc.fund_eoa(10**18)
    assert sender_1 != sender_2
    assert sender_1 in alloc
    assert sender_2 in alloc
    assert Address(sender_1) == TestAddress
    assert Address(sender_2) == TestAddress2
    assert alloc[sender_1].balance == 10**18
    assert alloc[sender_2].balance == 10**18


@pytest.mark.parametrize(
    ["account_1", "account_2", "expected_account"],
    [
        pytest.param(
            Account(),
            Account(),
            Account(),
            id="empty_accounts",
        ),
        pytest.param(
            None,
            None,
            Account(),
            id="none_accounts",
        ),
        pytest.param(
            Account(nonce=1),
            Account(code="0x6000"),
            Account(nonce=1, code="0x6000"),
            id="accounts_with_different_fields",
        ),
        pytest.param(
            Account(nonce=1),
            Account(nonce=2),
            Account(nonce=2),
            id="accounts_with_different_nonce",
        ),
    ],
)
def test_account_merge(
    account_1: Account | None, account_2: Account | None, expected_account: Account
):
    """
    Test `ethereum_test.types.account` merging.
    """
    assert Account.merge(account_1, account_2) == expected_account


CHECKSUM_ADDRESS = "0x8a0A19589531694250d570040a0c4B74576919B8"


@pytest.mark.parametrize(
    ["can_be_deserialized", "model_instance", "json"],
    [
        pytest.param(
            True,
            Address(CHECKSUM_ADDRESS),
            CHECKSUM_ADDRESS,
            marks=pytest.mark.xfail,
            id="address_with_checksum_address",
        ),
        pytest.param(
            True,
            Account(),
            {
                "nonce": "0x00",
                "balance": "0x00",
                "code": "0x",
                "storage": {},
            },
            id="account_1",
        ),
        pytest.param(
            True,
            Account(
                nonce=1,
                balance=2,
                code="0x1234",
                storage={
                    0: 0,
                    1: 1,
                },
            ),
            {
                "nonce": "0x01",
                "balance": "0x02",
                "code": "0x1234",
                "storage": {
                    "0x00": "0x00",
                    "0x01": "0x01",
                },
            },
            id="account_2",
        ),
        pytest.param(
            True,
            AccessList(
                address=0x1234,
                storage_keys=[0, 1],
            ),
            {
                "address": "0x0000000000000000000000000000000000001234",
                "storageKeys": [
                    "0x0000000000000000000000000000000000000000000000000000000000000000",
                    "0x0000000000000000000000000000000000000000000000000000000000000001",
                ],
            },
            id="access_list",
        ),
        pytest.param(
            True,
            Withdrawal(index=0, validator_index=1, address=0x1234, amount=2),
            {
                "index": "0x0",
                "validatorIndex": "0x1",
                "address": "0x0000000000000000000000000000000000001234",
                "amount": "0x2",
            },
            id="withdrawal",
        ),
        pytest.param(
            True,
            Environment(),
            {
                "currentCoinbase": "0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba",
                "currentGasLimit": "100000000000000000",
                "currentNumber": "1",
                "currentTimestamp": "1000",
                "blockHashes": {},
                "ommers": [],
                "parentUncleHash": (
                    "0x0000000000000000000000000000000000000000000000000000000000000000"
                ),
            },
            id="environment_1",
        ),
        pytest.param(
            True,
            Environment(
                fee_recipient=0x1234,
                difficulty=0x5,
                prev_randao=0x6,
                base_fee_per_gas=0x7,
                parent_difficulty=0x8,
                parent_timestamp=0x9,
                parent_base_fee_per_gas=0xA,
                parent_gas_used=0xB,
                parent_gas_limit=0xC,
                parent_ommers_hash=0xD,
                withdrawals=[Withdrawal(index=0, validator_index=1, address=0x1234, amount=2)],
                parent_blob_gas_used=0xE,
                parent_excess_blob_gas=0xF,
                blob_gas_used=0x10,
                excess_blob_gas=0x11,
                block_hashes={1: 2, 3: 4},
            ),
            {
                "currentCoinbase": "0x0000000000000000000000000000000000001234",
                "currentGasLimit": "100000000000000000",
                "currentNumber": "1",
                "currentTimestamp": "1000",
                "currentDifficulty": "5",
                "currentRandom": "6",
                "currentBaseFee": "7",
                "parentDifficulty": "8",
                "parentTimestamp": "9",
                "parentBaseFee": "10",
                "parentGasUsed": "11",
                "parentGasLimit": "12",
                "parentUncleHash": (
                    "0x000000000000000000000000000000000000000000000000000000000000000d"
                ),
                "withdrawals": [
                    {
                        "index": "0x0",
                        "validatorIndex": "0x1",
                        "address": "0x0000000000000000000000000000000000001234",
                        "amount": "0x2",
                    },
                ],
                "parentBlobGasUsed": "14",
                "parentExcessBlobGas": "15",
                "currentBlobGasUsed": "16",
                "currentExcessBlobGas": "17",
                "blockHashes": {
                    "1": "0x0000000000000000000000000000000000000000000000000000000000000002",
                    "3": "0x0000000000000000000000000000000000000000000000000000000000000004",
                },
                "parentHash": "0x0000000000000000000000000000000000000000000000000000000000000004",
                "ommers": [],
            },
            id="environment_2",
        ),
        pytest.param(
            True,
            Transaction().with_signature_and_sender(),
            {
                "type": "0x0",
                "chainId": "0x1",
                "nonce": "0x0",
                "to": "0x00000000000000000000000000000000000000aa",
                "value": "0x0",
                "input": "0x",
                "gas": "0x5208",
                "gasPrice": "0xa",
                "v": "0x26",
                "r": "0xcc61d852649c34cc0b71803115f38036ace257d2914f087bf885e6806a664fbd",
                "s": "0x2020cb35f5d7731ab540d62614503a7f2344301a86342f67daf011c1341551ff",
                "sender": "0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b",
            },
            id="transaction_t8n_default_args",
        ),
        pytest.param(
            True,
            Transaction(
                to=None,
            ).with_signature_and_sender(),
            {
                "type": "0x0",
                "chainId": "0x1",
                "nonce": "0x0",
                "to": None,
                "value": "0x0",
                "input": "0x",
                "gas": "0x5208",
                "gasPrice": "0xa",
                "v": "0x25",
                "r": "0x1cfe2cbb0c3577f74d9ae192a7f1ee2d670fe806a040f427af9cb768be3d07ce",
                "s": "0xcbe2d029f52dbf93ade486625bed0603945d2c7358b31de99fe8786c00f13da",
                "sender": "0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b",
            },
            id="transaction_t8n_to_none",
        ),
        pytest.param(
            True,
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
            {
                "type": "0x3",
                "chainId": "0x1",
                "nonce": "0x0",
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
                "value": "0x0",
                "input": "0x0100",
                "gas": "0x5208",
                "maxPriorityFeePerGas": "0xa",
                "maxFeePerGas": "0x14",
                "maxFeePerBlobGas": "0x1e",
                "blobVersionedHashes": [
                    "0x0000000000000000000000000000000000000000000000000000000000000000",
                    "0x0000000000000000000000000000000000000000000000000000000000000001",
                ],
                "v": "0x0",
                "r": "0x418bb557c43262375f80556cb09dac5e67396acf0eaaf2c2540523d1ce54b280",
                "s": "0x4fa36090ea68a1138043d943ced123c0b0807d82ff3342a6977cbc09230e927c",
                "sender": "0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b",
            },
            id="transaction_3",
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


@pytest.mark.parametrize(
    ["invalid_tx_args", "expected_exception", "expected_exception_substring"],
    [
        pytest.param(
            {"gas_price": 1, "max_fee_per_gas": 2},
            Transaction.InvalidFeePayment,
            "only one type of fee payment field can be used",
            id="gas-price-and-max-fee-per-gas",
        ),
        pytest.param(
            {"gas_price": 1, "max_priority_fee_per_gas": 2},
            Transaction.InvalidFeePayment,
            "only one type of fee payment field can be used",
            id="gas-price-and-max-priority-fee-per-gas",
        ),
        pytest.param(
            {"gas_price": 1, "max_fee_per_blob_gas": 2},
            Transaction.InvalidFeePayment,
            "only one type of fee payment field can be used",
            id="gas-price-and-max-fee-per-blob-gas",
        ),
        pytest.param(
            {"ty": 0, "v": 1, "secret_key": 2},
            Transaction.InvalidSignaturePrivateKey,
            "can't define both 'signature' and 'private_key'",
            id="type0-signature-and-secret-key",
        ),
    ],
)
def test_transaction_post_init_invalid_arg_combinations(  # noqa: D103
    invalid_tx_args, expected_exception, expected_exception_substring
):
    """
    Test that Transaction.__post_init__ raises the expected exceptions for
    invalid constructor argument combinations.
    """
    with pytest.raises(expected_exception) as exc_info:
        Transaction(**invalid_tx_args)
    assert expected_exception_substring in str(exc_info.value)


@pytest.mark.parametrize(
    ["tx_args", "expected_attributes_and_values"],
    [
        pytest.param(
            {"max_fee_per_blob_gas": 10},
            [
                ("ty", 3),
            ],
            id="max_fee_per_blob_gas-adds-ty-3",
        ),
        pytest.param(
            {},
            [
                ("gas_price", 10),
            ],
            id="no-fees-adds-gas_price",
        ),
        pytest.param(
            {},
            [
                ("secret_key", TestPrivateKey),
            ],
            id="no-signature-adds-secret_key",
        ),
        pytest.param(
            {"max_fee_per_gas": 10},
            [
                ("ty", 2),
            ],
            id="max_fee_per_gas-adds-ty-2",
        ),
        pytest.param(
            {"access_list": [AccessList(address=0x1234, storage_keys=[0, 1])]},
            [
                ("ty", 1),
            ],
            id="access_list-adds-ty-1",
        ),
        pytest.param(
            {"ty": 1},
            [
                ("access_list", []),
            ],
            id="ty-1-adds-empty-access_list",
        ),
        pytest.param(
            {"ty": 2},
            [
                ("max_priority_fee_per_gas", 0),
            ],
            id="ty-2-adds-max_priority_fee_per_gas",
        ),
    ],
)
def test_transaction_post_init_defaults(tx_args, expected_attributes_and_values):
    """
    Test that Transaction.__post_init__ sets the expected default values for
    missing fields.
    """
    tx = Transaction(**tx_args)
    for attr, val in expected_attributes_and_values:
        assert hasattr(tx, attr)
        assert getattr(tx, attr) == val


@pytest.mark.parametrize(
    ["withdrawals", "expected_root"],
    [
        pytest.param(
            [],
            bytes.fromhex("56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421"),
            id="empty-withdrawals",
        ),
        pytest.param(
            [
                Withdrawal(
                    index=0,
                    validator_index=1,
                    address=0x1234,
                    amount=2,
                )
            ],
            bytes.fromhex("dc3ead883fc17ea3802cd0f8e362566b07b223f82e52f94c76cf420444b8ff81"),
            id="single-withdrawal",
        ),
        pytest.param(
            [
                Withdrawal(
                    index=0,
                    validator_index=1,
                    address=0x1234,
                    amount=2,
                ),
                Withdrawal(
                    index=1,
                    validator_index=2,
                    address=0xABCD,
                    amount=0,
                ),
            ],
            bytes.fromhex("069ab71e5d228db9b916880f02670c85682c46641bb9c95df84acc5075669e01"),
            id="multiple-withdrawals",
        ),
        pytest.param(
            [
                Withdrawal(
                    index=0,
                    validator_index=0,
                    address=0x100,
                    amount=0,
                ),
                Withdrawal(
                    index=0,
                    validator_index=0,
                    address=0x200,
                    amount=0,
                ),
            ],
            bytes.fromhex("daacd8fe889693f7d20436d9c0c044b5e92cc17b57e379997273fc67fd2eb7b8"),
            id="multiple-withdrawals",
        ),
    ],
)
def test_withdrawals_root(withdrawals: List[Withdrawal], expected_root: bytes):
    """
    Test that withdrawals_root returns the expected hash.
    """
    assert Withdrawal.list_root(withdrawals) == expected_root


@pytest.mark.parametrize(
    ["json_str", "type_adapter", "expected"],
    [
        pytest.param(
            """
            [
                {
                    "type": "0x0",
                    "pubkey": "0x000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001",
                    "withdrawalCredentials": "0x0000000000000000000000000000000000000000000000000000000000000002",
                    "amount": "0x1234",
                    "signature": "0x000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000003",
                    "index": "0x5678"
                }
            ]
            """,  # noqa: E501
            TypeAdapter(Requests),
            Requests(
                root=[
                    DepositRequest(
                        pubkey=1,
                        withdrawal_credentials=2,
                        amount=0x1234,
                        signature=3,
                        index=0x5678,
                    ),
                ]
            ),
            id="requests_1",
        ),
    ],
)
def test_parsing(json_str: str, type_adapter: TypeAdapter, expected: Any):
    """
    Test that parsing the given JSON string returns the expected object.
    """
    assert type_adapter.validate_json(json_str) == expected


@pytest.mark.parametrize(
    "model",
    [
        Environment(),
        Container(),
    ],
    ids=lambda model: model.__class__.__name__,
)
def test_model_copy(model: CopyValidateModel):
    """
    Test that the copy method returns a correct copy of the model.
    """
    assert to_json(model.copy()) == to_json(model)
    assert model.copy().model_fields_set == model.model_fields_set
