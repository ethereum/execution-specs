"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stRandom/randomStatetest150Filler.json
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
    ["tests/static/state_tests/stRandom/randomStatetest150Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.pre_alloc_mutable
def test_random_statetest150(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x4f3f701464972e74606d6ea82d4d3080599a0e79")
    sender = EOA(
        key=0xB1F4CBC3A50042184425A6F9E996D0910F7BA879457CE5DAC5C71E498AD3C005
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    pre[sender] = Account(balance=0xDE0B6B3A7640000)
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.JUMPI(
                pc=0x9,
                condition=Op.ISZERO(Op.SLOAD(key=Op.CALLDATALOAD(offset=0x0))),
            )
            + Op.STOP
            + Op.JUMPDEST
            + Op.SSTORE(
                key=Op.CALLDATALOAD(offset=0x0),
                value=Op.CALLDATALOAD(offset=0x20),
            )
        ),
        balance=46,
        nonce=0,
        address=coinbase,  # noqa: E501
    )
    # Source: raw bytecode
    contract = pre.deploy_contract(
        code=(
            Op.PUSH7[0x8254D76C6F24D4]
            + Op.DUP1
            + Op.LOG2(
                offset=0x62,
                size=0x3E,
                topic_1=0x20AE2688CF4B75842AC7265966F5F5CA,
                topic_2=0x77D83F3A46A1A6,
            )
            + Op.PUSH9[0xABA89067DC278E1F86]
            + Op.PUSH18[0x462DAE624AC683889038D26894AF02617C0]
            + Op.PUSH12[0x39C4988A5A60A12C0D9AD0CA]
            + Op.PUSH6[0x839C92F7C75C]
            + Op.PUSH11[0xD3D6A7B617AC7FBD41F5A2]
            + Op.SWAP4
            + Op.CALLDATALOAD(
                offset=0xCA6AD48748A94E31302254147FB3B5857568E516CB6E8AA2,
            )
            + Op.PUSH24[0xAF85D0E508DC17DC50E246130BE577CB59826ADC86AF6C10]
            + Op.PUSH32[
                0xD8A98F47CCCD9D22A867A43CD8AD77BBE8BB737AF5ACC0BE67FD7B054F7281E7  # noqa: E501
            ]
            + Op.PUSH18[0x891DC4AAD180996B9CB71C6016D0F6A9148C]
            + Op.PUSH24[0x5E57AC8456A883EEDC3182623898F32B5C83760465A2061C]
            + Op.PUSH23[0x52E785E7EEF7A97B0AA6D6C15B5C296BCF05EE2E9B87AA]
            + Op.PUSH1[0xB5]
            + Op.PUSH21[0x1B3F7D69A1DF03DF117B848B3A75F81C12DEE2244F]
            + Op.PUSH23[0xE56BB261E9C75FB5CCC769DB72BFAEADEE3F68CF22BBCA]
            + Op.PUSH7[0x5B0647AC74C140]
            + Op.SWAP8
            + Op.PUSH25[0xC71B73ED4ADAA2C6BA1C181B0747C27506478C403B3943129E]
            + Op.PUSH26[0x223E788BF8B81F60ABECB73BE035D03A8BBDFA112CD8CB2F7A10]
            + Op.PUSH6[0x250292740D2D]
            + Op.PUSH19[0x259B4D7E3EF844783DA8118B72912B9F96A61F]
            + Op.PUSH2[0x68F1]
            + Op.PUSH1[0xEF]
            + Op.PUSH10[0xD7DD3DFC7E4EF204766F]
            + Op.PUSH25[0x9CBAF2ABECEADCF5BDD8DDDFEF773F0A628AFDF3988861662B]
            + Op.PUSH24[0x882A5CEBFFC61E75F11835B109E81F7C915A91C13B09097B]
            + Op.PUSH26[0x2D3D59DE0EF5B0F00F95EA49860917656263925DA2FD6685359C]
            + Op.PUSH14[0x7E4C3C4D2001A30111DE14C56503]
            + Op.PUSH25[0x8453DF98A29B8715561B2C2021CF78E0CCC4701B192EBF67BB]
            + Op.PUSH16[0x522656788B3D21428B50A2FA16224D92]
            + Op.PUSH13[0xE2EA5944760D501BFA0774238C]
            + Op.PUSH4[0x51DD224B]
            + Op.PUSH21[0x3D3FC4D5A309166016A71B1C230FE9AFD647932471]
            + Op.PUSH15[0x71E3B27BDD3FB18CCCC42F6EC97312]
            + Op.SWAP16
            + Op.ISZERO(0x58435F45DA181AEB1608ED31713C33330AB4D2D4AF54DD92D1DF)
            + Op.CALL(
                gas=0x2AEC0540,
                address=0xA00C267DA6E57A9318A096C6333C4BCED51306DA,
                value=0x6B1D9A35,
                args_offset=0x1F,
                args_size=0x1D,
                ret_offset=0x14,
                ret_size=0x8,
            )
            + Op.PUSH13[0xFB040C16BD7C3761BDB86DD6BE]
            + Op.PUSH6[0x8D2AEFE15739]
            + Op.PUSH3[0x173936]
            + Op.PUSH4[0x769965A6]
            + Op.PUSH5[0x79176D702E]
            + Op.PUSH31[
                0x2D5697681AAC1BECCC55825241CD77551F39526CFA77838FAA9C4759AAFA5C  # noqa: E501
            ]
            + Op.PUSH5[0xDF5E919997]
            + Op.PUSH16[0x35F8298ACD398D1913C1FD2DDACBBEAC]
            + Op.PUSH29[
                0xC29DAEE12C057385808F19D07110F30CFD900A130B0A713468BCEAF423
            ]
            + Op.PUSH2[0x53AB]
            + Op.PUSH13[0x7BDC39CF86D0A5B03684624D18]
            + Op.PUSH21[0x73B42A2968F1128872724B3D42218DBAC11F5A9492]
            + Op.PUSH6[0x1F09A866F61A]
            + Op.PUSH19[0x535C373274618D5914163ABC7481BB7789394E]
            + Op.PUSH3[0xF247E7]
            + Op.DUP15
            + Op.OR(
                0x629B20A108E1CFBA0DB03FCDEE497EE2F8BCF78EF143,
                0x83AF55A5686926972AF7C6519658AEE40A564E3C2950F874DEF7A2110AF0526F,  # noqa: E501
            )
        ),
        nonce=0,
        address=Address("0xa00c267da6e57a9318a096c6333c4bced51306da"),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex(
            "70afe04f9b9074d39383f0718bb0b14ecdb6680c54b4c20ae65044c572a5c832c15f55e8"  # noqa: E501
            "c1b63ffbb7da41d4c8faa43f087b1960b54938bbdb14f35e3552723ad2053a3c74b98d03"  # noqa: E501
            "20f74bbe4ff06630f30e1caa6e13797a14d07bb94ae4972ce38da7aefa2ab07aedb81397"  # noqa: E501
            "137b698a63675aa8895c5b1207be9262507b0866acfa180cfbbdff5572fb9a74b245d118"  # noqa: E501
            "0e80a93b2dc5bcf891e1b84d6c66ab13b03e937d4268f4e9be0381417c1db9b7341c9912"  # noqa: E501
            "e685e38ee499f1fb82b027b84e01ef235f18b95b0bf567fcfcc5181f51c6dd0465d063d0"  # noqa: E501
            "f11f267ccd81aa8d4fda65e7e213e5ae4a6da0c6493209753a089323c5bfdde091556681"  # noqa: E501
            "b0648f59b8b2684d82a240f7d5b8eefd645e6320270660e960467877a8561129b7114a61"  # noqa: E501
            "7d36423905813b7dc594d88b0eb751ba946f54595f624b07da116f0971fc6e540a966364"  # noqa: E501
            "c8a1df698688b1ba91f9ac7a74f878a61c87ad3240d656c9ee80fd90d4f8c01ca89c8bc5"  # noqa: E501
            "37380df079ba8a2e6f2a3cbeb6bfb9687a7cc323f2a9eafd81789ae783355764b23354ba"  # noqa: E501
            "3f693c4d774ed6ab89da8846604172ad96ab938a4beff64adf9594812f491a0ba98e6f77"  # noqa: E501
            "d4c40454047c20cfb2625c43608dc26d032e6f8b53bfc1243fbd23a14c077e2071997635"  # noqa: E501
            "fdb2ffb317cd0e116f1ea7649dcf80ead9dea010cc4e456893f16d7c534f980d27c3312f"  # noqa: E501
            "34fbf5c8ba9b"
        ),
        gas_limit=2042667010,
        value=1816460087,
    )

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
