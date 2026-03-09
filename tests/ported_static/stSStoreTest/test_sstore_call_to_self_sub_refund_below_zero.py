"""
Test where accnt has slot 1 value of '2', is cleared, then calls itself and...

Ported from:
tests/static/state_tests/stSStoreTest
SstoreCallToSelfSubRefundBelowZeroFiller.json
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
        "tests/static/state_tests/stSStoreTest/SstoreCallToSelfSubRefundBelowZeroFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_sstore_call_to_self_sub_refund_below_zero(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test where accnt has slot 1 value of '2', is cleared, then calls..."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xAF50993BA9FD52F2A61FCD1DC6D59A44E7AF39F4289201CC19EA7D30E8E27E83
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=68719476736,
    )

    pre[sender] = Account(balance=0xFFFFFFFFFFFFFFFF)
    # Source: raw bytecode
    contract = pre.deploy_contract(
        code=(
            Op.JUMPI(pc=0x15, condition=Op.EQ(Op.ADDRESS, Op.CALLER))
            + Op.SSTORE(key=0x1, value=0x0)
            + Op.CALL(
                gas=Op.GAS,
                address=Op.ADDRESS,
                value=Op.DUP1,
                args_offset=Op.DUP1,
                args_size=Op.DUP1,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
            + Op.STOP
            + Op.JUMPDEST
            + Op.SSTORE(key=0x1, value=0x3)
            + Op.STOP
        ),
        storage={0x1: 0x2},
        nonce=0,
        address=Address("0xb48023055b6c3d565a6f5488459d64efab79b6c7"),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=2367154,
    )

    post = {
        contract: Account(storage={1: 3}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
