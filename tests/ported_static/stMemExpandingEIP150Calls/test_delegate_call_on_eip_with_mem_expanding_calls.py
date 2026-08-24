"""
Test_delegate_call_on_eip_with_mem_expanding_calls.

Ported from:
state_tests/stMemExpandingEIP150Calls/DelegateCallOnEIPWithMemExpandingCallsFiller.json

@manually-enhanced: Do not overwrite. The post-state asserts the GAS
opcode value stored at target slot 8 (0x8D5B6), which depends on the
execution budget left after the intrinsic charge. The original test
hardcoded `gas_limit` against Cancun's `TX_BASE` of 21_000; EIP-2780
lowers the intrinsic for non-self non-value txs, so `gas_limit` is
derived from the fork as `600_000 + (intrinsic - 21_000)`, subtracting
the pre-EIP-2780 baseline 21_000 so the budget is invariant across the
intrinsic decomposition and EIP-8038 access repricing. Do not hardcode
the literal gas_limit.
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
        "state_tests/stMemExpandingEIP150Calls/DelegateCallOnEIPWithMemExpandingCallsFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
@pytest.mark.valid_before("EIP8368")
def test_delegate_call_on_eip_with_mem_expanding_calls(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Test_delegate_call_on_eip_with_mem_expanding_calls."""
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

    # Source: hex
    # 0x6012600055
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x12),
        nonce=0,
    )
    # Source: hex
    # 0x5a60085560ff60ff60ff60ff73<contract:0x1000000000000000000000000000000000000105>620927c0f4600955  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x8, value=Op.GAS)
        + Op.SSTORE(
            key=0x9,
            value=Op.DELEGATECALL(
                gas=0x927C0,
                address=addr,
                args_offset=0xFF,
                args_size=0xFF,
                ret_offset=0xFF,
                ret_size=0xFF,
            ),
        ),
        nonce=0,
    )

    # The original test was built against Cancun's ``TX_BASE`` of
    # 21_000. EIP-2780 lowers the intrinsic for non-self non-value
    # txs, so shift ``gas_limit`` by the intrinsic delta to preserve
    # the post-intrinsic execution budget the Op.GAS storage
    # assertion depends on.
    intrinsic = fork.transaction_intrinsic_cost_calculator()()
    gas_limit = 600_000 + (intrinsic - 21_000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=gas_limit,
    )

    post = {
        sender: Account(nonce=1),
        target: Account(storage={0: 18, 8: 0x8D5B6, 9: 1}),
        addr: Account(storage={}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
