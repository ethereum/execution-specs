"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stRefundTest/refund50_1Filler.json
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
    ["tests/static/state_tests/stRefundTest/refund50_1Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_refund50_1(
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

    # Source: LLL
    # { [[ 1 ]] 0 [[ 2 ]] 0 [[ 3 ]] 0 [[ 4 ]] 0 [[ 5 ]] 0 }
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x1, value=0x0)
            + Op.SSTORE(key=0x2, value=0x0)
            + Op.SSTORE(key=0x3, value=0x0)
            + Op.SSTORE(key=0x4, value=0x0)
            + Op.SSTORE(key=0x5, value=0x0)
            + Op.STOP
        ),
        storage={0x1: 0x1, 0x2: 0x1, 0x3: 0x1, 0x4: 0x1, 0x5: 0x1},
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x6737eac10f0b6ff19a1c903cafc30b26752a5af4"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x989680)
    pre[coinbase] = Account(balance=0, nonce=1)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=100000,
    )

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
