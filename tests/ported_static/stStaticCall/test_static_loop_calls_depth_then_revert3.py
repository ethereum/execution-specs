"""
Test_static_loop_calls_depth_then_revert3.

Ported from:
state_tests/stStaticCall/static_LoopCallsDepthThenRevert3Filler.json
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stStaticCall/static_LoopCallsDepthThenRevert3Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.slow
@pytest.mark.pre_alloc_mutable
def test_static_loop_calls_depth_then_revert3(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_static_loop_calls_depth_then_revert3."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0xA000000000000000000000000000000000000000)
    sender = pre.fund_eoa(amount=0x13426172C74D822B878FE800000000)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    # Source: raw
    # 0x6103fe60003514603d57600160003501600052600060006020600073a0000000000000000000000000000000000000005afa5061041a600035106051575b66600060006002f0600052600760196003f0505b  # noqa: E501
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.JUMPI(
            pc=0x3D, condition=Op.EQ(Op.CALLDATALOAD(offset=0x0), 0x3FE)
        )
        + Op.MSTORE(offset=0x0, value=Op.ADD(Op.CALLDATALOAD(offset=0x0), 0x1))
        + Op.POP(
            Op.STATICCALL(
                gas=Op.GAS,
                address=0xA000000000000000000000000000000000000000,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.JUMPI(
            pc=0x51, condition=Op.LT(Op.CALLDATALOAD(offset=0x0), 0x41A)
        )
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x0, value=0x600060006002F0)
        + Op.POP(Op.CREATE(value=0x3, offset=0x19, size=0x7))
        + Op.JUMPDEST,
        balance=10,
        nonce=0,
        address=Address(0xA000000000000000000000000000000000000000),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=Bytes(""),
        gas_limit=9214364837600034817,
    )

    post = {
        compute_create_address(
            address=contract_0, nonce=0
        ): Account.NONEXISTENT,
        compute_create_address(
            address=compute_create_address(address=contract_0, nonce=0),
            nonce=1,
        ): Account.NONEXISTENT,
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
