"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stEIP150singleCodeGasPrices/RawBalanceGasFiller.json
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
        "tests/static/state_tests/stEIP150singleCodeGasPrices/RawBalanceGasFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_raw_balance_gas(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x4F31B3206FBF0E0E598B9B1A7D8AC86302A0FF1D8930738F1BEBAE9B67173E52
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    # Source: LLL
    # { [0] (GAS) (BALANCE <eoa:sender:0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b>) [[1]] (SUB @0 (GAS)) }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=Op.GAS)
            + Op.POP(
                Op.BALANCE(address=0xFAA10B404AB607779993C016CD5DA73AE1F29D7E),
            )
            + Op.SSTORE(key=0x1, value=Op.SUB(Op.MLOAD(offset=0x0), Op.GAS))
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xdfde2d07c7829a62d244d6b9791742b2921af7c0"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xE8D4A51000)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=600000,
    )

    post = {
        contract: Account(storage={1: 116}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
