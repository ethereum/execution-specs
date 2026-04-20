"""
SELFBALANCE tests inside CALL, DELEGATECALL, and CALLCODE.

Ported from:
state_tests/stSelfBalance/selfBalanceCallTypesFiller.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
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
    ["state_tests/stSelfBalance/selfBalanceCallTypesFiller.json"],
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
    ],
)
@pytest.mark.pre_alloc_mutable
def test_self_balance_call_types(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """SELFBALANCE tests inside CALL, DELEGATECALL, and CALLCODE."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0x897B12D02D588D8A4FE16FF831CBD4459C6F62F8C845B0CCDD31CAF068C84A26
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
    )

    # Source: lll
    # { [[ 0x11 ]] (EQ (SELFBALANCE) (BALANCE (ADDRESS))) }
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x11,
            value=Op.EQ(Op.SELFBALANCE, Op.BALANCE(address=Op.ADDRESS)),
        )
        + Op.STOP,
        balance=4096,
        nonce=0,
        address=Address(0xA590BBF1B07B00FED987724E1DB1BF206C2BC37C),  # noqa: E501
    )
    # Source: lll
    # { [[ 0x21 ]] (SELFBALANCE) }
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x21, value=Op.SELFBALANCE) + Op.STOP,
        balance=4352,
        nonce=0,
        address=Address(0x76BAC61EE2056F42F6CC29F5400ADAE3E5705237),  # noqa: E501
    )
    # Source: lll
    # (asm GAS SELFBALANCE GAS SWAP1 POP SWAP1 SUB 2 SWAP1 SUB 0x31 SSTORE)
    addr_3 = pre.deploy_contract(  # noqa: F841
        code=Op.GAS
        + Op.SELFBALANCE
        + Op.GAS
        + Op.SWAP1
        + Op.POP
        + Op.SWAP1
        + Op.SUB
        + Op.PUSH1[0x2]
        + Op.SWAP1
        + Op.SSTORE(key=0x31, value=Op.SUB)
        + Op.STOP,
        balance=4608,
        nonce=0,
        address=Address(0x8537CE29429EA557E3903C255EE6554DD8D21D26),  # noqa: E501
    )
    # Source: lll
    # (asm SELFBALANCE DUP1 0x41 SSTORE 0 0 0 0 1 0 0 CALL POP SELFBALANCE DUP1 0x42 SSTORE SWAP1 SUB 0x43 SSTORE)  # noqa: E501
    addr_4 = pre.deploy_contract(  # noqa: F841
        code=Op.SELFBALANCE
        + Op.SSTORE(key=0x41, value=Op.DUP1)
        + Op.POP(
            Op.CALL(
                gas=0x0,
                address=0x0,
                value=0x1,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.SELFBALANCE
        + Op.SSTORE(key=0x42, value=Op.DUP1)
        + Op.SWAP1
        + Op.SSTORE(key=0x43, value=Op.SUB)
        + Op.STOP,
        balance=4864,
        nonce=0,
        address=Address(0xE1CE93B3251FB38AE74D41AF9F865978C572CF63),  # noqa: E501
    )
    # Source: lll
    # {(set 'i 0) (while @@ @i {(when (eq 0x01 $0x0) (call allgas @@ @i 0 0 0 0 0)) (when (eq 0x02 $0x0) (delegatecall allgas @@ @i 0 0 0 0)) (when (eq 0x03 $0x0) (callcode allgas @@ @i 0 0 0 0 0)) [i]:(+ @i 1)})}  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x80, value=0x0)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=0x75, condition=Op.ISZERO(Op.SLOAD(key=Op.MLOAD(offset=0x80)))
        )
        + Op.JUMPI(
            pc=0x2C,
            condition=Op.ISZERO(Op.EQ(0x1, Op.CALLDATALOAD(offset=0x0))),
        )
        + Op.POP(
            Op.CALL(
                gas=Op.SUB(Op.GAS, 0x15),
                address=Op.SLOAD(key=Op.MLOAD(offset=0x80)),
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=0x49,
            condition=Op.ISZERO(Op.EQ(0x2, Op.CALLDATALOAD(offset=0x0))),
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=Op.SUB(Op.GAS, 0x15),
                address=Op.SLOAD(key=Op.MLOAD(offset=0x80)),
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=0x68,
            condition=Op.ISZERO(Op.EQ(0x3, Op.CALLDATALOAD(offset=0x0))),
        )
        + Op.POP(
            Op.CALLCODE(
                gas=Op.SUB(Op.GAS, 0x15),
                address=Op.SLOAD(key=Op.MLOAD(offset=0x80)),
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x80, value=Op.ADD(Op.MLOAD(offset=0x80), 0x1))
        + Op.JUMP(pc=0x5)
        + Op.JUMPDEST
        + Op.STOP,
        storage={
            0: 0xA590BBF1B07B00FED987724E1DB1BF206C2BC37C,
            1: 0x76BAC61EE2056F42F6CC29F5400ADAE3E5705237,
            2: 0x8537CE29429EA557E3903C255EE6554DD8D21D26,
            3: 0xE1CE93B3251FB38AE74D41AF9F865978C572CF63,
        },
        balance=8192,
        nonce=0,
        address=Address(0x84BF87FBEF135AFEA15330FDF5847EB504CFF901),  # noqa: E501
    )
    pre[sender] = Account(balance=0x3635C9ADC5DEA00000)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": [0], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                addr: Account(storage={17: 1}),
                addr_2: Account(storage={33: 4352}),
                addr_3: Account(storage={49: 5}),
                addr_4: Account(storage={65: 4864, 66: 4863, 67: 1}),
            },
        },
        {
            "indexes": {"data": [1, 2], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(
                    storage={
                        0: 0xA590BBF1B07B00FED987724E1DB1BF206C2BC37C,
                        1: 0x76BAC61EE2056F42F6CC29F5400ADAE3E5705237,
                        2: 0x8537CE29429EA557E3903C255EE6554DD8D21D26,
                        3: 0xE1CE93B3251FB38AE74D41AF9F865978C572CF63,
                        17: 1,
                        33: 8192,
                        49: 5,
                        65: 8192,
                        66: 8191,
                        67: 1,
                    },
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Hash(0x1),
        Hash(0x2),
        Hash(0x3),
    ]
    tx_gas = [1000000]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
