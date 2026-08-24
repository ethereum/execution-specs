"""
Test_zero_value_callcode_to_non_zero_balance.

Ported from:
state_tests/stZeroCallsTest/ZeroValue_CALLCODE_ToNonZeroBalanceFiller.json

@manually-enhanced: Do not overwrite. The post-state asserts the
`Op.GAS` value stored at slot 0 (0x8D5B6), which depends on the gas
remaining at a fixed execution point. To hold that point constant, the
`gas_limit` is derived from the fork gas model rather than hardcoded:
`gas_limit = 600_000 + (intrinsic - 21_000)`, where `intrinsic` comes
from `fork.transaction_intrinsic_cost_calculator()`. Subtracting the
pre-EIP-2780 baseline intrinsic 21_000 keeps the post-intrinsic
execution budget at 600_000 across the EIP-2780 intrinsic
decomposition (which lowers the intrinsic for non-self, non-value txs).
Do not hardcode the gas_limit.
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
        "state_tests/stZeroCallsTest/ZeroValue_CALLCODE_ToNonZeroBalanceFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
@pytest.mark.valid_before("EIP8368")
def test_zero_value_callcode_to_non_zero_balance(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Test_zero_value_callcode_to_non_zero_balance."""
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

    addr = pre.fund_eoa(amount=100)  # noqa: F841
    # Source: lll
    # { [[0]](GAS) [[1]] (CALLCODE 60000 <eoa:0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0 0) [[100]] 1 }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=Op.GAS)
        + Op.SSTORE(
            key=0x1,
            value=Op.CALLCODE(
                gas=0xEA60,
                address=addr,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(key=0x64, value=0x1)
        + Op.STOP,
        nonce=0,
    )

    # Preserve Cancun's post-intrinsic execution budget across
    # forks; EIP-2780 lowers the intrinsic for non-self non-value
    # txs, and the Op.GAS storage assertion depends on the
    # remaining gas at a fixed execution point.
    intrinsic = fork.transaction_intrinsic_cost_calculator()()
    gas_limit = 600_000 + (intrinsic - 21_000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=gas_limit,
    )

    post = {
        addr: Account(balance=100),
        target: Account(storage={0: 0x8D5B6, 1: 1, 100: 1}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
