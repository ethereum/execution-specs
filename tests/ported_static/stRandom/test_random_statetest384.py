"""
Ori Pomerantz   qbzzt1@gmail.com.

Ported from:
tests/static/state_tests/stRandom/randomStatetest384Filler.yml
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
    ["tests/static/state_tests/stRandom/randomStatetest384Filler.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_random_statetest384(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Ori Pomerantz   qbzzt1@gmail.com."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x04DC42D61413D4DED993826AC4D6ED7A4A970C60335D2B285C60A4274E792FF1
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=71794957647893862,
    )

    # Source: raw bytecode
    contract = pre.deploy_contract(
        code=(
            Op.EXTCODESIZE(
                address=0x6675A4758D443DBFF535F034A4EDA729A6FFC1E59F674E0C55,
            )
            + Op.PUSH6[0x5D7974272AC7]
            + Op.AND(0xFFFF, 0x18CE2014249172572ED5EAC0B9D2E4)
            + Op.SWAP1
            + Op.LOG0(offset=Op.AND, size=0xFFFF)
            + Op.CALLER
            + Op.GT
            + Op.BASEFEE
            + Op.EXTCODESIZE(
                address=Op.EQ(
                    0x513376BC288AA1FDB973C149CD,
                    Op.DELEGATECALL(
                        gas=Op.GAS,
                        address=0x4D84673D975D1811374A239EF14EE26532D643CC4DD6E9115E28815562C2EB94,  # noqa: E501
                        args_offset=0xAD13,
                        args_size=0xA9BB,
                        ret_offset=0x9FE1,
                        ret_size=0xC0CD,
                    ),
                ),
            )
            + Op.PUSH25[0x89CC6512F8D604E5D0656C17F2D45B916DF6816A1999719F2B]
            + Op.JUMPI(
                pc=Op.ADD(0x8, Op.PC),
                condition=Op.AND(0x1, 0xD521394F07100138B341F1DEBC06C3FB3CBC),
            )
            + Op.POP(0xCB)
            + Op.JUMPDEST
            + Op.PUSH19[0x27E1DC4C54400E52AB133F162C6DF107151D11]
            + Op.GASLIMIT
            + Op.SWAP4
            + Op.SWAP5
            + Op.GASLIMIT
            + Op.DUP1
            + Op.PUSH31[
                0x5153417E8FF00D138F0DFFC0CD79CED2ECECD6F0DCE826302E4129CB6C37AB  # noqa: E501
            ]
            + Op.NUMBER
            + Op.COINBASE
            + Op.JUMPDEST
            + Op.AND(
                0xFFFF,
                Op.DELEGATECALL(
                    gas=Op.GAS,
                    address=0xA5D352916626FE6BE4AA6EF0E7634DB7909FD79752E5BCB504B358D36AF70849,  # noqa: E501
                    args_offset=0xC30,
                    args_size=0x52A9,
                    ret_offset=0x73CE,
                    ret_size=0x45C1,
                ),
            )
            + Op.SWAP1
            + Op.PUSH2[0xFFFF]
            + Op.AND
            + Op.LOG2
            + Op.MLOAD(offset=Op.AND(0xFFFF, 0xE900F727806828F5EE6088EBF8))
            + Op.PUSH17[0x15C1269FA9F5387AB7387A81F51905640]
            + Op.SWAP9
            + Op.PUSH1[0x1F]
            + Op.SWAP5
            + Op.PUSH18[0xB46EB2F2D66EE0B4C6845455E9C5EEFF0218]
            + Op.SMOD(
                0x66120B1A7A97C93A6A04BD493F4A,
                0xBAE1D66F6CB6213C6CE69859F1046AE4CB5E5B743AB7,
            )
            + Op.SWAP7
            + Op.RETURNDATASIZE
            + Op.SIGNEXTEND
            + Op.PUSH10[0x471B70DEC306FA6142CE]
            + Op.SWAP13
            + Op.MOD(
                Op.SDIV(
                    0xA04EA7E0BD9D9CDA29962B,
                    Op.BLOCKHASH(block_number=Op.SUB(Op.NUMBER, Op.AND)),
                ),
                0xFF,
            )
            + Op.PUSH19[0x46CE83AB26762D5E2CFB614AA2394AD1D70EA9]
            + Op.CODESIZE
            + Op.DUP6
            + Op.PUSH12[0x938D5C3FF280BF7EFDA95E66]
            + Op.DUP11
            + Op.PUSH17[0x149AFA7A18BF9C2D796DE03773E0D35C9A]
            + Op.NOT(
                0x8E0E968BA16F3AD59D6442DDBDB9E537908DB1F791BB3F17B33A1433340107,  # noqa: E501
            )
            + Op.PUSH2[0xA168]
            + Op.SWAP13
            + Op.PUSH28[
                0x413ED4A9B16E7D66A17B07730188A08FA9E6148100F0311EA269ECC5
            ]
            + Op.DUP9
            + Op.PUSH1[0x7D]
            + Op.PUSH32[
                0xCBFFF9F42E22612E938809AF2674B0CEDC8548F47EE642097C0C4ABC9BF7C76B  # noqa: E501
            ]
            + Op.SWAP7
            + Op.PUSH25[0x996410D0BF28E5E3E1B35B37FFCE70E346E013D5345494D476]
            + Op.SWAP1
            + Op.CALLER
            + Op.TIMESTAMP
            + Op.DELEGATECALL(
                gas=Op.GAS,
                address=0x1396B439A0049676213FD1FF8B75232DBD2117C0C5DCC184D76E2534EA9628AC,  # noqa: E501
                args_offset=0xF195,
                args_size=0x74FD,
                ret_offset=0xABAE,
                ret_size=0x7717,
            )
            + Op.DUP7
            + Op.GASPRICE
            + Op.SWAP8
            + Op.PUSH2[0xFFFF]
            + Op.AND
            + Op.SWAP1
            + Op.LOG0(offset=Op.AND, size=0xFFFF)
            + Op.MSTORE8(
                offset=Op.AND(0xFFFF, Op.EQ),
                value=0x486085A7047BD1ACAB7C048C2AE5A07A9E25934021CFAF0651EFBD393B7214,  # noqa: E501
            )
            + Op.PUSH2[0xFFFF]
            + Op.AND
            + Op.SWAP1
            + Op.PUSH2[0xFFFF]
            + Op.AND
            + Op.LOG1
            + Op.EQ(Op.DIV(Op.ADDRESS, Op.DUP7), 0x84ED962562151D0B903FB2)
            + Op.DIV
            + Op.PUSH20[0x380357280D5DBC434298AC45559FC2855C0D2A04]
            + Op.GAS
            + Op.PUSH7[0xAF59655ED483A0]
            + Op.SHL(
                0x5F1536B1893659FBB9FFA023722BEB2F24B5693BE6B572737FED,
                Op.BLOCKHASH(
                    block_number=Op.SUB(
                        Op.NUMBER,
                        Op.AND(0xFF, Op.BALANCE(address=Op.PC)),
                    ),
                ),
            )
            + Op.SWAP14
            + Op.EXP
            + Op.PUSH5[0x6F7A2658B5]
            + Op.DUP12
            + Op.JUMPDEST
            + Op.COINBASE
            + Op.PUSH19[0x20E684F471111724A4F72553B4FDC9593AE22C]
            + Op.SWAP7
            + Op.SWAP6
            + Op.SWAP10
            + Op.CALL(
                gas=Op.GAS,
                address=0x39DBE091B64B8BE6A557A93BF2C25DD042E8C8FEA4DB3BD8EE5BE3EABDE2835E,  # noqa: E501
                value=0x8FE0,
                args_offset=0xF3F6,
                args_size=0x1991,
                ret_offset=0x5AD4,
                ret_size=0xA631,
            )
            + Op.SSTORE(key=0x0, value=Op.SDIV)
            + Op.PUSH1[0x1]
            + Op.SSTORE
            + Op.PUSH1[0x2]
            + Op.SSTORE
            + Op.PUSH1[0x3]
            + Op.SSTORE
            + Op.PUSH1[0x4]
            + Op.SSTORE
            + Op.PUSH1[0x5]
            + Op.SSTORE
            + Op.PUSH1[0x6]
            + Op.SSTORE
            + Op.PUSH1[0x7]
            + Op.SSTORE
            + Op.PUSH1[0x8]
            + Op.SSTORE
            + Op.PUSH1[0x9]
            + Op.SSTORE
            + Op.PUSH1[0xA]
            + Op.SSTORE
            + Op.PUSH1[0xB]
            + Op.SSTORE
            + Op.PUSH1[0xC]
            + Op.SSTORE
            + Op.PUSH1[0xD]
            + Op.SSTORE
            + Op.PUSH1[0xE]
            + Op.SSTORE
            + Op.PUSH1[0xF]
            + Op.SSTORE
            + Op.PUSH1[0x10]
            + Op.SSTORE
            + Op.PUSH1[0x11]
            + Op.SSTORE
            + Op.PUSH1[0x12]
            + Op.SSTORE
            + Op.PUSH1[0x13]
            + Op.SSTORE
            + Op.PUSH1[0x14]
            + Op.SSTORE
            + Op.PUSH1[0x15]
            + Op.SSTORE
            + Op.PUSH1[0x16]
            + Op.SSTORE
            + Op.PUSH1[0x17]
            + Op.SSTORE
            + Op.PUSH1[0x18]
            + Op.SSTORE
            + Op.PUSH1[0x19]
            + Op.SSTORE
            + Op.PUSH1[0x1A]
            + Op.SSTORE
            + Op.PUSH1[0x1B]
            + Op.SSTORE
            + Op.PUSH1[0x1C]
            + Op.SSTORE
            + Op.PUSH1[0x1D]
            + Op.SSTORE
            + Op.PUSH1[0x1E]
            + Op.SSTORE
            + Op.RETURN(offset=0xC065, size=0x2739)
        ),
        balance=0xDE0B6B3A7640000,
        address=Address("0x14ceed78f6e86eead0a39e3f5c3481c7c233e8ea"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x3635C9ADC5DEA00000, nonce=1)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        1: 0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA,
                        2: 0x938D5C3FF280BF7EFDA95E66,
                        3: 0x6F7A2658B5,
                        4: 0x9582CED6097AE8D75CB9CAC205753DD88202D5D36541F1B1BB9C1446739E0D01,  # noqa: E501
                        5: 0xF400CA,
                        7: 0x20E684F471111724A4F72553B4FDC9593AE22C,
                        8: 100,
                        9: 0x413ED4A9B16E7D66A17B07730188A08FA9E6148100F0311EA269ECC5,  # noqa: E501
                        10: 0x380357280D5DBC434298AC45559FC2855C0D2A04,
                        11: 0xFF71F169745E90C52A629BBD2242461AC86F724E086E44C0E84CC5EBCCCBFEF8,  # noqa: E501
                        12: 0x149AFA7A18BF9C2D796DE03773E0D35C9A,
                        13: 0xCBFFF9F42E22612E938809AF2674B0CEDC8548F47EE642097C0C4ABC9BF7C76B,  # noqa: E501
                        14: 0x938D5C3FF280BF7EFDA95E66,
                        15: 10,
                        16: 996,
                        19: 0xB46EB2F2D66EE0B4C6845455E9C5EEFF0218,
                        20: 1,
                        21: 10,
                        23: 41320,
                        24: 0xFF112233445566,
                        25: 0x66120B1A7A97C93A6A04BD493F4A,
                        26: 0x27E1DC4C54400E52AB133F162C6DF107151D11,
                        27: 0x89CC6512F8D604E5D0656C17F2D45B916DF6816A1999719F2B,  # noqa: E501
                        29: 0xFF112233445566,
                        30: 0x471B70DEC306FA6142CE,
                    },
                    code=bytes.fromhex(
                        "786675a4758d443dbff535f034a4eda729a6ffc1e59f674e0c553b655d7974272ac76e18ce2014249172572ed5eac0b9d2e461ffff169061ffff16a033114861c0cd619fe161a9bb61ad137f4d84673d975d1811374a239ef14ee26532d643cc4dd6e9115e28815562c2eb945af46c513376bc288aa1fdb973c149cd143b7889cc6512f8d604e5d0656c17f2d45b916df6816a1999719f2b71d521394f07100138b341f1debc06c3fb3cbc600116586008015760cb505b7227e1dc4c54400e52ab133f162c6df107151d1145939445807e5153417e8ff00d138f0dffc0cd79ced2ececd6f0dce826302e4129cb6c37ab43415b6145c16173ce6152a9610c307fa5d352916626fe6be4aa6ef0e7634db7909fd79752e5bcb504b358d36af708495af461ffff169061ffff16a26ce900f727806828f5ee6088ebf861ffff165170015c1269fa9f5387ab7387a81f5190564098601f9471b46eb2f2d66ee0b4c6845455e9c5eeff021875bae1d66f6cb6213c6ce69859f1046ae4cb5e5b743ab76d66120b1a7a97c93a6a04bd493f4a07963d0b69471b70dec306fa6142ce9c60ff164303406aa04ea7e0bd9d9cda29962b05067246ce83ab26762d5e2cfb614aa2394ad1d70ea938856b938d5c3ff280bf7efda95e668a70149afa7a18bf9c2d796de03773e0d35c9a7e8e0e968ba16f3ad59d6442ddbdb9e537908db1f791bb3f17b33a14333401071961a1689c7b413ed4a9b16e7d66a17b07730188a08fa9e6148100f0311ea269ecc588607d7fcbfff9f42e22612e938809af2674b0cedc8548f47ee642097c0c4abc9bf7c76b9678996410d0bf28e5e3e1b35b37ffce70e346e013d5345494d47690334261771761abae6174fd61f1957f1396b439a0049676213fd1ff8b75232dbd2117c0c5dcc184d76e2534ea9628ac5af4863a9761ffff169061ffff16a07e486085a7047bd1acab7c048c2ae5a07a9e25934021cfaf0651efbd393b72141461ffff165361ffff169061ffff16a16a84ed962562151d0b903fb2863004140473380357280d5dbc434298ac45559fc2855c0d2a045a66af59655ed483a0583160ff16430340795f1536b1893659fbb9ffa023722beb2f24b5693be6b572737fed1b9d0a646f7a2658b58b5b417220e684f471111724a4f72553b4fdc9593ae22c96959961a631615ad461199161f3f6618fe07f39dbe091b64b8be6a557a93bf2c25dd042e8c8fea4db3bd8ee5be3eabde2835e5af105600055600155600255600355600455600555600655600755600855600955600a55600b55600c55600d55600e55600f55601055601155601255601355601455601555601655601755601855601955601a55601b55601c55601d55601e5561273961c065f3"  # noqa: E501
                    ),
                )
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, 0, 0, 0, fork)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=16777216,
        gas_price=100,
        nonce=1,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
