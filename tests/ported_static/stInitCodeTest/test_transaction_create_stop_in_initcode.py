"""
Test_transaction_create_stop_in_initcode.

Ported from:
state_tests/stInitCodeTest/TransactionCreateStopInInitcodeFiller.json
@manually-enhanced: Do not overwrite. tx `gas_limit` bumped on Amsterdam
above intrinsic+state-gas; pre-EIP-8037 unchanged.

"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stInitCodeTest/TransactionCreateStopInInitcodeFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_before("EIP8368")
def test_transaction_create_stop_in_initcode(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Test_transaction_create_stop_in_initcode."""
    # EIP-8037 folds new-account state-gas into TX_CREATE intrinsic.
    tx_gas_limit = 55000
    sender_balance = 1000000
    if fork.is_eip_enabled(8037):
        tx_gas_limit = 300_000
        sender_balance = 10000000

    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=sender_balance)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    tx = Transaction(
        sender=sender,
        to=None,
        data=Op.PUSH1[0xA]
        + Op.CODECOPY(dest_offset=0x0, offset=0xC, size=Op.DUP1)
        + Op.PUSH1[0x0]
        + Op.STOP
        + Op.CALLCODE
        + Op.STOP * 2
        + Op.PUSH1[0x1]
        + Op.PUSH1[0x0]
        + Op.BYTE(Op.DUP2, Op.CALLDATALOAD(offset=Op.DUP1))
        + Op.DUP2,
        gas_limit=tx_gas_limit,
        value=1,
    )

    post = {
        compute_create_address(address=sender, nonce=0): Account(balance=1),
        sender: Account(nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
