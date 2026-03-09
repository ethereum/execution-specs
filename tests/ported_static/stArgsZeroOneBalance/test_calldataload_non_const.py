"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stArgsZeroOneBalance/calldataloadNonConstFiller.yml
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
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stArgsZeroOneBalance/calldataloadNonConstFiller.yml",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, tx_value, expected_post",
    [
        ("", 0, {}),
        ("", 1, {}),
        (
            "11223344",
            0,
            {
                Address("0x148f97630d3668441f1a33a5e509f268b64f998f"): Account(
                    storage={
                        0: 0x1122334400000000000000000000000000000000000000000000000000000000  # noqa: E501
                    }
                )
            },
        ),
        (
            "11223344",
            1,
            {
                Address("0x148f97630d3668441f1a33a5e509f268b64f998f"): Account(
                    storage={
                        0: 0x2233440000000000000000000000000000000000000000000000000000000000  # noqa: E501
                    }
                )
            },
        ),
    ],
    ids=["case0", "case1", "case2", "case3"],
)
@pytest.mark.pre_alloc_mutable
def test_calldataload_non_const(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    tx_value: int,
    expected_post: dict,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xB1F4CBC3A50042184425A6F9E996D0910F7BA879457CE5DAC5C71E498AD3C005
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    # Source: LLL
    # { [[ 0 ]](CALLDATALOAD (BALANCE <contract:target:0x095e7baea6a6c7c4c2dfeb977efac326af552d87>)) }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.CALLDATALOAD(
                    offset=Op.BALANCE(
                        address=0x148F97630D3668441F1A33A5E509F268B64F998F,
                    ),
                ),
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x148f97630d3668441f1a33a5e509f268b64f998f"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=contract,
        data=tx_data,
        gas_limit=400000,
        value=tx_value,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
