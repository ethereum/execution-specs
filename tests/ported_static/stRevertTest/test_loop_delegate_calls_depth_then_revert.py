"""
test_loop_delegate_calls_depth_then_revert

Ported from:
state_tests/stRevertTest/LoopDelegateCallsDepthThenRevertFiller.json
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
    ["state_tests/stRevertTest/LoopDelegateCallsDepthThenRevertFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_loop_delegate_calls_depth_then_revert(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_loop_delegate_calls_depth_then_revert"""
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
    # { [[0]] (+ (SLOAD 0) 1) (DELEGATECALL (GAS) <contract:0xb000000000000000000000000000000000000000> 0 0 0 0) }
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.ADD(Op.SLOAD(key=0x0), 0x1))
        + Op.DELEGATECALL(gas=Op.GAS, address=0xf798cb78490da31dfacdcd1f2b3fb1948bb2b228, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0)
        + Op.STOP,
        nonce=0,
        address=Address("0xb0923c4a632de291fcdac653e6c6cc2b4e4cdfa8"),  # noqa: E501
    )
    # Source: lll
    # { [[0]] (+ (SLOAD 0) 1) (DELEGATECALL (GAS) <contract:target:0xa000000000000000000000000000000000000000> 0 0 0 0)  }
    addr_0xb000000000000000000000000000000000000000 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.ADD(Op.SLOAD(key=0x0), 0x1))
        + Op.DELEGATECALL(gas=Op.GAS, address=0xb0923c4a632de291fcdac653e6c6cc2b4e4cdfa8, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0)
        + Op.STOP,
        nonce=0,
        address=Address("0xf798cb78490da31dfacdcd1f2b3fb1948bb2b228"),  # noqa: E501
    )


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=10000000,
        nonce=0,
        gas_price=10,
    )

    post = {
        target: Account(storage={0: 386}),
        addr_0xb000000000000000000000000000000000000000: Account(storage={}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
