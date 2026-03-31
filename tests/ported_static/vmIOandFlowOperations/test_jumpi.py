"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
state_tests/VMTests/vmIOandFlowOperations/jumpiFiller.yml
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
    ["state_tests/VMTests/vmIOandFlowOperations/jumpiFiller.yml"],
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
            id="not-jump-hyperspace",
        ),
        pytest.param(
            3,
            0,
            0,
            id="not-jump-hyperspace",
        ),
        pytest.param(
            4,
            0,
            0,
            id="jump-stop-dest",
        ),
        pytest.param(
            5,
            0,
            0,
            id="not-jump-stop-dest",
        ),
        pytest.param(
            6,
            0,
            0,
            id="jump-hyperspace",
        ),
        pytest.param(
            7,
            0,
            0,
            id="not-jump-hyperspace",
        ),
        pytest.param(
            8,
            0,
            0,
            id="jump-not-jumpdest",
        ),
        pytest.param(
            9,
            0,
            0,
            id="endless-loop",
        ),
        pytest.param(
            10,
            0,
            0,
            id="jump-dest",
        ),
        pytest.param(
            11,
            0,
            0,
            id="jump-dest",
        ),
        pytest.param(
            12,
            0,
            0,
            id="jump-dynamic",
        ),
        pytest.param(
            13,
            0,
            0,
            id="not-jump-dynamic",
        ),
        pytest.param(
            14,
            0,
            0,
            id="jump-2-push",
        ),
        pytest.param(
            15,
            0,
            0,
            id="jump-2-push",
        ),
        pytest.param(
            16,
            0,
            0,
            id="jump-not-jumpdest",
        ),
        pytest.param(
            17,
            0,
            0,
            id="jump-not-jumpdest",
        ),
        pytest.param(
            18,
            0,
            0,
            id="jump-hyperspace",
        ),
        pytest.param(
            19,
            0,
            0,
            id="not-jump-hyperspace",
        ),
        pytest.param(
            20,
            0,
            0,
            id="jump-hyperspace",
        ),
        pytest.param(
            21,
            0,
            0,
            id="not-jump-hyperspace",
        ),
        pytest.param(
            22,
            0,
            0,
            id="jump-hyperspace",
        ),
        pytest.param(
            23,
            0,
            0,
            id="not-jump-hyperspace",
        ),
        pytest.param(
            24,
            0,
            0,
            id="jump-to-list",
        ),
        pytest.param(
            25,
            0,
            0,
            id="loop",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_jumpi(
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
    contract_2 = Address(0x0000000000000000000000000000000000000200)
    contract_3 = Address(0x0000000000000000000000000000000000000201)
    contract_4 = Address(0x0000000000000000000000000000000000001002)
    contract_5 = Address(0x0000000000000000000000000000000000000202)
    contract_6 = Address(0x0000000000000000000000000000000000001003)
    contract_7 = Address(0x0000000000000000000000000000000000000203)
    contract_8 = Address(0x0000000000000000000000000000000000001004)
    contract_9 = Address(0x0000000000000000000000000000000000001005)
    contract_10 = Address(0x0000000000000000000000000000000000001006)
    contract_11 = Address(0x0000000000000000000000000000000000001007)
    contract_12 = Address(0x0000000000000000000000000000000000001008)
    contract_13 = Address(0x0000000000000000000000000000000000000208)
    contract_14 = Address(0x0000000000000000000000000000000000001009)
    contract_15 = Address(0x000000000000000000000000000000000000100A)
    contract_16 = Address(0x000000000000000000000000000000000000100B)
    contract_17 = Address(0x000000000000000000000000000000000000100C)
    contract_18 = Address(0x000000000000000000000000000000000000100D)
    contract_19 = Address(0x000000000000000000000000000000000000020D)
    contract_20 = Address(0x000000000000000000000000000000000000100E)
    contract_21 = Address(0x000000000000000000000000000000000000020E)
    contract_22 = Address(0x000000000000000000000000000000000000100F)
    contract_23 = Address(0x000000000000000000000000000000000000020F)
    contract_24 = Address(0x0000000000000000000000000000000000000110)
    contract_25 = Address(0x0000000000000000000000000000000000000111)
    contract_26 = Address(0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC)
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
    #   (asm 0x01 0x10 0x20 mul jumpi jumpdest)
    # }
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x600D)
        + Op.JUMPI(pc=Op.MUL(0x20, 0x10), condition=0x1)
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
    # Source: lll
    # {
    #   [[0]] 0x600D
    #   (asm 0x00 0x10 0x20 mul jumpi jumpdest)
    # }
    contract_2 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x600D)
        + Op.JUMPI(pc=Op.MUL(0x20, 0x10), condition=0x0)
        + Op.JUMPDEST
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000000200),  # noqa: E501
    )
    # Source: lll
    # {
    #   [[0]] 0x600D
    #   (asm 0x00 0x10 0x20 mul jumpi jumpdest)
    # }
    contract_3 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x600D)
        + Op.JUMPI(pc=Op.MUL(0x20, 0x10), condition=0x0)
        + Op.JUMPDEST
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000000201),  # noqa: E501
    )
    # Source: raw
    # 0x6001600657005B61600D60005500
    contract_4 = pre.deploy_contract(  # noqa: F841
        code=Op.JUMPI(pc=0x6, condition=0x1)
        + Op.STOP
        + Op.JUMPDEST
        + Op.SSTORE(key=0x0, value=0x600D)
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001002),  # noqa: E501
    )
    # Source: raw
    # 0x6000600657005B61600D60005500
    contract_5 = pre.deploy_contract(  # noqa: F841
        code=Op.JUMPI(pc=0x6, condition=0x0)
        + Op.STOP
        + Op.JUMPDEST
        + Op.SSTORE(key=0x0, value=0x600D)
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000000202),  # noqa: E501
    )
    # Source: lll
    # {
    #   [[0]] 0x600D
    #   (asm 0xff 0x0fffffff jumpi)
    # }
    contract_6 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x600D)
        + Op.JUMPI(pc=0xFFFFFFF, condition=0xFF)
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001003),  # noqa: E501
    )
    # Source: lll
    # {
    #   [[0]] 0x600D
    #   (asm 0x00 0x0fffffff jumpi)
    # }
    contract_7 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x600D)
        + Op.JUMPI(pc=0xFFFFFFF, condition=0x0)
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000000203),  # noqa: E501
    )
    # Source: raw
    # 0x6023600160085760015b600255
    contract_8 = pre.deploy_contract(  # noqa: F841
        code=Op.PUSH1[0x23]
        + Op.JUMPI(pc=0x8, condition=0x1)
        + Op.PUSH1[0x1]
        + Op.JUMPDEST
        + Op.PUSH1[0x2]
        + Op.SSTORE,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001004),  # noqa: E501
    )
    # Source: raw
    # 0x61600D6000555B6006600657
    contract_9 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x600D)
        + Op.JUMPDEST
        + Op.JUMPI(pc=0x6, condition=0x6),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001005),  # noqa: E501
    )
    # Source: raw
    # 0x61600D6001600A5760FF5B600055
    contract_10 = pre.deploy_contract(  # noqa: F841
        code=Op.PUSH2[0x600D]
        + Op.JUMPI(pc=0xA, condition=0x1)
        + Op.PUSH1[0xFF]
        + Op.JUMPDEST
        + Op.PUSH1[0x0]
        + Op.SSTORE,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001006),  # noqa: E501
    )
    # Source: raw
    # 0x600B565B61600D600055005B6001600357
    contract_11 = pre.deploy_contract(  # noqa: F841
        code=Op.JUMP(pc=0xB)
        + Op.JUMPDEST
        + Op.SSTORE(key=0x0, value=0x600D)
        + Op.STOP
        + Op.JUMPDEST
        + Op.JUMPI(pc=0x3, condition=0x1),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001007),  # noqa: E501
    )
    # Source: raw
    # 0x6001600460050157005B61600D600055
    contract_12 = pre.deploy_contract(  # noqa: F841
        code=Op.JUMPI(pc=Op.ADD(0x5, 0x4), condition=0x1)
        + Op.STOP
        + Op.JUMPDEST
        + Op.SSTORE(key=0x0, value=0x600D),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001008),  # noqa: E501
    )
    # Source: raw
    # 0x6000600460050157005B61600D600055
    contract_13 = pre.deploy_contract(  # noqa: F841
        code=Op.JUMPI(pc=Op.ADD(0x5, 0x4), condition=0x0)
        + Op.STOP
        + Op.JUMPDEST
        + Op.SSTORE(key=0x0, value=0x600D),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000000208),  # noqa: E501
    )
    # Source: raw
    # 0x600160075700605B61600D600055
    contract_14 = pre.deploy_contract(  # noqa: F841
        code=Op.JUMPI(pc=0x7, condition=0x1)
        + Op.STOP
        + Op.PUSH1[0x5B]
        + Op.SSTORE(key=0x0, value=0x600D),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001009),  # noqa: E501
    )
    # Source: raw
    # 0x600160075700600161600D600055
    contract_15 = pre.deploy_contract(  # noqa: F841
        code=Op.JUMPI(pc=0x7, condition=0x1)
        + Op.STOP
        + Op.PUSH1[0x1]
        + Op.SSTORE(key=0x0, value=0x600D),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000100A),  # noqa: E501
    )
    # Source: raw
    # 0x61600D6000556001600D575A5B5A600155
    contract_16 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x600D)
        + Op.JUMPI(pc=0xD, condition=0x1)
        + Op.GAS
        + Op.JUMPDEST
        + Op.SSTORE(key=0x1, value=Op.GAS),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000100B),  # noqa: E501
    )
    # Source: raw
    # 0x61600D6000556001600B575A5B5A600155
    contract_17 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x600D)
        + Op.JUMPI(pc=0xB, condition=0x1)
        + Op.GAS
        + Op.JUMPDEST
        + Op.SSTORE(key=0x1, value=Op.GAS),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000100C),  # noqa: E501
    )
    # Source: raw
    # 0x60116801000000000000000D575b5b61600D600055
    contract_18 = pre.deploy_contract(  # noqa: F841
        code=Op.JUMPI(pc=0x1000000000000000D, condition=0x11)
        + Op.JUMPDEST * 2
        + Op.SSTORE(key=0x0, value=0x600D),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000100D),  # noqa: E501
    )
    # Source: raw
    # 0x60006801000000000000000D575b5b61600D600055
    contract_19 = pre.deploy_contract(  # noqa: F841
        code=Op.JUMPI(pc=0x1000000000000000D, condition=0x0)
        + Op.JUMPDEST * 2
        + Op.SSTORE(key=0x0, value=0x600D),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000020D),  # noqa: E501
    )
    # Source: raw
    # 0x6011640100000009575b5b61600D600055
    contract_20 = pre.deploy_contract(  # noqa: F841
        code=Op.JUMPI(pc=0x100000009, condition=0x11)
        + Op.JUMPDEST * 2
        + Op.SSTORE(key=0x0, value=0x600D),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000100E),  # noqa: E501
    )
    # Source: raw
    # 0x6000640100000009575b5b61600D600055
    contract_21 = pre.deploy_contract(  # noqa: F841
        code=Op.JUMPI(pc=0x100000009, condition=0x0)
        + Op.JUMPDEST * 2
        + Op.SSTORE(key=0x0, value=0x600D),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000020E),  # noqa: E501
    )
    # Source: lll
    # {
    #   @0 (- 0 1)
    #   (asm 1 0 mload jumpi 0x600D 0x00 sstore)
    # }
    contract_22 = pre.deploy_contract(  # noqa: F841
        code=Op.POP(Op.MLOAD(offset=0x0))
        + Op.POP(Op.SUB(0x0, 0x1))
        + Op.JUMPI(pc=Op.MLOAD(offset=0x0), condition=0x1)
        + Op.SSTORE(key=0x0, value=0x600D)
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000100F),  # noqa: E501
    )
    # Source: lll
    # {
    #   @0 (- 0 1)
    #   (asm 0 0 mload jumpi 0x600D 0x00 sstore)
    # }
    contract_23 = pre.deploy_contract(  # noqa: F841
        code=Op.POP(Op.MLOAD(offset=0x0))
        + Op.POP(Op.SUB(0x0, 0x1))
        + Op.JUMPI(pc=Op.MLOAD(offset=0x0), condition=0x0)
        + Op.SSTORE(key=0x0, value=0x600D)
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000020F),  # noqa: E501
    )
    # Source: raw
    # 0x6001600E575B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B61600D600055
    contract_24 = pre.deploy_contract(  # noqa: F841
        code=Op.JUMPI(pc=0xE, condition=0x1)
        + Op.JUMPDEST * 16
        + Op.SSTORE(key=0x0, value=0x600D),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000000110),  # noqa: E501
    )
    # Source: raw
    # 0x61600D60005560106000525B60016000510380600052600B57
    contract_25 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x600D)
        + Op.MSTORE(offset=0x0, value=0x10)
        + Op.JUMPDEST
        + Op.SUB(Op.MLOAD(offset=0x0), 0x1)
        + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.PUSH1[0xB]
        + Op.JUMPI,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000000111),  # noqa: E501
    )
    # Source: lll
    # {
    #     ; limited gas because of the endless loop
    #     (delegatecall 0x10000 $4 0 0 0 0)
    # }
    contract_26 = pre.deploy_contract(  # noqa: F841
        code=Op.DELEGATECALL(
            gas=0x10000,
            address=Op.CALLDATALOAD(offset=0x4),
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
                "data": [0, 1, 5, 6, 8, 9, 13, 14, 15, 16, 17, 18, 20, 22],
                "gas": -1,
                "value": -1,
            },
            "network": [">=Cancun"],
            "result": {contract_26: Account(storage={0: 2989})},
        },
        {
            "indexes": {
                "data": [2, 3, 4, 7, 10, 11, 12, 19, 21, 23, 24, 25],
                "gas": -1,
                "value": -1,
            },
            "network": [">=Cancun"],
            "result": {contract_26: Account(storage={0: 24589})},
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Bytes("693c6139") + Hash(contract_0, left_padding=True),
        Bytes("693c6139") + Hash(contract_1, left_padding=True),
        Bytes("693c6139") + Hash(contract_2, left_padding=True),
        Bytes("693c6139") + Hash(contract_3, left_padding=True),
        Bytes("693c6139") + Hash(contract_4, left_padding=True),
        Bytes("693c6139") + Hash(contract_5, left_padding=True),
        Bytes("693c6139") + Hash(contract_6, left_padding=True),
        Bytes("693c6139") + Hash(contract_7, left_padding=True),
        Bytes("693c6139") + Hash(contract_8, left_padding=True),
        Bytes("693c6139") + Hash(contract_9, left_padding=True),
        Bytes("693c6139") + Hash(contract_10, left_padding=True),
        Bytes("693c6139") + Hash(contract_11, left_padding=True),
        Bytes("693c6139") + Hash(contract_12, left_padding=True),
        Bytes("693c6139") + Hash(contract_13, left_padding=True),
        Bytes("693c6139") + Hash(contract_14, left_padding=True),
        Bytes("693c6139") + Hash(contract_15, left_padding=True),
        Bytes("693c6139") + Hash(contract_16, left_padding=True),
        Bytes("693c6139") + Hash(contract_17, left_padding=True),
        Bytes("693c6139") + Hash(contract_18, left_padding=True),
        Bytes("693c6139") + Hash(contract_19, left_padding=True),
        Bytes("693c6139") + Hash(contract_20, left_padding=True),
        Bytes("693c6139") + Hash(contract_21, left_padding=True),
        Bytes("693c6139") + Hash(contract_22, left_padding=True),
        Bytes("693c6139") + Hash(contract_23, left_padding=True),
        Bytes("693c6139") + Hash(contract_24, left_padding=True),
        Bytes("693c6139") + Hash(contract_25, left_padding=True),
    ]
    tx_gas = [16777216]
    tx_value = [1]

    tx = Transaction(
        sender=sender,
        to=contract_26,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
