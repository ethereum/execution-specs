"""
Test_loop_calls_then_revert.

Ported from:
state_tests/stRevertTest/LoopCallsThenRevertFiller.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stRevertTest/LoopCallsThenRevertFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_loop_calls_then_revert(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_loop_calls_then_revert."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0x4F31B3206FBF0E0E598B9B1A7D8AC86302A0FF1D8930738F1BEBAE9B67173E52
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[sender] = Account(balance=0xE8D4A51000)
    # Source: raw
    # 0x5b6001600054036000556000600060006000600073<contract:0xb000000000000000000000000000000000000000>61c350f150600054600057  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.JUMPDEST
        + Op.SSTORE(key=0x0, value=Op.SUB(Op.SLOAD(key=0x0), 0x1))
        + Op.POP(
            Op.CALL(
                gas=0xC350,
                address=0xC47BCBF49DD735566CFDE927821E938D5B33014C,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.JUMPI(pc=0x0, condition=Op.SLOAD(key=0x0)),
        storage={0: 850},
        nonce=0,
        address=Address(0x0347AFF20D9D3C574E18F3B17DC267DDCD2D75CA),  # noqa: E501
    )
    # Source: lll
    # { [[0]] (ADD 1 (SLOAD 0)) }
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=Op.ADD(0x1, Op.SLOAD(key=0x0)))
        + Op.STOP,
        nonce=0,
        address=Address(0xC47BCBF49DD735566CFDE927821E938D5B33014C),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=10000000,
    )

    post = {
        target: Account(storage={0: 0}),
        addr: Account(storage={0: 850}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
