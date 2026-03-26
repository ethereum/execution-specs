"""
test_loop_calls_depth_then_revert2

Ported from:
state_tests/stRevertTest/LoopCallsDepthThenRevert2Filler.json
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
    ["state_tests/stRevertTest/LoopCallsDepthThenRevert2Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.pre_alloc_mutable
def test_loop_calls_depth_then_revert2(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_loop_calls_depth_then_revert2"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    contract_0 = Address("0xa000000000000000000000000000000000000000")
    sender = EOA(
        key=0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8
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

    pre[sender] = Account(balance=0x13426172c74d822b878fe800000000)
    # Source: raw
    # 0x6103ff60005414603f576001600054016000556000600060006000600073a0000000000000000000000000000000000000005af15061041a600054106053575b66600060006002f0600052600760196003f0505b
    contract_0 = pre.deploy_contract(
        code=Op.JUMPI(pc=0x3f, condition=Op.EQ(Op.SLOAD(key=0x0), 0x3ff))
        + Op.SSTORE(key=0x0, value=Op.ADD(Op.SLOAD(key=0x0), 0x1))
        + Op.POP(Op.CALL(gas=Op.GAS, address=0xa000000000000000000000000000000000000000, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.JUMPI(pc=0x53, condition=Op.LT(Op.SLOAD(key=0x0), 0x41a))
        + Op.JUMPDEST + Op.MSTORE(offset=0x0, value=0x600060006002f0)
        + Op.POP(Op.CREATE(value=0x3, offset=0x19, size=0x7)) + Op.JUMPDEST,
        balance=10,
        nonce=0,
        address=Address("0xa000000000000000000000000000000000000000"),  # noqa: E501
    )


    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=b'',
        gas_limit=9214364837600034817,
        nonce=0,
        gas_price=10,
    )

    post = {
        Address("0x7db299e0885c85039f56fa504a13dd8ce8a56aa7"): Account(balance=3, nonce=1),  # noqa: E501
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
