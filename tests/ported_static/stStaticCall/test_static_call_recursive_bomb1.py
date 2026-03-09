"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stStaticCall/static_CallRecursiveBomb1Filler.json
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
        "tests/static/state_tests/stStaticCall/static_CallRecursiveBomb1Filler.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.pre_alloc_mutable
@pytest.mark.slow
def test_static_call_recursive_bomb1(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xE04D1AC7DDDA0C98397D56A0B501E960D4CD325A39286919AC23C1A07009A869
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    # Source: LLL
    # {  (CALLCODE (GAS) <contract:0x095e7baea6a6c7c4c2dfeb977efac326af552d87> 0 0 0 0 0) [[ 1 ]] 1  }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.POP(
                Op.CALLCODE(
                    gas=Op.GAS,
                    address=0xCF55FF2B7D15859F0CEA76885B2D9E850D7DCACD,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(key=0x1, value=0x1)
            + Op.STOP
        ),
        balance=0x1312D00,
        nonce=0,
        address=Address("0x3134aac90d2474f00108572cb10ad2de05bfa7ee"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=Op.ADD(Op.MLOAD(offset=0x0), 0x1))
            + Op.STATICCALL(
                gas=Op.SUB(Op.GAS, 0x3A98),
                address=Op.ADDRESS,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        balance=0x1312D00,
        nonce=0,
        address=Address("0xcf55ff2b7d15859f0cea76885b2d9e850d7dcacd"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=20622100,
        value=100000,
    )

    post = {
        contract: Account(storage={1: 1}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
