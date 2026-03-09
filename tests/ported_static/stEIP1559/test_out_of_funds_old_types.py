"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
tests/static/state_tests/stEIP1559/outOfFundsOldTypesFiller.yml
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
    TransactionException,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["tests/static/state_tests/stEIP1559/outOfFundsOldTypesFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, tx_gas_limit, tx_value, tx_access_list, tx_error, expected_post",  # noqa: E501
    [
        pytest.param(
            "00",
            16777216,
            0,
            None,
            TransactionException.INSUFFICIENT_ACCOUNT_FUNDS,
            {},
            id="case0",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            "00",
            16777216,
            1000000000000000000,
            None,
            TransactionException.INSUFFICIENT_ACCOUNT_FUNDS,
            {},
            id="case1",
            marks=pytest.mark.exception_test,
        ),
        pytest.param("00", 40000, 0, None, None, {}, id="case2"),
        pytest.param(
            "00",
            40000,
            1000000000000000000,
            None,
            TransactionException.INSUFFICIENT_ACCOUNT_FUNDS,
            {},
            id="case3",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            "01",
            16777216,
            0,
            [],
            TransactionException.INSUFFICIENT_ACCOUNT_FUNDS,
            {},
            id="case4",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            "01",
            16777216,
            1000000000000000000,
            [],
            TransactionException.INSUFFICIENT_ACCOUNT_FUNDS,
            {},
            id="case5",
            marks=pytest.mark.exception_test,
        ),
        pytest.param("01", 40000, 0, [], None, {}, id="case6"),
        pytest.param(
            "01",
            40000,
            1000000000000000000,
            [],
            TransactionException.INSUFFICIENT_ACCOUNT_FUNDS,
            {},
            id="case7",
            marks=pytest.mark.exception_test,
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_out_of_funds_old_types(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    tx_gas_limit: int,
    tx_value: int,
    tx_access_list: list | None,
    tx_error: object,
    expected_post: dict,
) -> None:
    """Ori Pomerantz qbzzt1@gmail.com."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xDE0C95357363DA5C1C5A73BD7C2781CA5C9FECC1014103B5E1D1E990AE8208EC
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=1000,
        gas_limit=71794957647893862,
    )

    pre[sender] = Account(balance=0xDE0B6B3A7640000, nonce=1)
    # Source: Yul
    # {
    #     sstore(0, add(1,1))
    # }
    contract = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=0x2) + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0xd71b14c239fc39327f25764dd784c85ef0285fda"),  # noqa: E501
    )

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=contract,
        data=tx_data,
        gas_limit=tx_gas_limit,
        gas_price=100000000000,
        nonce=1,
        value=tx_value,
        access_list=tx_access_list,
        error=tx_error,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
