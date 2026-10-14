"""
Test_static_loop_calls_depth_then_revert3.

Ported from:
state_tests/stStaticCall/static_LoopCallsDepthThenRevert3Filler.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytes,
    Environment,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.vm import Op

from tests.ported_static.constants import HIGH_GAS_LIMIT

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stStaticCall/static_LoopCallsDepthThenRevert3Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.slow
def test_static_loop_calls_depth_then_revert3(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_static_loop_calls_depth_then_revert3."""
    env = Environment(gas_limit=HIGH_GAS_LIMIT)

    sender = pre.fund_eoa(amount=0x13426172C74D822B878FE800000000)

    # Source: raw
    # 0x6103fe60003514603d57600160003501600052600060006020600073a0000000000000000000000000000000000000005afa5061041a600035106051575b66600060006002f0600052600760196003f0505b  # noqa: E501
    contract_0 = pre.deploy_contract(
        code=Op.JUMPI(
            pc=0x29, condition=Op.EQ(Op.CALLDATALOAD(offset=0x0), 0x3FE)
        )
        + Op.MSTORE(offset=0x0, value=Op.ADD(Op.CALLDATALOAD(offset=0x0), 0x1))
        + Op.POP(
            Op.STATICCALL(
                gas=Op.GAS,
                address=Op.ADDRESS,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.JUMPI(
            pc=0x3D, condition=Op.LT(Op.CALLDATALOAD(offset=0x0), 0x41A)
        )
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x0, value=0x600060006002F0)
        + Op.POP(Op.CREATE(value=0x3, offset=0x19, size=0x7))
        + Op.JUMPDEST,
        balance=10,
    )

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=Bytes(""),
        gas_limit=9214364837600034817,
    )

    post = {
        compute_create_address(
            address=contract_0, nonce=1
        ): Account.NONEXISTENT,
        compute_create_address(
            address=compute_create_address(address=contract_0, nonce=1),
            nonce=1,
        ): Account.NONEXISTENT,
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
