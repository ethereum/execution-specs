"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stDelegatecallTestHomestead/CallLoseGasOOGFiller.json
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
        "tests/static/state_tests/stDelegatecallTestHomestead/CallLoseGasOOGFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_call_lose_gas_oog(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    sender = EOA(
        key=0xE7C72B378297589ACEE4E0BA3272841BCFC5E220F86DE253F890274CFEE9E474
    )
    callee = Address("0xd9b97c712ebce43f3c19179bbef44b550f9e8bc0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    pre[sender] = Account(balance=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
    # Source: LLL
    # { [[ 0 ]] (ADD @@0 1) [[ 1 ]] (DELEGATECALL (ADD 1(MUL @@0 100000)) <contract:target:0xbbbf5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0) [[ 2 ]] (ADD 1(MUL @@0 1000)) }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=Op.ADD(Op.SLOAD(key=0x0), 0x1))
            + Op.SSTORE(
                key=0x1,
                value=Op.DELEGATECALL(
                    gas=Op.ADD(0x1, Op.MUL(Op.SLOAD(key=0x0), 0x186A0)),
                    address=0xBE855315B63D137B74D5EED6BE5CD9DDE6E2478D,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(
                key=0x2,
                value=Op.ADD(0x1, Op.MUL(Op.SLOAD(key=0x0), 0x3E8)),
            )
            + Op.STOP
        ),
        balance=1024,
        nonce=0,
        address=Address("0xbe855315b63d137b74d5eed6be5cd9dde6e2478d"),  # noqa: E501
    )
    pre[callee] = Account(balance=7000, nonce=0)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=200000,
        value=10,
    )

    post = {
        contract: Account(storage={0: 1, 2: 1001}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
