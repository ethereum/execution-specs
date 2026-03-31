"""
CALL precompiles during init code of CREATE2 contract.

Ported from:
state_tests/stCreate2/create2callPrecompilesFiller.json
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
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stCreate2/create2callPrecompilesFiller.json"],
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
        pytest.param(
            6,
            0,
            0,
            id="d6",
        ),
        pytest.param(
            7,
            0,
            0,
            id="d7",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_create2call_precompiles(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """CALL precompiles during init code of CREATE2 contract ."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0xADDF5374FCE5EDBC8E2A8697C15331677E6EBF0B)
    contract_1 = Address(0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B)
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000000000,
    )

    pre[sender] = Account(balance=0xDE0B6B3A7640000)
    # Source: lll
    # {(MSTORE 0 (CALLDATALOAD 0)) (MSTORE 32 (CALLDATALOAD 32)) (MSTORE 64 (CALLDATALOAD 64)) (MSTORE 96 (CALLDATALOAD 96)) [[0]](CALLCODE 500000 6 0 0 128 200 64)  [[1]] (MLOAD 200)  [[2]] (MLOAD 232) }  # noqa: E501
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=Op.CALLDATALOAD(offset=0x0))
        + Op.MSTORE(offset=0x20, value=Op.CALLDATALOAD(offset=0x20))
        + Op.MSTORE(offset=0x40, value=Op.CALLDATALOAD(offset=0x40))
        + Op.MSTORE(offset=0x60, value=Op.CALLDATALOAD(offset=0x60))
        + Op.SSTORE(
            key=0x0,
            value=Op.CALLCODE(
                gas=0x7A120,
                address=0x6,
                value=0x0,
                args_offset=0x0,
                args_size=0x80,
                ret_offset=0xC8,
                ret_size=0x40,
            ),
        )
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0xC8))
        + Op.SSTORE(key=0x2, value=Op.MLOAD(offset=0xE8))
        + Op.STOP,
        nonce=0,
        address=Address(0xADDF5374FCE5EDBC8E2A8697C15331677E6EBF0B),  # noqa: E501
    )
    # Source: lll
    # {(MSTORE 0 (CALLDATALOAD 0)) (MSTORE 32 (CALLDATALOAD 32)) (MSTORE 64 (CALLDATALOAD 64)) (MSTORE 96 (CALLDATALOAD 96))  (MSTORE 128 (CALLDATALOAD 128)) (MSTORE 160 (CALLDATALOAD 160)) (MSTORE 192 (CALLDATALOAD 192)) [[0]](CALLCODE 500000 6 0 0 128 300 64)  [[1]](CALLCODE 500000 7 0 128 96 400 64) [[10]] (MLOAD 300)  [[11]] (MLOAD 332) [[20]] (MLOAD 400)  [[21]] (MLOAD 432) [[2]] (EQ (SLOAD 10) (SLOAD 20)) [[3]] (EQ (SLOAD 11) (SLOAD 21))}  # noqa: E501
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=Op.CALLDATALOAD(offset=0x0))
        + Op.MSTORE(offset=0x20, value=Op.CALLDATALOAD(offset=0x20))
        + Op.MSTORE(offset=0x40, value=Op.CALLDATALOAD(offset=0x40))
        + Op.MSTORE(offset=0x60, value=Op.CALLDATALOAD(offset=0x60))
        + Op.MSTORE(offset=0x80, value=Op.CALLDATALOAD(offset=0x80))
        + Op.MSTORE(offset=0xA0, value=Op.CALLDATALOAD(offset=0xA0))
        + Op.MSTORE(offset=0xC0, value=Op.CALLDATALOAD(offset=0xC0))
        + Op.SSTORE(
            key=0x0,
            value=Op.CALLCODE(
                gas=0x7A120,
                address=0x6,
                value=0x0,
                args_offset=0x0,
                args_size=0x80,
                ret_offset=0x12C,
                ret_size=0x40,
            ),
        )
        + Op.SSTORE(
            key=0x1,
            value=Op.CALLCODE(
                gas=0x7A120,
                address=0x7,
                value=0x0,
                args_offset=0x80,
                args_size=0x60,
                ret_offset=0x190,
                ret_size=0x40,
            ),
        )
        + Op.SSTORE(key=0xA, value=Op.MLOAD(offset=0x12C))
        + Op.SSTORE(key=0xB, value=Op.MLOAD(offset=0x14C))
        + Op.SSTORE(key=0x14, value=Op.MLOAD(offset=0x190))
        + Op.SSTORE(key=0x15, value=Op.MLOAD(offset=0x1B0))
        + Op.SSTORE(
            key=0x2, value=Op.EQ(Op.SLOAD(key=0xA), Op.SLOAD(key=0x14))
        )
        + Op.SSTORE(
            key=0x3, value=Op.EQ(Op.SLOAD(key=0xB), Op.SLOAD(key=0x15))
        )
        + Op.STOP,
        nonce=0,
        address=Address(0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                Address(0xF68E26002DB0F9CA9B54367C57C25E474C581622): Account(
                    storage={
                        0: 0xA94F5374FCE5EDBC8E2A8697C15331677E6EBF0B,
                        1: 1,
                        2: 1,
                    },
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                Address(0x3B9EA59B92545BEB727022289665CF38FA462BAE): Account(
                    storage={
                        0: 0xCB39B3BDE22925B2F931111130C774761D8895E0E08437C9B396C1E97D10F34D,  # noqa: E501
                        2: 1,
                    },
                ),
            },
        },
        {
            "indexes": {"data": 2, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                Address(0x7525F19E2970539FD2897357777A4C275175BCF5): Account(
                    storage={
                        0: 0x9C1185A5C5E9FC54612808977EE8F548B2258D31,
                        2: 1,
                    },
                ),
            },
        },
        {
            "indexes": {"data": 3, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                Address(0x0EE431DB7C48FC10A9A56C909BFEFA87661442FB): Account(
                    storage={0: 0xF34578907F, 2: 1}
                ),
            },
        },
        {
            "indexes": {"data": 4, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                Address(0xBBD394930B408DA783EE071CED240ECE997BC8B2): Account(
                    storage={
                        1: 1,
                        2: 0x162EAD82CADEFAEAF6E9283248FDF2F2845F6396F6F17C4D5A39F820B6F6B5F9,  # noqa: E501
                    },
                ),
            },
        },
        {
            "indexes": {"data": 5, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                Address(0x2E3EC33A50ED32C2FCBEF07A1BAB8643DB4DC670): Account(
                    storage={0: 1, 2: 0}
                ),
            },
        },
        {
            "indexes": {"data": 6, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                Address(0xAA0AB87AA0E27E22E21671040C11F3537CDC7B3E): Account(
                    storage={
                        0: 1,
                        1: 0x1F4D1D80177B1377743D1901F70D7389BE7F7A35A35BFD234A8AAEE615B88C49,  # noqa: E501
                        2: 0x18683193AE021A2F8920FED186CDE5D9B1365116865281CCF884C1F28B1DF8F,  # noqa: E501
                    },
                ),
            },
        },
        {
            "indexes": {"data": 7, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                Address(0xAB7CF4E4980432E892FA512EC2B9E8532C23AC15): Account(
                    storage={
                        0: 1,
                        1: 1,
                        2: 1,
                        3: 1,
                        10: 0x1DE49A4B0233273BBA8146AF82042D004F2085EC982397DB0D97DA17204CC286,  # noqa: E501
                        11: 0x217327FFC463919BEF80CC166D09C6172639D8589799928761BCD9F22C903D4,  # noqa: E501
                        20: 0x1DE49A4B0233273BBA8146AF82042D004F2085EC982397DB0D97DA17204CC286,  # noqa: E501
                        21: 0x217327FFC463919BEF80CC166D09C6172639D8589799928761BCD9F22C903D4,  # noqa: E501
                    },
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Op.PUSH1[0x0]
        + Op.PUSH1[0x9B]
        + Op.CODECOPY(dest_offset=0x0, offset=0x13, size=Op.DUP1)
        + Op.PUSH1[0x0] * 2
        + Op.POP(Op.CREATE2)
        + Op.STOP * 2
        + Op.INVALID
        + Op.MSTORE(
            offset=0x0,
            value=0x18C547E4F7B0F325AD1E56F57E26C745B09A3E503D86E00E5255FF7F715D3D1C,  # noqa: E501
        )
        + Op.MSTORE(offset=0x20, value=0x1C)
        + Op.MSTORE(
            offset=0x40,
            value=0x73B1693892219D736CABA55BDB67216E485557EA6B6AF75F37096C9AA6A5A75F,  # noqa: E501
        )
        + Op.MSTORE(
            offset=0x60,
            value=0xEEB940B1D03B21E36B0E47E79769F095FE2AB855BD91E3A38756B7D75A9C4549,  # noqa: E501
        )
        + Op.SSTORE(
            key=0x2,
            value=Op.CALL(
                gas=0x493E0,
                address=0x1,
                value=0x0,
                args_offset=0x0,
                args_size=0x80,
                ret_offset=0x80,
                ret_size=0x20,
            ),
        )
        + Op.SSTORE(
            key=0x0, value=Op.MOD(Op.MLOAD(offset=0x80), Op.EXP(0x2, 0xA0))
        )
        + Op.SSTORE(key=0x1, value=Op.EQ(Op.ORIGIN, Op.SLOAD(key=0x0)))
        + Op.STOP * 2,
        Op.PUSH1[0x0]
        + Op.PUSH1[0x24]
        + Op.CODECOPY(dest_offset=0x0, offset=0x13, size=Op.DUP1)
        + Op.PUSH1[0x0] * 2
        + Op.POP(Op.CREATE2)
        + Op.STOP * 2
        + Op.INVALID
        + Op.MSTORE(offset=0x5, value=0xF34578907F)
        + Op.SSTORE(
            key=0x2,
            value=Op.CALL(
                gas=0x1F4,
                address=0x2,
                value=0x0,
                args_offset=0x0,
                args_size=0x25,
                ret_offset=0x0,
                ret_size=0x20,
            ),
        )
        + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
        + Op.STOP * 2,
        Op.PUSH1[0x0]
        + Op.PUSH1[0x1B]
        + Op.CODECOPY(dest_offset=0x0, offset=0x13, size=Op.DUP1)
        + Op.PUSH1[0x0] * 2
        + Op.POP(Op.CREATE2)
        + Op.STOP * 2
        + Op.INVALID
        + Op.SSTORE(
            key=0x2,
            value=Op.CALL(
                gas=0x258,
                address=0x3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x20,
            ),
        )
        + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
        + Op.STOP * 2,
        Op.PUSH1[0x0]
        + Op.PUSH1[0x24]
        + Op.CODECOPY(dest_offset=0x0, offset=0x13, size=Op.DUP1)
        + Op.PUSH1[0x0] * 2
        + Op.POP(Op.CREATE2)
        + Op.STOP * 2
        + Op.INVALID
        + Op.MSTORE(offset=0x0, value=0xF34578907F)
        + Op.SSTORE(
            key=0x2,
            value=Op.CALL(
                gas=0x1F4,
                address=0x4,
                value=0x0,
                args_offset=0x0,
                args_size=0x25,
                ret_offset=0x0,
                ret_size=0x20,
            ),
        )
        + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
        + Op.STOP * 2,
        Op.PUSH1[0x0]
        + Op.PUSH1[0x96]
        + Op.CODECOPY(dest_offset=0x0, offset=0x13, size=Op.DUP1)
        + Op.PUSH1[0x0] * 2
        + Op.POP(Op.CREATE2)
        + Op.STOP * 2
        + Op.INVALID
        + Op.MSTORE(offset=0x0, value=0x1)
        + Op.MSTORE(offset=0x20, value=0x20)
        + Op.MSTORE(offset=0x40, value=0x20)
        + Op.MSTORE(
            offset=0x60,
            value=0x3FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC,  # noqa: E501
        )
        + Op.MSTORE(
            offset=0x80,
            value=0x2EFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC,  # noqa: E501
        )
        + Op.MSTORE(
            offset=0x96,
            value=0x2F00000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
        )
        + Op.SSTORE(
            key=0x1,
            value=Op.CALLCODE(
                gas=Op.GAS,
                address=0x5,
                value=0x0,
                args_offset=0x0,
                args_size=0x97,
                ret_offset=0x3E8,
                ret_size=0x20,
            ),
        )
        + Op.SSTORE(key=0x2, value=Op.MLOAD(offset=0x3E8))
        + Op.STOP * 2,
        Op.PUSH1[0x0]
        + Op.PUSH1[0x22]
        + Op.CODECOPY(dest_offset=0x0, offset=0x13, size=Op.DUP1)
        + Op.PUSH1[0x0] * 2
        + Op.POP(Op.CREATE2)
        + Op.STOP * 2
        + Op.INVALID
        + Op.MSTORE(offset=0x0, value=0x1)
        + Op.SSTORE(
            key=0x2,
            value=Op.CALL(
                gas=0x927C0,
                address=0x6,
                value=0x0,
                args_offset=0x0,
                args_size=0x100,
                ret_offset=0x0,
                ret_size=0x20,
            ),
        )
        + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
        + Op.STOP * 2,
        Op.PUSH1[0x0]
        + Op.PUSH1[0xB7]
        + Op.CODECOPY(dest_offset=0x0, offset=0x13, size=Op.DUP1)
        + Op.PUSH1[0x0] * 2
        + Op.POP(Op.CREATE2)
        + Op.STOP * 2
        + Op.INVALID
        + Op.MSTORE(
            offset=0x0,
            value=0xF25929BCB43D5A57391564615C9E70A992B10EAFA4DB109709649CF48C50DD2,  # noqa: E501
        )
        + Op.MSTORE(
            offset=0x20,
            value=0x16DA2F5CB6BE7A0AA72C440C53C9BBDFEC6C36C7D515536431B3A865468ACBBA,  # noqa: E501
        )
        + Op.MSTORE(
            offset=0x40,
            value=0x1DE49A4B0233273BBA8146AF82042D004F2085EC982397DB0D97DA17204CC286,  # noqa: E501
        )
        + Op.MSTORE(
            offset=0x60,
            value=0x217327FFC463919BEF80CC166D09C6172639D8589799928761BCD9F22C903D4,  # noqa: E501
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x7A120,
                address=contract_0,
                value=0x0,
                args_offset=0x0,
                args_size=0x80,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.STOP * 2,
        Op.PUSH1[0x0]
        + Op.PUSH1[0xC6]
        + Op.CODECOPY(dest_offset=0x0, offset=0x13, size=Op.DUP1)
        + Op.PUSH1[0x0] * 2
        + Op.POP(Op.CREATE2)
        + Op.STOP * 2
        + Op.INVALID
        + Op.MSTORE(
            offset=0x0,
            value=0x1DE49A4B0233273BBA8146AF82042D004F2085EC982397DB0D97DA17204CC286,  # noqa: E501
        )
        + Op.MSTORE(
            offset=0x20,
            value=0x217327FFC463919BEF80CC166D09C6172639D8589799928761BCD9F22C903D4,  # noqa: E501
        )
        + Op.MSTORE(offset=0x40, value=0x0)
        + Op.MSTORE(offset=0x60, value=0x0)
        + Op.MSTORE(
            offset=0x80,
            value=0x1DE49A4B0233273BBA8146AF82042D004F2085EC982397DB0D97DA17204CC286,  # noqa: E501
        )
        + Op.MSTORE(
            offset=0xA0,
            value=0x217327FFC463919BEF80CC166D09C6172639D8589799928761BCD9F22C903D4,  # noqa: E501
        )
        + Op.MSTORE(offset=0xC0, value=0x1)
        + Op.POP(
            Op.CALLCODE(
                gas=0x7A120,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0xE0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.STOP * 2,
    ]
    tx_gas = [15000000]
    tx_value = [1]

    tx = Transaction(
        sender=sender,
        to=None,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
