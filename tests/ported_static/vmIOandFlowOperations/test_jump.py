"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
state_tests/VMTests/vmIOandFlowOperations/jumpFiller.yml
"""

import pytest
from execution_testing import (
    EOA,
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
    ["state_tests/VMTests/vmIOandFlowOperations/jumpFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="jump-hyperspace",
        ),
        pytest.param(
            1,
            0,
            0,
            id="jump-hyperspace",
        ),
        pytest.param(
            2,
            0,
            0,
            id="jump-stop-dest",
        ),
        pytest.param(
            3,
            0,
            0,
            id="jump-hyperspace",
        ),
        pytest.param(
            4,
            0,
            0,
            id="jump-not-jumpdest",
        ),
        pytest.param(
            5,
            0,
            0,
            id="endless-loop",
        ),
        pytest.param(
            6,
            0,
            0,
            id="jump-dest",
        ),
        pytest.param(
            7,
            0,
            0,
            id="jump-dest",
        ),
        pytest.param(
            8,
            0,
            0,
            id="jump-dynamic",
        ),
        pytest.param(
            9,
            0,
            0,
            id="jump-2-push",
        ),
        pytest.param(
            10,
            0,
            0,
            id="jump-2-push",
        ),
        pytest.param(
            11,
            0,
            0,
            id="jump-not-jumpdest",
        ),
        pytest.param(
            12,
            0,
            0,
            id="jump-not-jumpdest",
        ),
        pytest.param(
            13,
            0,
            0,
            id="jump-hyperspace",
        ),
        pytest.param(
            14,
            0,
            0,
            id="jump-hyperspace",
        ),
        pytest.param(
            15,
            0,
            0,
            id="jump-hyperspace",
        ),
        pytest.param(
            16,
            0,
            0,
            id="jump-to-list",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_jump(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Ori Pomerantz qbzzt1@gmail."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0x0000000000000000000000000000000000001000)
    contract_1 = Address(0x0000000000000000000000000000000000001001)
    contract_2 = Address(0x0000000000000000000000000000000000001002)
    contract_3 = Address(0x0000000000000000000000000000000000001003)
    contract_4 = Address(0x0000000000000000000000000000000000001004)
    contract_5 = Address(0x0000000000000000000000000000000000001005)
    contract_6 = Address(0x0000000000000000000000000000000000001006)
    contract_7 = Address(0x0000000000000000000000000000000000001007)
    contract_8 = Address(0x0000000000000000000000000000000000001008)
    contract_9 = Address(0x0000000000000000000000000000000000001009)
    contract_10 = Address(0x000000000000000000000000000000000000100A)
    contract_11 = Address(0x000000000000000000000000000000000000100B)
    contract_12 = Address(0x000000000000000000000000000000000000100C)
    contract_13 = Address(0x000000000000000000000000000000000000100D)
    contract_14 = Address(0x000000000000000000000000000000000000100E)
    contract_15 = Address(0x000000000000000000000000000000000000100F)
    contract_16 = Address(0x0000000000000000000000000000000000001010)
    contract_17 = Address(0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC)
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    # Source: lll
    # {
    #   [[0]] 0x600D
    #   (asm 0x10 0x20 mul jump jumpdest)
    # }
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x600D)
        + Op.JUMP(pc=Op.MUL(0x20, 0x10))
        + Op.JUMPDEST
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001000),  # noqa: E501
    )
    # Source: lll
    # {
    #   [[0]] 0x600D
    #   (asm 0x01 0x10 0x20 mul jumpi jumpdest)
    # }
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x600D)
        + Op.JUMPI(pc=Op.MUL(0x20, 0x10), condition=0x1)
        + Op.JUMPDEST
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001001),  # noqa: E501
    )
    # Source: raw
    # 0x600456005B61600D60005500
    contract_2 = pre.deploy_contract(  # noqa: F841
        code=Op.JUMP(pc=0x4)
        + Op.STOP
        + Op.JUMPDEST
        + Op.SSTORE(key=0x0, value=0x600D)
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001002),  # noqa: E501
    )
    # Source: lll
    # {
    #   [[0]] 0x600D
    #   (asm 0x0fffffff jump)
    # }
    contract_3 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x600D)
        + Op.JUMP(pc=0xFFFFFFF)
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001003),  # noqa: E501
    )
    # Source: raw
    # 0x602360085660015b600255
    contract_4 = pre.deploy_contract(  # noqa: F841
        code=Op.PUSH1[0x23]
        + Op.JUMP(pc=0x8)
        + Op.PUSH1[0x1]
        + Op.JUMPDEST
        + Op.PUSH1[0x2]
        + Op.SSTORE,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001004),  # noqa: E501
    )
    # Source: raw
    # 0x61600D6000555B600656
    contract_5 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x600D) + Op.JUMPDEST + Op.JUMP(pc=0x6),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001005),  # noqa: E501
    )
    # Source: raw
    # 0x61600D60085660FF5B600055
    contract_6 = pre.deploy_contract(  # noqa: F841
        code=Op.PUSH2[0x600D]
        + Op.JUMP(pc=0x8)
        + Op.PUSH1[0xFF]
        + Op.JUMPDEST
        + Op.PUSH1[0x0]
        + Op.SSTORE,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001006),  # noqa: E501
    )
    # Source: raw
    # 0x600B565B61600D600055005B600356
    contract_7 = pre.deploy_contract(  # noqa: F841
        code=Op.JUMP(pc=0xB)
        + Op.JUMPDEST
        + Op.SSTORE(key=0x0, value=0x600D)
        + Op.STOP
        + Op.JUMPDEST
        + Op.JUMP(pc=0x3),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001007),  # noqa: E501
    )
    # Source: raw
    # 0x600260050156005B61600D600055
    contract_8 = pre.deploy_contract(  # noqa: F841
        code=Op.JUMP(pc=Op.ADD(0x5, 0x2))
        + Op.STOP
        + Op.JUMPDEST
        + Op.SSTORE(key=0x0, value=0x600D),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001008),  # noqa: E501
    )
    # Source: raw
    # 0x60055600605B61600D600055
    contract_9 = pre.deploy_contract(  # noqa: F841
        code=Op.JUMP(pc=0x5)
        + Op.STOP
        + Op.PUSH1[0x5B]
        + Op.SSTORE(key=0x0, value=0x600D),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001009),  # noqa: E501
    )
    # Source: raw
    # 0x60055600600161600D600055
    contract_10 = pre.deploy_contract(  # noqa: F841
        code=Op.JUMP(pc=0x5)
        + Op.STOP
        + Op.PUSH1[0x1]
        + Op.SSTORE(key=0x0, value=0x600D),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000100A),  # noqa: E501
    )
    # Source: raw
    # 0x61600D600055600B565A5B5A600155
    contract_11 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x600D)
        + Op.JUMP(pc=0xB)
        + Op.GAS
        + Op.JUMPDEST
        + Op.SSTORE(key=0x1, value=Op.GAS),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000100B),  # noqa: E501
    )
    # Source: raw
    # 0x61600D6000556009565A5B5A600155
    contract_12 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x600D)
        + Op.JUMP(pc=0x9)
        + Op.GAS
        + Op.JUMPDEST
        + Op.SSTORE(key=0x1, value=Op.GAS),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000100C),  # noqa: E501
    )
    # Source: raw
    # 0x6801000000000000000b565b5b6001600155
    contract_13 = pre.deploy_contract(  # noqa: F841
        code=Op.JUMP(pc=0x1000000000000000B)
        + Op.JUMPDEST * 2
        + Op.SSTORE(key=0x1, value=0x1),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000100D),  # noqa: E501
    )
    # Source: raw
    # 0x640100000007565b5b6001600155
    contract_14 = pre.deploy_contract(  # noqa: F841
        code=Op.JUMP(pc=0x100000007)
        + Op.JUMPDEST * 2
        + Op.SSTORE(key=0x1, value=0x1),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000100E),  # noqa: E501
    )
    # Source: lll
    # {
    #   @0 (- 0 1)
    #   (asm 0 mload jump 0x600D 0x00 sstore)
    # }
    contract_15 = pre.deploy_contract(  # noqa: F841
        code=Op.POP(Op.MLOAD(offset=0x0))
        + Op.POP(Op.SUB(0x0, 0x1))
        + Op.JUMP(pc=Op.MLOAD(offset=0x0))
        + Op.SSTORE(key=0x0, value=0x600D)
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000100F),  # noqa: E501
    )
    # Source: raw
    # 0x600E565B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B61600D600055
    contract_16 = pre.deploy_contract(  # noqa: F841
        code=Op.JUMP(pc=0xE)
        + Op.JUMPDEST * 16
        + Op.SSTORE(key=0x0, value=0x600D),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001010),  # noqa: E501
    )
    # Source: lll
    # {
    #     ; limited gas because of the endless loop
    #     (delegatecall 0x10000 (+ 0x1000 $4) 0 0 0 0)
    # }
    contract_17 = pre.deploy_contract(  # noqa: F841
        code=Op.DELEGATECALL(
            gas=0x10000,
            address=Op.ADD(0x1000, Op.CALLDATALOAD(offset=0x4)),
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        storage={0: 2989},
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC),  # noqa: E501
    )
    pre[sender] = Account(balance=0x100000000000)

    expect_entries_: list[dict] = [
        {
            "indexes": {
                "data": [0, 1, 3, 4, 5, 9, 10, 11, 12, 13, 14, 15],
                "gas": -1,
                "value": -1,
            },
            "network": [">=Cancun"],
            "result": {contract_17: Account(storage={0: 2989})},
        },
        {
            "indexes": {"data": [2, 6, 7, 8, 16], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_17: Account(storage={0: 24589})},
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Bytes("693c6139") + Hash(0x0),
        Bytes("693c6139") + Hash(0x1),
        Bytes("693c6139") + Hash(0x2),
        Bytes("693c6139") + Hash(0x3),
        Bytes("693c6139") + Hash(0x4),
        Bytes("693c6139") + Hash(0x5),
        Bytes("693c6139") + Hash(0x6),
        Bytes("693c6139") + Hash(0x7),
        Bytes("693c6139") + Hash(0x8),
        Bytes("693c6139") + Hash(0x9),
        Bytes("693c6139") + Hash(0xA),
        Bytes("693c6139") + Hash(0xB),
        Bytes("693c6139") + Hash(0xC),
        Bytes("693c6139") + Hash(0xD),
        Bytes("693c6139") + Hash(0xE),
        Bytes("693c6139") + Hash(0xF),
        Bytes("693c6139") + Hash(0x10),
    ]
    tx_gas = [16777216]
    tx_value = [1]

    tx = Transaction(
        sender=sender,
        to=contract_17,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
