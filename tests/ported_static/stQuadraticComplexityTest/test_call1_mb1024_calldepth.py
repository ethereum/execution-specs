"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stQuadraticComplexityTest
Call1MB1024CalldepthFiller.json
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
        "tests/static/state_tests/stQuadraticComplexityTest/Call1MB1024CalldepthFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.parametrize(
    "tx_gas_limit, expected_post",
    [
        (150000, {}),
        (
            250000000,
            {
                Address("0x9d15232f6851f9f3a88f88a3b358ed1579977a5a"): Account(
                    storage={0: 69, 1: 1}
                )
            },
        ),
    ],
    ids=["case0", "case1"],
)
@pytest.mark.pre_alloc_mutable
@pytest.mark.slow
def test_call1_mb1024_calldepth(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
    expected_post: dict,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    sender = EOA(
        key=0xE7C72B378297589ACEE4E0BA3272841BCFC5E220F86DE253F890274CFEE9E474
    )
    callee = Address("0x2ab8257767339461506c0c67824cf17bc77b52ca")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=882500000000,
    )

    pre[callee] = Account(balance=0xFFFFFFFFFFFFF, nonce=0)
    pre[sender] = Account(balance=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
    # Source: LLL
    # { (def 'i 0x80) [[ 0 ]] (+ @@0 1) (if (LT @@0 1024) [[ 1 ]] (CALL (- (GAS) 1005000) <contract:target:0xbbbf5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 1000000 0 0) [[ 2 ]] 1 )  }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=Op.ADD(Op.SLOAD(key=0x0), 0x1))
            + Op.JUMPI(pc=0x1B, condition=Op.LT(Op.SLOAD(key=0x0), 0x400))
            + Op.SSTORE(key=0x2, value=0x1)
            + Op.JUMP(pc=0x47)
            + Op.JUMPDEST
            + Op.SSTORE(
                key=0x1,
                value=Op.CALL(
                    gas=Op.SUB(Op.GAS, 0xF55C8),
                    address=0x9D15232F6851F9F3A88F88A3B358ED1579977A5A,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0xF4240,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.JUMPDEST
            + Op.STOP
        ),
        balance=0xFFFFFFFFFFFFF,
        nonce=0,
        address=Address("0x9d15232f6851f9f3a88f88a3b358ed1579977a5a"),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=tx_gas_limit,
        value=10,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
