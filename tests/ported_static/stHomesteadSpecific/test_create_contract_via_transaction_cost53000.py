"""
trigger transaction creating gasPrice in the state

Ported from:
state_tests/stHomesteadSpecific/createContractViaTransactionCost53000Filler.json
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

REFERENCE_SPEC_GIT_PATH = "N/A"

REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stHomesteadSpecific/createContractViaTransactionCost53000Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_create_contract_via_transaction_cost53000(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """trigger transaction creating gasPrice in the state"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre[sender] = Account(balance=0xf4240)


    tx = Transaction(
        sender=sender,
        to=None,
        data=b'',
        gas_limit=100000,
        nonce=0,
        gas_price=10,
    )

    post = {sender: Account(nonce=1)}

    state_test(env=env, pre=pre, post=post, tx=tx)
