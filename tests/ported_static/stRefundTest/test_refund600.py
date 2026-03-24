"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stRefundTest/refund600Filler.json
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
    ["tests/static/state_tests/stRefundTest/refund600Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_refund600(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0xeb201d2887816e041f6e807e804f64f3a7a226fe")
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

    pre[sender] = Account(balance=0x989680)
    # Source: LLL
    # { @@1 @@2 [[ 10 ]] (EXP 2 0xffff) [[ 11 ]] (BALANCE (ADDRESS)) [[ 1 ]] 0 [[ 2 ]] 0 [[ 3 ]] 0 [[ 4 ]] 0 [[ 5 ]] 0 [[ 6 ]] 0 }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.POP(Op.SLOAD(key=0x1))
            + Op.POP(Op.SLOAD(key=0x2))
            + Op.SSTORE(key=0xA, value=Op.EXP(0x2, 0xFFFF))
            + Op.SSTORE(key=0xB, value=Op.BALANCE(address=Op.ADDRESS))
            + Op.SSTORE(key=0x1, value=0x0)
            + Op.SSTORE(key=0x2, value=0x0)
            + Op.SSTORE(key=0x3, value=0x0)
            + Op.SSTORE(key=0x4, value=0x0)
            + Op.SSTORE(key=0x5, value=0x0)
            + Op.SSTORE(key=0x6, value=0x0)
            + Op.STOP
        ),
        storage={
            0x1: 0x1,
            0x2: 0x1,
            0x3: 0x1,
            0x4: 0x1,
            0x5: 0x1,
            0x6: 0x1,
        },
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0xc09923e2275e4ee7822a1feb5eee1c18143575c7"),  # noqa: E501
    )
    pre[coinbase] = Account(balance=0, nonce=1)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=100000,
    )

    post = {
        contract: Account(storage={11: 0xDE0B6B3A7640000}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
