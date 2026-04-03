"""
Test_refund600.

Ported from:
state_tests/stRefundTest/refund600Filler.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stRefundTest/refund600Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_refund600(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_refund600."""
    coinbase = Address(0xEB201D2887816E041F6E807E804F64F3A7A226FE)
    sender = EOA(
        key=0xDC4EFA209AECDD4C2D5201A419EA27506151B4EC687F14A613229E310932491B
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre[coinbase] = Account(balance=0, nonce=1)
    # Source: lll
    # { @@1 @@2 [[ 10 ]] (EXP 2 0xffff) [[ 11 ]] (BALANCE (ADDRESS)) [[ 1 ]] 0 [[ 2 ]] 0 [[ 3 ]] 0 [[ 4 ]] 0 [[ 5 ]] 0 [[ 6 ]] 0 }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.POP(Op.SLOAD(key=0x1))
        + Op.POP(Op.SLOAD(key=0x2))
        + Op.SSTORE(key=0xA, value=Op.EXP(0x2, 0xFFFF))
        + Op.SSTORE(key=0xB, value=Op.BALANCE(address=Op.ADDRESS))
        + Op.SSTORE(key=0x1, value=0x0)
        + Op.SSTORE(key=0x2, value=0x0)
        + Op.SSTORE(key=0x3, value=0x0)
        + Op.SSTORE(key=0x4, value=0x0)
        + Op.SSTORE(key=0x5, value=0x0)
        + Op.SSTORE(key=0x6, value=0x0)
        + Op.STOP,
        storage={1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1},
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0xC09923E2275E4EE7822A1FEB5EEE1C18143575C7),  # noqa: E501
    )
    pre[sender] = Account(balance=0x989680)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=100000,
    )

    post = {
        target: Account(storage={11: 0xDE0B6B3A7640000}),
        coinbase: Account(balance=0),
        sender: Account(balance=0x8F5CF0),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
