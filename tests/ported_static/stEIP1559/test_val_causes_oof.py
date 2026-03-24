"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
tests/static/state_tests/stEIP1559/valCausesOOFFiller.yml
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
    ["tests/static/state_tests/stEIP1559/valCausesOOFFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, tx_gas_limit, tx_value, tx_error, expected_post",
    [
        pytest.param(
            "693c61390000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
            100000,
            0,
            None,
            {
                Address("0x71e12b76ab6be1efbc98ac17ebfe5faf488da45e"): Account(
                    storage={1: 24743}
                )
            },
            id="case0",
        ),
        pytest.param(
            "693c61390000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
            100000,
            1,
            TransactionException.INSUFFICIENT_ACCOUNT_FUNDS,
            {},
            id="case1",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            "693c61390000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
            90000,
            0,
            None,
            {
                Address("0x71e12b76ab6be1efbc98ac17ebfe5faf488da45e"): Account(
                    storage={1: 24743}
                )
            },
            id="case2",
        ),
        pytest.param(
            "693c61390000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
            90000,
            1,
            None,
            {
                Address("0x71e12b76ab6be1efbc98ac17ebfe5faf488da45e"): Account(
                    storage={1: 24743}
                )
            },
            id="case3",
        ),
        pytest.param(
            "693c61390000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
            110000,
            0,
            TransactionException.INSUFFICIENT_ACCOUNT_FUNDS,
            {},
            id="case4",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            "693c61390000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
            110000,
            1,
            TransactionException.INSUFFICIENT_ACCOUNT_FUNDS,
            {},
            id="case5",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            "693c61390000000000000000000000000000000000000000000000000000000000000002",  # noqa: E501
            100000,
            0,
            None,
            {
                Address("0x71e12b76ab6be1efbc98ac17ebfe5faf488da45e"): Account(
                    storage={1: 24743, 2: 24743}
                )
            },
            id="case6",
        ),
        pytest.param(
            "693c61390000000000000000000000000000000000000000000000000000000000000002",  # noqa: E501
            100000,
            1,
            TransactionException.INSUFFICIENT_ACCOUNT_FUNDS,
            {},
            id="case7",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            "693c61390000000000000000000000000000000000000000000000000000000000000002",  # noqa: E501
            90000,
            0,
            None,
            {
                Address("0x71e12b76ab6be1efbc98ac17ebfe5faf488da45e"): Account(
                    storage={1: 24743, 2: 24743}
                )
            },
            id="case8",
        ),
        pytest.param(
            "693c61390000000000000000000000000000000000000000000000000000000000000002",  # noqa: E501
            90000,
            1,
            None,
            {
                Address("0x71e12b76ab6be1efbc98ac17ebfe5faf488da45e"): Account(
                    storage={1: 24743, 2: 24743}
                )
            },
            id="case9",
        ),
        pytest.param(
            "693c61390000000000000000000000000000000000000000000000000000000000000002",  # noqa: E501
            110000,
            0,
            TransactionException.INSUFFICIENT_ACCOUNT_FUNDS,
            {},
            id="case10",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            "693c61390000000000000000000000000000000000000000000000000000000000000002",  # noqa: E501
            110000,
            1,
            TransactionException.INSUFFICIENT_ACCOUNT_FUNDS,
            {},
            id="case11",
            marks=pytest.mark.exception_test,
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_val_causes_oof(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    tx_gas_limit: int,
    tx_value: int,
    tx_error: object,
    expected_post: dict,
) -> None:
    """Ori Pomerantz qbzzt1@gmail.com."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x7608AB0A661408930040C5E3EB5B0C6520ACBB6CE5B28DDBE53676109E8EA24B
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=1000,
        gas_limit=71794957647893862,
    )

    pre[sender] = Account(balance=0x5F5E100, nonce=1)
    # Source: Yul
    # {
    #     // This loop runs a number of times specified in the data,
    #     // so the gas cost depends on the data
    #     for { let i := calldataload(4) } gt(i,0) { i := sub(i,1) } {
    #        sstore(i, 0x60A7)
    #     }     // for loop
    # }
    contract = pre.deploy_contract(
        code=(
            Op.CALLDATALOAD(offset=0x4)
            + Op.JUMPDEST
            + Op.JUMPI(pc=0xC, condition=Op.GT(Op.DUP2, 0x0))
            + Op.STOP
            + Op.JUMPDEST
            + Op.SSTORE(key=Op.DUP2, value=0x60A7)
            + Op.NOT(0x0)
            + Op.ADD
            + Op.JUMP(pc=0x3)
        ),
        balance=0x5AF3107A4000,
        nonce=0,
        address=Address("0x71e12b76ab6be1efbc98ac17ebfe5faf488da45e"),  # noqa: E501
    )

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=contract,
        data=tx_data,
        gas_limit=tx_gas_limit,
        max_fee_per_gas=1000,
        nonce=1,
        value=tx_value,
        error=tx_error,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
