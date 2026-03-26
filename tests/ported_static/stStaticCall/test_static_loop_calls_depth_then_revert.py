"""
test_static_loop_calls_depth_then_revert

Ported from:
state_tests/stStaticCall/static_LoopCallsDepthThenRevertFiller.json
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
    ["state_tests/stStaticCall/static_LoopCallsDepthThenRevertFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_static_loop_calls_depth_then_revert(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_static_loop_calls_depth_then_revert"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x4f31b3206fbf0e0e598b9b1a7d8ac86302a0ff1d8930738f1bebae9b67173e52
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[sender] = Account(balance=0xe8d4a51000)
    # Source: lll
    # { [[ 0 ]] (CALL ( - (GAS) 100000) <contract:target:0x1000000000000000000000000000000000000000> 0 0 0 0 0) [[ 1 ]] 1 }
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.CALL(gas=Op.SUB(Op.GAS, 0x186a0), address=0x15dc6ad6aa4b45c8c5f8658596f0be95f4fb77fd, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0x1, value=0x1) + Op.STOP,
        nonce=0,
        address=Address("0x15dc6ad6aa4b45c8c5f8658596f0be95f4fb77fd"),  # noqa: E501
    )
    # Source: lll
    # { (STATICCALL (GAS) <contract:0xb000000000000000000000000000000000000000> 0 0 0 0) }
    addr_0xa000000000000000000000000000000000000000 = pre.deploy_contract(
        code=Op.STATICCALL(gas=Op.GAS, address=0x8ac26ad64561031be35e49c24ee18c6e43c21795, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0)
        + Op.STOP,
        nonce=0,
        address=Address("0x77c35f69d9f67cc9c06c803eb2c0aca9c2a746e6"),  # noqa: E501
    )
    # Source: lll
    # { (STATICCALL (GAS) <contract:0xa000000000000000000000000000000000000000> 0 0 0 0)  }
    addr_0xb000000000000000000000000000000000000000 = pre.deploy_contract(
        code=Op.STATICCALL(gas=Op.GAS, address=0x77c35f69d9f67cc9c06c803eb2c0aca9c2a746e6, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0)
        + Op.STOP,
        nonce=0,
        address=Address("0x8ac26ad64561031be35e49c24ee18c6e43c21795"),  # noqa: E501
    )


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=10000000,
        nonce=0,
        gas_price=10,
    )

    post = {target: Account(storage={0: 1, 1: 1})}

    state_test(env=env, pre=pre, post=post, tx=tx)
