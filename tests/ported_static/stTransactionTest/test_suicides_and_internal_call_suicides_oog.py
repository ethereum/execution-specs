"""
test_suicides_and_internal_call_suicides_oog

Ported from:
state_tests/stTransactionTest/SuicidesAndInternalCallSuicidesOOGFiller.json
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
    ["state_tests/stTransactionTest/SuicidesAndInternalCallSuicidesOOGFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_suicides_and_internal_call_suicides_oog(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_suicides_and_internal_call_suicides_oog"""
    coinbase = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    sender = EOA(
        key=0xa2333eef5630066b928dea5fd85a239f511b5b067d1441ee7ac290d0122b917b
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
    addr_0x0000000000000000000000000000000000000000 = pre.deploy_contract(
        code=Op.SELFDESTRUCT(address=0x1) + Op.STOP,
        nonce=0,
        address=Address("0x5f0d8cd21c9026a32a4e8d15257b1801458989f3"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x5f5e100)
    # Source: lll
    # {(CALL 22000 <contract:0x0000000000000000000000000000000000000000> 1 0 0 0 0) (SELFDESTRUCT 0)}
    target = pre.deploy_contract(
        code=Op.POP(Op.CALL(gas=0x55f0, address=0x5f0d8cd21c9026a32a4e8d15257b1801458989f3, value=0x1, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.SELFDESTRUCT(address=0x0) + Op.STOP,
        balance=10,
        nonce=0,
        address=Address("0x78f15ba0abc5cc1aaa5a0ac6add5d28dd9ab8e1e"),  # noqa: E501
    )


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=50000,
        value=10,
        nonce=0,
        gas_price=10,
    )

    post = {
        addr_0x0000000000000000000000000000000000000000: Account(balance=0),
        sender: Account(nonce=1),
        target: Account(balance=10),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
