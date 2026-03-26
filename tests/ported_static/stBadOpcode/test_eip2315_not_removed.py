"""
test_eip2315_not_removed

Ported from:
state_tests/stBadOpcode/eip2315NotRemovedFiller.json
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
    ["state_tests/stBadOpcode/eip2315NotRemovedFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_eip2315_not_removed(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_eip2315_not_removed"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x31b5af02b012484ae954b3a43943242ede546a2e76fc0a6acc17435107c385eb
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    # Source: raw
    # 0x60045e005c60016000555d
    target = pre.deploy_contract(
        code=Op.PUSH1[0x4] + Op.MCOPY + Op.STOP + Op.TLOAD
        + Op.SSTORE(key=0x0, value=0x1) + Op.TSTORE,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0x147943601b1281618e4d824d11073025cd2ac623"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x7fffffffffffffff)


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=400000,
        nonce=0,
        gas_price=10,
    )

    post = {target: Account(storage={})}

    state_test(env=env, pre=pre, post=post, tx=tx)
