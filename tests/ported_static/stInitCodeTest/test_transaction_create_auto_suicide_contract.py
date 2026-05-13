"""
Test_transaction_create_auto_suicide_contract.

Ported from:
state_tests/stInitCodeTest/TransactionCreateAutoSuicideContractFiller.json
@manually-enhanced: Do not overwrite. tx `gas_limit` and sender balance
bumped on Amsterdam to cover EIP-8037 TX_CREATE intrinsic (new-account
state-gas folded in); pre-EIP-8037 unchanged.

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
from execution_testing.forks import Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stInitCodeTest/TransactionCreateAutoSuicideContractFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_transaction_create_auto_suicide_contract(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Test_transaction_create_auto_suicide_contract."""
    # EIP-8037 folds new-account state-gas into TX_CREATE intrinsic.
    tx_gas_limit = 55000
    sender_balance = 1000000
    if fork.is_eip_enabled(8037):
        tx_gas_limit = 300_000
        sender_balance = 10000000

    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre[sender] = Account(balance=sender_balance)

    tx = Transaction(
        sender=sender,
        to=None,
        data=Op.PUSH1[0xA]
        + Op.CODECOPY(dest_offset=0x0, offset=0xC, size=Op.DUP1)
        + Op.SELFDESTRUCT(address=0x0)
        + Op.SELFDESTRUCT(address=Op.CALLCODE)
        + Op.SELFDESTRUCT
        + Op.PUSH1[0x1]
        + Op.PUSH1[0x0]
        + Op.BYTE(Op.DUP2, Op.CALLDATALOAD(offset=Op.DUP1))
        + Op.DUP2,
        gas_limit=tx_gas_limit,
        value=15,
    )

    post = {
        Address(
            0x0000000000000000000000000000000000000000
        ): Account.NONEXISTENT,
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
