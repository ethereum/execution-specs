"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
state_tests/stMemExpandingEIP150Calls/OOGinReturnFiller.yml
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    Hash,
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
    ["state_tests/stMemExpandingEIP150Calls/OOGinReturnFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="d0",
        ),
        pytest.param(
            1,
            0,
            0,
            id="d1",
        ),
        pytest.param(
            2,
            0,
            0,
            id="d2",
        ),
        pytest.param(
            3,
            0,
            0,
            id="d3",
        ),
        pytest.param(
            4,
            0,
            0,
            id="d4",
        ),
        pytest.param(
            5,
            0,
            0,
            id="d5",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_oo_gin_return(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Ori Pomerantz qbzzt1@gmail."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0xBA1A9CE0BA1A9CE)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=4294967296,
    )

    # Source: lll
    # {
    #     [0] 0xDEAD60A7
    #     (return 0 0x100)
    # }
    return_ = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=0xDEAD60A7)
        + Op.RETURN(offset=0x0, size=0x100)
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x9F5C4C430E37B429D18F8ABA147E2302AF08F210),  # noqa: E501
    )
    # Source: lll
    # {
    #     [0] 0xDEAD60A7
    #     (revert 0 0x100)
    # }
    revert = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=0xDEAD60A7)
        + Op.REVERT(offset=0x0, size=0x100)
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0xCEE9F0C6117CC881AD7B4C378C2BEBEE8FCD04A9),  # noqa: E501
    )
    # Source: lll
    # {
    #   ; Variables are 0x20 bytes (= 256 bits) apart, except for
    #   ; code buffers that get 0x100 (256 bytes)
    #   (def 'callRet    0x100)
    #   (def 'type       0x120)
    #   (def 'gas2Use    0x140)
    #   (def 'retVal     0x160)
    #   ; Other constants
    #   (def 'NOP 0)   ; No OPeration
    #   ; Understand the input.
    #   [type]       $4
    #   [gas2Use]    $36
    #   ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
    #   [0] 0x60A760A7
    #   [callRet] (call @gas2Use
    #                   @type
    #                   0
    #                   0 0
    #                   0 0x100)
    #   [[0]] @0    ; first 0x20 bytes of return data
    #   (if (> (returndatasize) 0) (returndatacopy retVal 0 0x20) NOP)
    #   [[1]] @retVal
    # }   ; end of LLL code
    target = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x120, value=Op.CALLDATALOAD(offset=0x4))
        + Op.MSTORE(offset=0x140, value=Op.CALLDATALOAD(offset=0x24))
        + Op.MSTORE(offset=0x0, value=0x60A760A7)
        + Op.MSTORE(
            offset=0x100,
            value=Op.CALL(
                gas=Op.MLOAD(offset=0x140),
                address=Op.MLOAD(offset=0x120),
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x100,
            ),
        )
        + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
        + Op.JUMPI(pc=0x41, condition=Op.GT(Op.RETURNDATASIZE, 0x0))
        + Op.POP(0x0)
        + Op.JUMP(pc=0x4A)
        + Op.JUMPDEST
        + Op.RETURNDATACOPY(dest_offset=0x160, offset=0x0, size=0x20)
        + Op.JUMPDEST
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x160))
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0xEBD3191DD8150F47E30F87927DB4592163EE9224),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": [0, 1], "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 0xDEAD60A7, 1: 0xDEAD60A7})
            },
        },
        {
            "indexes": {"data": [2, 3, 4, 5], "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {target: Account(storage={0: 0x60A760A7})},
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Bytes("1a8451e6") + Hash(return_, left_padding=True) + Hash(0x36),
        Bytes("1a8451e6") + Hash(revert, left_padding=True) + Hash(0x36),
        Bytes("1a8451e6") + Hash(return_, left_padding=True) + Hash(0x25),
        Bytes("1a8451e6") + Hash(revert, left_padding=True) + Hash(0x25),
        Bytes("1a8451e6") + Hash(return_, left_padding=True) + Hash(0x10),
        Bytes("1a8451e6") + Hash(revert, left_padding=True) + Hash(0x10),
    ]
    tx_gas = [9437184]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
