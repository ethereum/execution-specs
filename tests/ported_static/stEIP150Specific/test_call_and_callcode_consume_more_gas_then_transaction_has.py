"""
Test_call_and_callcode_consume_more_gas_then_transaction_has.

Ported from:
state_tests/stEIP150Specific/CallAndCallcodeConsumeMoreGasThenTransactionHasFiller.json

@manually-enhanced: Do not overwrite. The post-state asserts
`storage[8] = 0x8D5B6` captured by `Op.GAS`, which depends on the exact
post-intrinsic execution budget. The original hardcoded `gas_limit` of
600_000 was built against Cancun's `TX_BASE` of 21_000; EIP-2780 lowers
the intrinsic for non-self non-value txs, so `gas_limit` is derived as
`600_000 + (intrinsic - 21_000)` from `transaction_intrinsic_cost_calculator`
to shift by the fork intrinsic delta and keep the Op.GAS assertion correct.
The `- 21_000` is the pre-EIP-2780 baseline intrinsic, so the adjustment
is exactly 0 pre-repricing. Do not hardcode the literal gas_limit.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    Fork,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stEIP150Specific/CallAndCallcodeConsumeMoreGasThenTransactionHasFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
@pytest.mark.valid_before("EIP8368")
def test_call_and_callcode_consume_more_gas_then_transaction_has(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Test_call_and_callcode_consume_more_gas_then_transaction_has."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0xE8D4A51000)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    # Source: lll
    # { (SSTORE 0 0x12) }
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x12) + Op.STOP,
        nonce=0,
    )
    # Source: lll
    # { (SSTORE 8 (GAS)) (SSTORE 9 (CALL 600000 <contract:0x1000000000000000000000000000000000000103> 0 0 0 0 0)) (SSTORE 10 (CALLCODE 600000 <contract:0x1000000000000000000000000000000000000103> 0 0 0 0 0)) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x8, value=Op.GAS)
        + Op.SSTORE(
            key=0x9,
            value=Op.CALL(
                gas=0x927C0,
                address=addr,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(
            key=0xA,
            value=Op.CALLCODE(
                gas=0x927C0,
                address=addr,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.STOP,
        nonce=0,
    )

    # The original test was built against Cancun's ``TX_BASE`` of
    # 21_000. EIP-2780 lowers the intrinsic for non-self non-value
    # txs, so shift ``gas_limit`` by the intrinsic delta to preserve
    # the post-intrinsic execution budget the Op.GAS storage
    # assertions depend on.
    intrinsic = fork.transaction_intrinsic_cost_calculator()()
    gas_limit = 600_000 + (intrinsic - 21_000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=gas_limit,
    )

    post = {target: Account(storage={0: 18, 8: 0x8D5B6, 9: 1, 10: 1})}

    state_test(env=env, pre=pre, post=post, tx=tx)
