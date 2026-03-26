"""
test_suicides_and_send_money_to_itself_ether_destroyed

Ported from:
state_tests/stTransactionTest/SuicidesAndSendMoneyToItselfEtherDestroyedFiller.json
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
    ["state_tests/stTransactionTest/SuicidesAndSendMoneyToItselfEtherDestroyedFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_suicides_and_send_money_to_itself_ether_destroyed(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_suicides_and_send_money_to_itself_ether_destroyed"""
    coinbase = Address("0xeb201d2887816e041f6e807e804f64f3a7a226fe")
    sender = EOA(
        key=0xd066c5db28bda8940cfc5cbefd1556cbc89c69b19f6d1aaa9fac69aee4b4a1bf
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

    pre[coinbase] = Account(balance=0, nonce=1)
    pre[sender] = Account(balance=0x7459280)
    # Source: lll
    # {(SELFDESTRUCT <contract:target:0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b>)}
    target = pre.deploy_contract(
        code=Op.SELFDESTRUCT(address=0xccbd97bed823989bf91c6ac4ceac020b2881f3a5)
        + Op.STOP,
        balance=1000,
        nonce=0,
        address=Address("0xccbd97bed823989bf91c6ac4ceac020b2881f3a5"),  # noqa: E501
    )


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=31700,
        value=10,
        nonce=0,
        gas_price=10,
    )

    post = {
        target: Account(
                code=bytes.fromhex("73ccbd97bed823989bf91c6ac4ceac020b2881f3a5ff00"),  # noqa: E501
                balance=1010,
                nonce=0,
            ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
