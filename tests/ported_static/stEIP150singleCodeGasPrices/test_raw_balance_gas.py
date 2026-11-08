"""
Test_raw_balance_gas.

Ported from:
state_tests/stEIP150singleCodeGasPrices/RawBalanceGasFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytes,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stEIP150singleCodeGasPrices/RawBalanceGasFiller.json"],
)
@pytest.mark.valid_from("Cancun")
def test_raw_balance_gas(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_raw_balance_gas."""
    sender = pre.fund_eoa(amount=0xE8D4A51000)

    # Source: lll
    # { [0] (GAS) (BALANCE <eoa:sender:0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b>) [[1]] (SUB @0 (GAS)) }  # noqa: E501
    target = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.POP(Op.BALANCE(address=sender))
        + Op.SSTORE(key=0x1, value=Op.SUB(Op.MLOAD(offset=0x0), Op.GAS))
        + Op.STOP,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=600000,
    )

    post = {target: Account(storage={1: 116})}

    state_test(pre=pre, post=post, tx=tx)
