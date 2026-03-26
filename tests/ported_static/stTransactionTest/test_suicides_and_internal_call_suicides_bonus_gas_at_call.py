"""
test_suicides_and_internal_call_suicides_bonus_gas_at_call

Ported from:
state_tests/stTransactionTest/SuicidesAndInternalCallSuicidesBonusGasAtCallFiller.json
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
    ["state_tests/stTransactionTest/SuicidesAndInternalCallSuicidesBonusGasAtCallFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_suicides_and_internal_call_suicides_bonus_gas_at_call(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_suicides_and_internal_call_suicides_bonus_gas_at_call"""
    coinbase = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract_0 = Address("0x0000000000000000000000000000000000000000")
    contract_1 = Address("0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b")
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

    # Source: lll
    # {(SELFDESTRUCT 0x0000000000000000000000000000000000000001)}
    contract_0 = pre.deploy_contract(
        code=Op.SELFDESTRUCT(address=0x1) + Op.STOP,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000000000"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x5f5e100)
    # Source: lll
    # {(CALL 0 0x0000000000000000000000000000000000000000 1 0 0 0 0) (SELFDESTRUCT 0)}
    contract_1 = pre.deploy_contract(
        code=Op.POP(Op.CALL(gas=0x0, address=0x0, value=0x1, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.SELFDESTRUCT(address=0x0) + Op.STOP,
        balance=10,
        nonce=0,
        address=Address("0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b"),  # noqa: E501
    )


    tx = Transaction(
        sender=sender,
        to=contract_1,
        data=b'',
        gas_limit=50000,
        value=10,
        nonce=0,
        gas_price=10,
    )

    post = {
        Address("0x0000000000000000000000000000000000000001"): Account.NONEXISTENT,  # noqa: E501
        contract_1: Account(
                storage={},
                code=bytes.fromhex("6000600060006000600160006000f1506000ff00"),
                balance=0,
                nonce=0,
            ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
