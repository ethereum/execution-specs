"""
Ori Pomerantz qbzzt1@gmail.com

Ported from:
state_tests/VMTests/vmArithmeticTest/expPower256Filler.yml
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
    ["state_tests/VMTests/vmArithmeticTest/expPower256Filler.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_exp_power256(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Ori Pomerantz qbzzt1@gmail."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x40ac0fc28c27e961ee46ec43355a094de205856edbd4654cf2577c2608d4ec1e
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
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
    target = pre.deploy_contract(
        code=Op.SSTORE(key=Op.MUL(0x10, 0x0), value=Op.EXP(0x100, 0x0))
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x0), 0x1), value=Op.EXP(0xff, 0x0))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x0), 0x2), value=Op.EXP(0x101, 0x0))  # noqa: E501
        + Op.SSTORE(key=Op.MUL(0x10, 0x1), value=Op.EXP(0x100, 0x1))
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x1), 0x1), value=Op.EXP(0xff, 0x1))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x1), 0x2), value=Op.EXP(0x101, 0x1))  # noqa: E501
        + Op.SSTORE(key=Op.MUL(0x10, 0x2), value=Op.EXP(0x100, 0x2))
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x2), 0x1), value=Op.EXP(0xff, 0x2))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x2), 0x2), value=Op.EXP(0x101, 0x2))  # noqa: E501
        + Op.SSTORE(key=Op.MUL(0x10, 0x3), value=Op.EXP(0x100, 0x3))
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x3), 0x1), value=Op.EXP(0xff, 0x3))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x3), 0x2), value=Op.EXP(0x101, 0x3))  # noqa: E501
        + Op.SSTORE(key=Op.MUL(0x10, 0x4), value=Op.EXP(0x100, 0x4))
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x4), 0x1), value=Op.EXP(0xff, 0x4))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x4), 0x2), value=Op.EXP(0x101, 0x4))  # noqa: E501
        + Op.SSTORE(key=Op.MUL(0x10, 0x5), value=Op.EXP(0x100, 0x5))
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x5), 0x1), value=Op.EXP(0xff, 0x5))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x5), 0x2), value=Op.EXP(0x101, 0x5))  # noqa: E501
        + Op.SSTORE(key=Op.MUL(0x10, 0x6), value=Op.EXP(0x100, 0x6))
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x6), 0x1), value=Op.EXP(0xff, 0x6))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x6), 0x2), value=Op.EXP(0x101, 0x6))  # noqa: E501
        + Op.SSTORE(key=Op.MUL(0x10, 0x7), value=Op.EXP(0x100, 0x7))
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x7), 0x1), value=Op.EXP(0xff, 0x7))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x7), 0x2), value=Op.EXP(0x101, 0x7))  # noqa: E501
        + Op.SSTORE(key=Op.MUL(0x10, 0x8), value=Op.EXP(0x100, 0x8))
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x8), 0x1), value=Op.EXP(0xff, 0x8))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x8), 0x2), value=Op.EXP(0x101, 0x8))  # noqa: E501
        + Op.SSTORE(key=Op.MUL(0x10, 0x9), value=Op.EXP(0x100, 0x9))
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x9), 0x1), value=Op.EXP(0xff, 0x9))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x9), 0x2), value=Op.EXP(0x101, 0x9))  # noqa: E501
        + Op.SSTORE(key=Op.MUL(0x10, 0xa), value=Op.EXP(0x100, 0xa))
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0xa), 0x1), value=Op.EXP(0xff, 0xa))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0xa), 0x2), value=Op.EXP(0x101, 0xa))  # noqa: E501
        + Op.SSTORE(key=Op.MUL(0x10, 0xb), value=Op.EXP(0x100, 0xb))
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0xb), 0x1), value=Op.EXP(0xff, 0xb))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0xb), 0x2), value=Op.EXP(0x101, 0xb))  # noqa: E501
        + Op.SSTORE(key=Op.MUL(0x10, 0xc), value=Op.EXP(0x100, 0xc))
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0xc), 0x1), value=Op.EXP(0xff, 0xc))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0xc), 0x2), value=Op.EXP(0x101, 0xc))  # noqa: E501
        + Op.SSTORE(key=Op.MUL(0x10, 0xd), value=Op.EXP(0x100, 0xd))
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0xd), 0x1), value=Op.EXP(0xff, 0xd))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0xd), 0x2), value=Op.EXP(0x101, 0xd))  # noqa: E501
        + Op.SSTORE(key=Op.MUL(0x10, 0xe), value=Op.EXP(0x100, 0xe))
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0xe), 0x1), value=Op.EXP(0xff, 0xe))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0xe), 0x2), value=Op.EXP(0x101, 0xe))  # noqa: E501
        + Op.SSTORE(key=Op.MUL(0x10, 0xf), value=Op.EXP(0x100, 0xf))
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0xf), 0x1), value=Op.EXP(0xff, 0xf))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0xf), 0x2), value=Op.EXP(0x101, 0xf))  # noqa: E501
        + Op.SSTORE(key=Op.MUL(0x10, 0x10), value=Op.EXP(0x100, 0x10))
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x10), 0x1), value=Op.EXP(0xff, 0x10))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x10), 0x2), value=Op.EXP(0x101, 0x10))  # noqa: E501
        + Op.SSTORE(key=Op.MUL(0x10, 0x11), value=Op.EXP(0x100, 0x11))
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x11), 0x1), value=Op.EXP(0xff, 0x11))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x11), 0x2), value=Op.EXP(0x101, 0x11))  # noqa: E501
        + Op.SSTORE(key=Op.MUL(0x10, 0x12), value=Op.EXP(0x100, 0x12))
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x12), 0x1), value=Op.EXP(0xff, 0x12))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x12), 0x2), value=Op.EXP(0x101, 0x12))  # noqa: E501
        + Op.SSTORE(key=Op.MUL(0x10, 0x13), value=Op.EXP(0x100, 0x13))
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x13), 0x1), value=Op.EXP(0xff, 0x13))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x13), 0x2), value=Op.EXP(0x101, 0x13))  # noqa: E501
        + Op.SSTORE(key=Op.MUL(0x10, 0x14), value=Op.EXP(0x100, 0x14))
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x14), 0x1), value=Op.EXP(0xff, 0x14))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x14), 0x2), value=Op.EXP(0x101, 0x14))  # noqa: E501
        + Op.SSTORE(key=Op.MUL(0x10, 0x15), value=Op.EXP(0x100, 0x15))
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x15), 0x1), value=Op.EXP(0xff, 0x15))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x15), 0x2), value=Op.EXP(0x101, 0x15))  # noqa: E501
        + Op.SSTORE(key=Op.MUL(0x10, 0x16), value=Op.EXP(0x100, 0x16))
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x16), 0x1), value=Op.EXP(0xff, 0x16))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x16), 0x2), value=Op.EXP(0x101, 0x16))  # noqa: E501
        + Op.SSTORE(key=Op.MUL(0x10, 0x17), value=Op.EXP(0x100, 0x17))
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x17), 0x1), value=Op.EXP(0xff, 0x17))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x17), 0x2), value=Op.EXP(0x101, 0x17))  # noqa: E501
        + Op.SSTORE(key=Op.MUL(0x10, 0x18), value=Op.EXP(0x100, 0x18))
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x18), 0x1), value=Op.EXP(0xff, 0x18))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x18), 0x2), value=Op.EXP(0x101, 0x18))  # noqa: E501
        + Op.SSTORE(key=Op.MUL(0x10, 0x19), value=Op.EXP(0x100, 0x19))
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x19), 0x1), value=Op.EXP(0xff, 0x19))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x19), 0x2), value=Op.EXP(0x101, 0x19))  # noqa: E501
        + Op.SSTORE(key=Op.MUL(0x10, 0x1a), value=Op.EXP(0x100, 0x1a))
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x1a), 0x1), value=Op.EXP(0xff, 0x1a))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x1a), 0x2), value=Op.EXP(0x101, 0x1a))  # noqa: E501
        + Op.SSTORE(key=Op.MUL(0x10, 0x1b), value=Op.EXP(0x100, 0x1b))
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x1b), 0x1), value=Op.EXP(0xff, 0x1b))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x1b), 0x2), value=Op.EXP(0x101, 0x1b))  # noqa: E501
        + Op.SSTORE(key=Op.MUL(0x10, 0x1c), value=Op.EXP(0x100, 0x1c))
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x1c), 0x1), value=Op.EXP(0xff, 0x1c))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x1c), 0x2), value=Op.EXP(0x101, 0x1c))  # noqa: E501
        + Op.SSTORE(key=Op.MUL(0x10, 0x1d), value=Op.EXP(0x100, 0x1d))
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x1d), 0x1), value=Op.EXP(0xff, 0x1d))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x1d), 0x2), value=Op.EXP(0x101, 0x1d))  # noqa: E501
        + Op.SSTORE(key=Op.MUL(0x10, 0x1e), value=Op.EXP(0x100, 0x1e))
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x1e), 0x1), value=Op.EXP(0xff, 0x1e))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x1e), 0x2), value=Op.EXP(0x101, 0x1e))  # noqa: E501
        + Op.SSTORE(key=Op.MUL(0x10, 0x1f), value=Op.EXP(0x100, 0x1f))
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x1f), 0x1), value=Op.EXP(0xff, 0x1f))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x1f), 0x2), value=Op.EXP(0x101, 0x1f))  # noqa: E501
        + Op.SSTORE(key=Op.MUL(0x10, 0x20), value=Op.EXP(0x100, 0x20))
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x20), 0x1), value=Op.EXP(0xff, 0x20))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x20), 0x2), value=Op.EXP(0x101, 0x20))  # noqa: E501
        + Op.SSTORE(key=Op.MUL(0x10, 0x21), value=Op.EXP(0x100, 0x21))
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x21), 0x1), value=Op.EXP(0xff, 0x21))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x21), 0x2), value=Op.EXP(0x101, 0x21))  # noqa: E501
        + Op.STOP,
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0xe660d528e4a7ad36825f9d64f5f141596feff7ae"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xba1a9ce0ba1a9ce)


    tx = Transaction(
        sender=sender,
        to=target,
        data=bytes.fromhex("693c61390000000000000000000000000000000000000000000000000000000000000000"),  # noqa: E501
        gas_limit=16777216,
        value=1,
        nonce=0,
        gas_price=10,
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
            49: 0xfd02ff,
            50: 0x1030301,
            64: 0x100000000,
            65: 0xfc05fc01,
            66: 0x104060401,
            80: 0x10000000000,
            81: 0xfb09f604ff,
            82: 0x1050a0a0501,
            96: 0x1000000000000,
            97: 0xfa0eec0efa01,
            98: 0x1060f140f0601,
            112: 0x100000000000000,
            113: 0xf914dd22eb06ff,
            114: 0x107152323150701,
            128: 0x10000000000000000,
            129: 0xf81bc845c81bf801,
            130: 0x1081c3846381c0801,
            144: 0x1000000000000000000,
            145: 0xf723ac7d8253dc08ff,
            146: 0x10924547e7e54240901,
            160: 0x100000000000000000000,
            161: 0xf62c88d104d1882cf601,
            162: 0x10a2d78d2fcd2782d0a01,
            176: 0x10000000000000000000000,
            177: 0xf5365c4833ccb6a4c90aff,
            178: 0x10b37a64bcfcf4aa5370b01,
            192: 0x1000000000000000000000000,
            193: 0xf44125ebeb98e9ee2441f401,
            194: 0x10c42ddf21b9f19efdc420c01,
            208: 0x100000000000000000000000000,
            209: 0xf34ce4c5ffad5104361db20cff,
            210: 0x10d4f20d00dbab909cc1e4e0d01,
            224: 0x10000000000000000000000000000,
            225: 0xf25997e139ada3b331e7945af201,
            226: 0x10e5c6ff0ddc873c2d5ea6c5b0e01,
            240: 0x1000000000000000000000000000000,
            241: 0xf1673e495873f60f7eb5acc6970eff,
            242: 0x10f6acc60cea63c3698c056c7690f01,
            256: 0x100000000000000000000000000000000,
            257: 0xf075d70b0f1b82196f36f719d077f001,
            258: 0x1107a372d2f74e272cf59171e30781001,
            272: 0x10000000000000000000000000000000000,
            273: 0xef856134040c669755c7c022b6a77810ff,
            274: 0x1118ab1645ca45755422870354ea8881101,
            288: 0x1000000000000000000000000000000000000,
            289: 0xee95dbd2d0085a30be71f86293f0d098ee01,
            290: 0x1129c3c15c100fbac976a98a583f730991201,
            304: 0x100000000000000000000000000000000000000,
            305: 0xeda745f6fd3851d68db3866a315cdfc85512ff,
            306: 0x113aed851d6c1fca84402033e297b27c9ab1301,
            320: 0x10000000000000000000000000000000000000000,
            321: 0xecb99eb1063b1984b725d2e3c72b82e88cbdec01,
            322: 0x114c2872a2898bea4ec46054167a4a2f174be1401,
            336: 0x1000000000000000000000000000000000000000000,
            337: 0xebcce5125534de6b326ead10e3645765a4312e14ff,
            338: 0x115d749b152c1576391324b46a90c47946632d21501,
            352: 0x100000000000000000000000000000000000000000000,
            353: 0xeae1182d42dfa98cc73c3e63d280f30e3e8cfce6ea01,
            354: 0x116ed20fb041418baf4c37d91efb553dbfa9904e71601,
            368: 0x10000000000000000000000000000000000000000000000,
            369: 0xe9f63715159cc9e33a7502256eae721b304e6fea0316ff,
            370: 0x118040e1bff182cd3afb8410f81a5092fd6939debfd1701,
            384: 0x1000000000000000000000000000000000000000000000000,
            385: 0xe90c40de00872d19573a8d23493fc3a9151e217a1913e801,
            386: 0x1191c122a1b1745008367f9509126ae39066a3189e9141801,
            400: 0x100000000000000000000000000000000000000000000000000,
            401: 0xe823349d2286a5ec3de3529625f683e56c0903589efad418ff,
            402: 0x11a352e3c45325c4583eb6149e1b7d4e73f709bbb72fd2c1901,
            416: 0x10000000000000000000000000000000000000000000000000000,
            417: 0xe73b116885641f4651a56f438fd08d61869cfa55465bd944e601,
            418: 0x11b4f636a81778ea1c96f4cab2b998cbc26b00c572e7029451a01,
            432: 0x1000000000000000000000000000000000000000000000000000000,
            433: 0xe653d6571cdebb270b53c9d44c40bcd425165d5af1157d6ba11aff,
            434: 0x11c6ab2cdebf906306b38bbf7d6c52648e2d6bc63859e996e5f1b01,
            448: 0x100000000000000000000000000000000000000000000000000000000,
            449: 0xe56d8280c5c1dc6be448760a77f47c1750f146fd962467ee3579e401,
            450: 0x11d871d80b9e4ff369ba3f4b3ce9beb6f2bb9931fe9243807cd7a1c01,
            464: 0x10000000000000000000000000000000000000000000000000000000000,
            465: 0xe48814fe44fc1a8f78642d946d7c879b39a055b6988e438647446a1cff,
            466: 0x11ea4a49e3a9ee435d23f98a8826a875a9ae54cb3090d5c3fd547961d01,
            480: 0x1000000000000000000000000000000000000000000000000000000000000,
            481: 0xe3a38ce946b71e74e8ebc966d90f0b139e66b560e1f5b542c0fd25b2e201,
            482: 0x11fc34942d8d9831a0811d8412aecf1e1f58031ffbc16699c151cddb31e01,
            496: 0x100000000000000000000000000000000000000000000000000000000000000,
            497: 0xe2bfe95c5d7067567402dd9d7235fc088ac84eab8113bf8d7e3c288d2f1eff,
            498: 0x120e30c8c1bb25c9d2219ea196c17ded3d775b231bbd28005b131fa90d11f01,
            512: 0,
            513: 0xe1dd29730112f6ef1d8edabfd4c3c60c823d865cd592abcdf0bdec64a1efe001,
            514: 0x2203ef98a7ce0ef9bf3c04038583f6b2ab4d27e3ed8e5285b6e32c8b61f02001,
            528: 0,
            529: 0xfb4c498e11e3f82e714be514ef024675bb48d678bd192222cd2e783d4df020ff,
            530: 0x25f3884075dd08b8fb400789097aa95df8750bd17be0d83c9a0fb7ed52102101,
        },
            ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
