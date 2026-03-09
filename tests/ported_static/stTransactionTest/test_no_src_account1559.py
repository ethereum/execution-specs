"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stTransactionTest/NoSrcAccount1559Filler.yml
"""

import pytest
from execution_testing import (
    EOA,
    AccessList,
    Address,
    Alloc,
    Environment,
    Hash,
    StateTestFiller,
    Transaction,
    TransactionException,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["tests/static/state_tests/stTransactionTest/NoSrcAccount1559Filler.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit, tx_value, tx_access_list, tx_error",
    [
        pytest.param(
            21000,
            0,
            [],
            [
                TransactionException.INSUFFICIENT_ACCOUNT_FUNDS,
                TransactionException.INTRINSIC_GAS_TOO_LOW,
            ],
            id="case0",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            21000,
            1,
            [],
            [
                TransactionException.INSUFFICIENT_ACCOUNT_FUNDS,
                TransactionException.INTRINSIC_GAS_TOO_LOW,
            ],
            id="case1",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            210000,
            0,
            [],
            TransactionException.INSUFFICIENT_ACCOUNT_FUNDS,
            id="case2",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            210000,
            1,
            [],
            TransactionException.INSUFFICIENT_ACCOUNT_FUNDS,
            id="case3",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            0,
            0,
            [],
            TransactionException.INTRINSIC_GAS_TOO_LOW,
            id="case4",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            0,
            1,
            [],
            [
                TransactionException.INSUFFICIENT_ACCOUNT_FUNDS,
                TransactionException.INTRINSIC_GAS_TOO_LOW,
            ],
            id="case5",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            21000,
            0,
            [
                AccessList(
                    address=Address(
                        "0x4d7b154e5bf8310a4d8220c8eed80020e4b8f86f"
                    ),
                    storage_keys=[],
                )
            ],
            [
                TransactionException.INSUFFICIENT_ACCOUNT_FUNDS,
                TransactionException.INTRINSIC_GAS_TOO_LOW,
            ],
            id="case6",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            21000,
            1,
            [
                AccessList(
                    address=Address(
                        "0x4d7b154e5bf8310a4d8220c8eed80020e4b8f86f"
                    ),
                    storage_keys=[],
                )
            ],
            [
                TransactionException.INSUFFICIENT_ACCOUNT_FUNDS,
                TransactionException.INTRINSIC_GAS_TOO_LOW,
            ],
            id="case7",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            210000,
            0,
            [
                AccessList(
                    address=Address(
                        "0x4d7b154e5bf8310a4d8220c8eed80020e4b8f86f"
                    ),
                    storage_keys=[],
                )
            ],
            TransactionException.INSUFFICIENT_ACCOUNT_FUNDS,
            id="case8",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            210000,
            1,
            [
                AccessList(
                    address=Address(
                        "0x4d7b154e5bf8310a4d8220c8eed80020e4b8f86f"
                    ),
                    storage_keys=[],
                )
            ],
            TransactionException.INSUFFICIENT_ACCOUNT_FUNDS,
            id="case9",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            0,
            0,
            [
                AccessList(
                    address=Address(
                        "0x4d7b154e5bf8310a4d8220c8eed80020e4b8f86f"
                    ),
                    storage_keys=[],
                )
            ],
            TransactionException.INTRINSIC_GAS_TOO_LOW,
            id="case10",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            0,
            1,
            [
                AccessList(
                    address=Address(
                        "0x4d7b154e5bf8310a4d8220c8eed80020e4b8f86f"
                    ),
                    storage_keys=[],
                )
            ],
            [
                TransactionException.INSUFFICIENT_ACCOUNT_FUNDS,
                TransactionException.INTRINSIC_GAS_TOO_LOW,
            ],
            id="case11",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            21000,
            0,
            [
                AccessList(
                    address=Address(
                        "0x4d7b154e5bf8310a4d8220c8eed80020e4b8f86f"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000001"  # noqa: E501
                        ),
                    ],
                )
            ],
            [
                TransactionException.INSUFFICIENT_ACCOUNT_FUNDS,
                TransactionException.INTRINSIC_GAS_TOO_LOW,
            ],
            id="case12",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            21000,
            1,
            [
                AccessList(
                    address=Address(
                        "0x4d7b154e5bf8310a4d8220c8eed80020e4b8f86f"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000001"  # noqa: E501
                        ),
                    ],
                )
            ],
            [
                TransactionException.INSUFFICIENT_ACCOUNT_FUNDS,
                TransactionException.INTRINSIC_GAS_TOO_LOW,
            ],
            id="case13",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            210000,
            0,
            [
                AccessList(
                    address=Address(
                        "0x4d7b154e5bf8310a4d8220c8eed80020e4b8f86f"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000001"  # noqa: E501
                        ),
                    ],
                )
            ],
            TransactionException.INSUFFICIENT_ACCOUNT_FUNDS,
            id="case14",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            210000,
            1,
            [
                AccessList(
                    address=Address(
                        "0x4d7b154e5bf8310a4d8220c8eed80020e4b8f86f"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000001"  # noqa: E501
                        ),
                    ],
                )
            ],
            TransactionException.INSUFFICIENT_ACCOUNT_FUNDS,
            id="case15",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            0,
            0,
            [
                AccessList(
                    address=Address(
                        "0x4d7b154e5bf8310a4d8220c8eed80020e4b8f86f"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000001"  # noqa: E501
                        ),
                    ],
                )
            ],
            TransactionException.INTRINSIC_GAS_TOO_LOW,
            id="case16",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            0,
            1,
            [
                AccessList(
                    address=Address(
                        "0x4d7b154e5bf8310a4d8220c8eed80020e4b8f86f"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000001"  # noqa: E501
                        ),
                    ],
                )
            ],
            [
                TransactionException.INSUFFICIENT_ACCOUNT_FUNDS,
                TransactionException.INTRINSIC_GAS_TOO_LOW,
            ],
            id="case17",
            marks=pytest.mark.exception_test,
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_no_src_account1559(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
    tx_value: int,
    tx_access_list: list | None,
    tx_error: object,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x4A2FFC8867FD8D1773481CF13F36E44F033133C579520D2745E46C3BBBF21E6A
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=89128960,
    )

    # Source: raw bytecode
    contract = pre.deploy_contract(
        code=bytes.fromhex("00"),
        nonce=0,
        address=Address("0x4d7b154e5bf8310a4d8220c8eed80020e4b8f86f"),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex("00"),
        gas_limit=tx_gas_limit,
        max_fee_per_gas=2000,
        max_priority_fee_per_gas=10,
        value=tx_value,
        access_list=tx_access_list,
        error=tx_error,
    )

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
