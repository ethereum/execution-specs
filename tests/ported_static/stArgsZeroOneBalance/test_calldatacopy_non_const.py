"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stArgsZeroOneBalance/calldatacopyNonConstFiller.yml
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
        "tests/static/state_tests/stArgsZeroOneBalance/calldatacopyNonConstFiller.yml",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, tx_value, expected_post",
    [
        ("", 0, {}),
        ("", 1, {}),
        ("11223344", 0, {}),
        ("11223344", 1, {}),
    ],
    ids=["case0", "case1", "case2", "case3"],
)
@pytest.mark.pre_alloc_mutable
def test_calldatacopy_non_const(
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

    pre[sender] = Account(balance=0xDE0B6B3A7640000)
    # Source: LLL
    # { (CALLDATACOPY (BALANCE <contract:target:0x095e7baea6a6c7c4c2dfeb977efac326af552d87>) (BALANCE <contract:target:0x095e7baea6a6c7c4c2dfeb977efac326af552d87>) (BALANCE <contract:target:0x095e7baea6a6c7c4c2dfeb977efac326af552d87>)) }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.CALLDATACOPY(
                dest_offset=Op.BALANCE(
                    address=0x444C2681920E1105C9104FB32249DDBB41CBA4A0,
                ),
                offset=Op.BALANCE(
                    address=0x444C2681920E1105C9104FB32249DDBB41CBA4A0,
                ),
                size=Op.BALANCE(
                    address=0x444C2681920E1105C9104FB32249DDBB41CBA4A0,
                ),
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x444c2681920e1105c9104fb32249ddbb41cba4a0"),  # noqa: E501
    )

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
