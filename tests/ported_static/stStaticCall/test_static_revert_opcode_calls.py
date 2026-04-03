"""
Test_static_revert_opcode_calls.

Ported from:
state_tests/stStaticCall/static_RevertOpcodeCallsFiller.json
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
from execution_testing.forks import Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stStaticCall/static_RevertOpcodeCallsFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.slow
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="-g0",
        ),
        pytest.param(
            0,
            1,
            0,
            id="-g1",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_static_revert_opcode_calls(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_static_revert_opcode_calls."""
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
        gas_limit=10000000,
    )

    pre[sender] = Account(balance=0xE8D4A51000)
    # Source: lll
    # {   [[0]] (STATICCALL 50000 <contract:0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0) [[1]] (RETURNDATASIZE)}  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.STATICCALL(
                gas=0xC350,
                address=0xBE254B4ACEB5B7495F1A5646BE06FE5A158581EC,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(key=0x1, value=Op.RETURNDATASIZE)
        + Op.STOP,
        balance=1,
        nonce=0,
        address=Address(0x187C91277DEEEDF062A07B44DE3C96C6E7CBC7BB),  # noqa: E501
    )
    # Source: lll
    # { (REVERT 0 1) }
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.REVERT(offset=0x0, size=0x1) + Op.STOP,
        balance=1,
        nonce=0,
        address=Address(0xBE254B4ACEB5B7495F1A5646BE06FE5A158581EC),  # noqa: E501
    )

    tx_data = [
        Bytes(""),
    ]
    tx_gas = [460000, 88000]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
    )

    post = {target: Account(storage={1: 1})}

    state_test(env=env, pre=pre, post=post, tx=tx)
