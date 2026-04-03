"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
state_tests/VMTests/vmArithmeticTest/expPower256Filler.yml
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
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/VMTests/vmArithmeticTest/expPower256Filler.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_exp_power256(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Ori Pomerantz qbzzt1@gmail."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0x40AC0FC28C27E961EE46EC43355A094DE205856EDBD4654CF2577C2608D4EC1E
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
    #     (def 'storageJump 0x10)
    #
    #     (def 'calc (n) {
    #          [[(* storageJump n)]] (exp 256 n)
    #          [[(+ (* storageJump n) 1)]] (exp 255 n)
    #          [[(+ (* storageJump n) 2)]] (exp 257 n)
    #       }
    #     )
    #
    #     (calc 0)
    #     (calc 1)
    #     (calc 2)
    #     (calc 3)
    #     (calc 4)
    #     (calc 5)
    #     (calc 6)
    #     (calc 7)
    #     (calc 8)
    #     (calc 9)
    #     (calc 10)
    #     (calc 11)
    #     (calc 12)
    #     (calc 13)
    #     (calc 14)
    #     (calc 15)
    #     (calc 16)
    #     (calc 17)
    #     (calc 18)
    #     (calc 19)
    # ... (15 more lines)
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=Op.MUL(0x10, 0x0), value=Op.EXP(0x100, 0x0))
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0x0), 0x1), value=Op.EXP(0xFF, 0x0)
        )
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0x0), 0x2), value=Op.EXP(0x101, 0x0)
        )
        + Op.SSTORE(key=Op.MUL(0x10, 0x1), value=Op.EXP(0x100, 0x1))
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0x1), 0x1), value=Op.EXP(0xFF, 0x1)
        )
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0x1), 0x2), value=Op.EXP(0x101, 0x1)
        )
        + Op.SSTORE(key=Op.MUL(0x10, 0x2), value=Op.EXP(0x100, 0x2))
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0x2), 0x1), value=Op.EXP(0xFF, 0x2)
        )
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0x2), 0x2), value=Op.EXP(0x101, 0x2)
        )
        + Op.SSTORE(key=Op.MUL(0x10, 0x3), value=Op.EXP(0x100, 0x3))
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0x3), 0x1), value=Op.EXP(0xFF, 0x3)
        )
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0x3), 0x2), value=Op.EXP(0x101, 0x3)
        )
        + Op.SSTORE(key=Op.MUL(0x10, 0x4), value=Op.EXP(0x100, 0x4))
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0x4), 0x1), value=Op.EXP(0xFF, 0x4)
        )
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0x4), 0x2), value=Op.EXP(0x101, 0x4)
        )
        + Op.SSTORE(key=Op.MUL(0x10, 0x5), value=Op.EXP(0x100, 0x5))
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0x5), 0x1), value=Op.EXP(0xFF, 0x5)
        )
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0x5), 0x2), value=Op.EXP(0x101, 0x5)
        )
        + Op.SSTORE(key=Op.MUL(0x10, 0x6), value=Op.EXP(0x100, 0x6))
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0x6), 0x1), value=Op.EXP(0xFF, 0x6)
        )
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0x6), 0x2), value=Op.EXP(0x101, 0x6)
        )
        + Op.SSTORE(key=Op.MUL(0x10, 0x7), value=Op.EXP(0x100, 0x7))
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0x7), 0x1), value=Op.EXP(0xFF, 0x7)
        )
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0x7), 0x2), value=Op.EXP(0x101, 0x7)
        )
        + Op.SSTORE(key=Op.MUL(0x10, 0x8), value=Op.EXP(0x100, 0x8))
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0x8), 0x1), value=Op.EXP(0xFF, 0x8)
        )
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0x8), 0x2), value=Op.EXP(0x101, 0x8)
        )
        + Op.SSTORE(key=Op.MUL(0x10, 0x9), value=Op.EXP(0x100, 0x9))
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0x9), 0x1), value=Op.EXP(0xFF, 0x9)
        )
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0x9), 0x2), value=Op.EXP(0x101, 0x9)
        )
        + Op.SSTORE(key=Op.MUL(0x10, 0xA), value=Op.EXP(0x100, 0xA))
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0xA), 0x1), value=Op.EXP(0xFF, 0xA)
        )
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0xA), 0x2), value=Op.EXP(0x101, 0xA)
        )
        + Op.SSTORE(key=Op.MUL(0x10, 0xB), value=Op.EXP(0x100, 0xB))
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0xB), 0x1), value=Op.EXP(0xFF, 0xB)
        )
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0xB), 0x2), value=Op.EXP(0x101, 0xB)
        )
        + Op.SSTORE(key=Op.MUL(0x10, 0xC), value=Op.EXP(0x100, 0xC))
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0xC), 0x1), value=Op.EXP(0xFF, 0xC)
        )
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0xC), 0x2), value=Op.EXP(0x101, 0xC)
        )
        + Op.SSTORE(key=Op.MUL(0x10, 0xD), value=Op.EXP(0x100, 0xD))
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0xD), 0x1), value=Op.EXP(0xFF, 0xD)
        )
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0xD), 0x2), value=Op.EXP(0x101, 0xD)
        )
        + Op.SSTORE(key=Op.MUL(0x10, 0xE), value=Op.EXP(0x100, 0xE))
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0xE), 0x1), value=Op.EXP(0xFF, 0xE)
        )
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0xE), 0x2), value=Op.EXP(0x101, 0xE)
        )
        + Op.SSTORE(key=Op.MUL(0x10, 0xF), value=Op.EXP(0x100, 0xF))
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0xF), 0x1), value=Op.EXP(0xFF, 0xF)
        )
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0xF), 0x2), value=Op.EXP(0x101, 0xF)
        )
        + Op.SSTORE(key=Op.MUL(0x10, 0x10), value=Op.EXP(0x100, 0x10))
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0x10), 0x1), value=Op.EXP(0xFF, 0x10)
        )
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0x10), 0x2), value=Op.EXP(0x101, 0x10)
        )
        + Op.SSTORE(key=Op.MUL(0x10, 0x11), value=Op.EXP(0x100, 0x11))
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0x11), 0x1), value=Op.EXP(0xFF, 0x11)
        )
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0x11), 0x2), value=Op.EXP(0x101, 0x11)
        )
        + Op.SSTORE(key=Op.MUL(0x10, 0x12), value=Op.EXP(0x100, 0x12))
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0x12), 0x1), value=Op.EXP(0xFF, 0x12)
        )
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0x12), 0x2), value=Op.EXP(0x101, 0x12)
        )
        + Op.SSTORE(key=Op.MUL(0x10, 0x13), value=Op.EXP(0x100, 0x13))
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0x13), 0x1), value=Op.EXP(0xFF, 0x13)
        )
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0x13), 0x2), value=Op.EXP(0x101, 0x13)
        )
        + Op.SSTORE(key=Op.MUL(0x10, 0x14), value=Op.EXP(0x100, 0x14))
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0x14), 0x1), value=Op.EXP(0xFF, 0x14)
        )
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0x14), 0x2), value=Op.EXP(0x101, 0x14)
        )
        + Op.SSTORE(key=Op.MUL(0x10, 0x15), value=Op.EXP(0x100, 0x15))
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0x15), 0x1), value=Op.EXP(0xFF, 0x15)
        )
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0x15), 0x2), value=Op.EXP(0x101, 0x15)
        )
        + Op.SSTORE(key=Op.MUL(0x10, 0x16), value=Op.EXP(0x100, 0x16))
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0x16), 0x1), value=Op.EXP(0xFF, 0x16)
        )
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0x16), 0x2), value=Op.EXP(0x101, 0x16)
        )
        + Op.SSTORE(key=Op.MUL(0x10, 0x17), value=Op.EXP(0x100, 0x17))
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0x17), 0x1), value=Op.EXP(0xFF, 0x17)
        )
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0x17), 0x2), value=Op.EXP(0x101, 0x17)
        )
        + Op.SSTORE(key=Op.MUL(0x10, 0x18), value=Op.EXP(0x100, 0x18))
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0x18), 0x1), value=Op.EXP(0xFF, 0x18)
        )
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0x18), 0x2), value=Op.EXP(0x101, 0x18)
        )
        + Op.SSTORE(key=Op.MUL(0x10, 0x19), value=Op.EXP(0x100, 0x19))
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0x19), 0x1), value=Op.EXP(0xFF, 0x19)
        )
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0x19), 0x2), value=Op.EXP(0x101, 0x19)
        )
        + Op.SSTORE(key=Op.MUL(0x10, 0x1A), value=Op.EXP(0x100, 0x1A))
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0x1A), 0x1), value=Op.EXP(0xFF, 0x1A)
        )
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0x1A), 0x2), value=Op.EXP(0x101, 0x1A)
        )
        + Op.SSTORE(key=Op.MUL(0x10, 0x1B), value=Op.EXP(0x100, 0x1B))
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0x1B), 0x1), value=Op.EXP(0xFF, 0x1B)
        )
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0x1B), 0x2), value=Op.EXP(0x101, 0x1B)
        )
        + Op.SSTORE(key=Op.MUL(0x10, 0x1C), value=Op.EXP(0x100, 0x1C))
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0x1C), 0x1), value=Op.EXP(0xFF, 0x1C)
        )
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0x1C), 0x2), value=Op.EXP(0x101, 0x1C)
        )
        + Op.SSTORE(key=Op.MUL(0x10, 0x1D), value=Op.EXP(0x100, 0x1D))
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0x1D), 0x1), value=Op.EXP(0xFF, 0x1D)
        )
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0x1D), 0x2), value=Op.EXP(0x101, 0x1D)
        )
        + Op.SSTORE(key=Op.MUL(0x10, 0x1E), value=Op.EXP(0x100, 0x1E))
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0x1E), 0x1), value=Op.EXP(0xFF, 0x1E)
        )
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0x1E), 0x2), value=Op.EXP(0x101, 0x1E)
        )
        + Op.SSTORE(key=Op.MUL(0x10, 0x1F), value=Op.EXP(0x100, 0x1F))
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0x1F), 0x1), value=Op.EXP(0xFF, 0x1F)
        )
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0x1F), 0x2), value=Op.EXP(0x101, 0x1F)
        )
        + Op.SSTORE(key=Op.MUL(0x10, 0x20), value=Op.EXP(0x100, 0x20))
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0x20), 0x1), value=Op.EXP(0xFF, 0x20)
        )
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0x20), 0x2), value=Op.EXP(0x101, 0x20)
        )
        + Op.SSTORE(key=Op.MUL(0x10, 0x21), value=Op.EXP(0x100, 0x21))
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0x21), 0x1), value=Op.EXP(0xFF, 0x21)
        )
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0x21), 0x2), value=Op.EXP(0x101, 0x21)
        )
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0xE660D528E4A7AD36825F9D64F5F141596FEFF7AE),  # noqa: E501
    )
    pre[sender] = Account(balance=0xBA1A9CE0BA1A9CE)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes("693c6139") + Hash(0x0),
        gas_limit=16777216,
        value=1,
    )

    post = {
        target: Account(
            storage={
                0: 1,
                1: 1,
                2: 1,
                16: 256,
                17: 255,
                18: 257,
                32: 0x10000,
                33: 65025,
                34: 0x10201,
                48: 0x1000000,
                49: 0xFD02FF,
                50: 0x1030301,
                64: 0x100000000,
                65: 0xFC05FC01,
                66: 0x104060401,
                80: 0x10000000000,
                81: 0xFB09F604FF,
                82: 0x1050A0A0501,
                96: 0x1000000000000,
                97: 0xFA0EEC0EFA01,
                98: 0x1060F140F0601,
                112: 0x100000000000000,
                113: 0xF914DD22EB06FF,
                114: 0x107152323150701,
                128: 0x10000000000000000,
                129: 0xF81BC845C81BF801,
                130: 0x1081C3846381C0801,
                144: 0x1000000000000000000,
                145: 0xF723AC7D8253DC08FF,
                146: 0x10924547E7E54240901,
                160: 0x100000000000000000000,
                161: 0xF62C88D104D1882CF601,
                162: 0x10A2D78D2FCD2782D0A01,
                176: 0x10000000000000000000000,
                177: 0xF5365C4833CCB6A4C90AFF,
                178: 0x10B37A64BCFCF4AA5370B01,
                192: 0x1000000000000000000000000,
                193: 0xF44125EBEB98E9EE2441F401,
                194: 0x10C42DDF21B9F19EFDC420C01,
                208: 0x100000000000000000000000000,
                209: 0xF34CE4C5FFAD5104361DB20CFF,
                210: 0x10D4F20D00DBAB909CC1E4E0D01,
                224: 0x10000000000000000000000000000,
                225: 0xF25997E139ADA3B331E7945AF201,
                226: 0x10E5C6FF0DDC873C2D5EA6C5B0E01,
                240: 0x1000000000000000000000000000000,
                241: 0xF1673E495873F60F7EB5ACC6970EFF,
                242: 0x10F6ACC60CEA63C3698C056C7690F01,
                256: 0x100000000000000000000000000000000,
                257: 0xF075D70B0F1B82196F36F719D077F001,
                258: 0x1107A372D2F74E272CF59171E30781001,
                272: 0x10000000000000000000000000000000000,
                273: 0xEF856134040C669755C7C022B6A77810FF,
                274: 0x1118AB1645CA45755422870354EA8881101,
                288: 0x1000000000000000000000000000000000000,
                289: 0xEE95DBD2D0085A30BE71F86293F0D098EE01,
                290: 0x1129C3C15C100FBAC976A98A583F730991201,
                304: 0x100000000000000000000000000000000000000,
                305: 0xEDA745F6FD3851D68DB3866A315CDFC85512FF,
                306: 0x113AED851D6C1FCA84402033E297B27C9AB1301,
                320: 0x10000000000000000000000000000000000000000,
                321: 0xECB99EB1063B1984B725D2E3C72B82E88CBDEC01,
                322: 0x114C2872A2898BEA4EC46054167A4A2F174BE1401,
                336: 0x1000000000000000000000000000000000000000000,
                337: 0xEBCCE5125534DE6B326EAD10E3645765A4312E14FF,
                338: 0x115D749B152C1576391324B46A90C47946632D21501,
                352: 0x100000000000000000000000000000000000000000000,
                353: 0xEAE1182D42DFA98CC73C3E63D280F30E3E8CFCE6EA01,
                354: 0x116ED20FB041418BAF4C37D91EFB553DBFA9904E71601,
                368: 0x10000000000000000000000000000000000000000000000,
                369: 0xE9F63715159CC9E33A7502256EAE721B304E6FEA0316FF,
                370: 0x118040E1BFF182CD3AFB8410F81A5092FD6939DEBFD1701,
                384: 0x1000000000000000000000000000000000000000000000000,
                385: 0xE90C40DE00872D19573A8D23493FC3A9151E217A1913E801,
                386: 0x1191C122A1B1745008367F9509126AE39066A3189E9141801,
                400: 0x100000000000000000000000000000000000000000000000000,
                401: 0xE823349D2286A5EC3DE3529625F683E56C0903589EFAD418FF,
                402: 0x11A352E3C45325C4583EB6149E1B7D4E73F709BBB72FD2C1901,
                416: 0x10000000000000000000000000000000000000000000000000000,
                417: 0xE73B116885641F4651A56F438FD08D61869CFA55465BD944E601,
                418: 0x11B4F636A81778EA1C96F4CAB2B998CBC26B00C572E7029451A01,
                432: 0x1000000000000000000000000000000000000000000000000000000,
                433: 0xE653D6571CDEBB270B53C9D44C40BCD425165D5AF1157D6BA11AFF,
                434: 0x11C6AB2CDEBF906306B38BBF7D6C52648E2D6BC63859E996E5F1B01,
                448: 0x100000000000000000000000000000000000000000000000000000000,  # noqa: E501
                449: 0xE56D8280C5C1DC6BE448760A77F47C1750F146FD962467EE3579E401,  # noqa: E501
                450: 0x11D871D80B9E4FF369BA3F4B3CE9BEB6F2BB9931FE9243807CD7A1C01,  # noqa: E501
                464: 0x10000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                465: 0xE48814FE44FC1A8F78642D946D7C879B39A055B6988E438647446A1CFF,  # noqa: E501
                466: 0x11EA4A49E3A9EE435D23F98A8826A875A9AE54CB3090D5C3FD547961D01,  # noqa: E501
                480: 0x1000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                481: 0xE3A38CE946B71E74E8EBC966D90F0B139E66B560E1F5B542C0FD25B2E201,  # noqa: E501
                482: 0x11FC34942D8D9831A0811D8412AECF1E1F58031FFBC16699C151CDDB31E01,  # noqa: E501
                496: 0x100000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                497: 0xE2BFE95C5D7067567402DD9D7235FC088AC84EAB8113BF8D7E3C288D2F1EFF,  # noqa: E501
                498: 0x120E30C8C1BB25C9D2219EA196C17DED3D775B231BBD28005B131FA90D11F01,  # noqa: E501
                512: 0,
                513: 0xE1DD29730112F6EF1D8EDABFD4C3C60C823D865CD592ABCDF0BDEC64A1EFE001,  # noqa: E501
                514: 0x2203EF98A7CE0EF9BF3C04038583F6B2AB4D27E3ED8E5285B6E32C8B61F02001,  # noqa: E501
                528: 0,
                529: 0xFB4C498E11E3F82E714BE514EF024675BB48D678BD192222CD2E783D4DF020FF,  # noqa: E501
                530: 0x25F3884075DD08B8FB400789097AA95DF8750BD17BE0D83C9A0FB7ED52102101,  # noqa: E501
            },
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
