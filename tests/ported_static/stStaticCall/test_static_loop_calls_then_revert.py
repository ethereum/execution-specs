"""
Requires a separate pre-alloc group due to time required to fill when...

Ported from:
state_tests/stStaticCall/static_LoopCallsThenRevertFiller.json
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
)
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stStaticCall/static_LoopCallsThenRevertFiller.json"],
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
def test_static_loop_calls_then_revert(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Requires a separate pre-alloc group due to time required to fill..."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0xE8D4A51000)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    # Source: lll
    # { (MSTORE 0 (ADD 1 (MLOAD 0))) }
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=Op.ADD(0x1, Op.MLOAD(offset=0x0)))
        + Op.STOP,
        nonce=0,
    )
    # Source: raw
    # 0x5b600160003503600052600060006000600073<contract:0xb000000000000000000000000000000000000000>61c350fa50600051600057  # noqa: E501
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.JUMPDEST
        + Op.MSTORE(offset=0x0, value=Op.SUB(Op.CALLDATALOAD(offset=0x0), 0x1))
        + Op.POP(
            Op.STATICCALL(
                gas=0xC350,
                address=addr_2,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.JUMPI(pc=0x0, condition=Op.MLOAD(offset=0x0)),
        storage={0: 850},
        nonce=0,
    )
    # Source: lll
    # { (MSTORE 0 850) [[ 0 ]] (CALL (- (GAS) 10000) <contract:0xa000000000000000000000000000000000000000> 0 0 32 0 0) [[ 1 ]] 1 }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=0x352)
        + Op.SSTORE(
            key=0x0,
            value=Op.CALL(
                gas=Op.SUB(Op.GAS, 0x2710),
                address=addr,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(key=0x1, value=0x1)
        + Op.STOP,
        nonce=0,
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": -1, "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {target: Account(storage={1: 1})},
        },
        {
            "indexes": {"data": -1, "gas": 1, "value": -1},
            "network": [">=Cancun"],
            "result": {target: Account(storage={1: 1})},
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Bytes(""),
    ]
    tx_gas = [10000000, 9000000]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
