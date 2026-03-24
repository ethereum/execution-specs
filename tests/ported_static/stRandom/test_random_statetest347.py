"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stRandom/randomStatetest347Filler.json
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
    ["tests/static/state_tests/stRandom/randomStatetest347Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_random_statetest347(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0xa7f7c8ef9bbbcfb0f7e81c1fd46bb732fba60592")
    sender = EOA(
        key=0x1F2F6944F70460E655546D414267BD3491A2DD9DAFB2280605404C858990D053
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=188473852,
    )

    pre[sender] = Account(balance=0x1024D289465FA51769)
    # Source: raw bytecode
    pre.deploy_contract(
        code=Op.CALLDATASIZE,
        balance=0x4EA91708,
        nonce=89,
        address=Address("0x79d9fbe6ac70917cb2e16ec4cd32968ce19c724d"),  # noqa: E501
    )
    # Source: raw bytecode
    contract = pre.deploy_contract(
        code=(
            Op.CALLCODE(
                gas=0xA9E792747CE0492ABDE8C2,
                address=0xE5D2EA2689DECFD971C7478EFFB0,
                value=0xEF63E19225,
                args_offset=0x7A0D,
                args_size=0x7D442A5E8734AF2AAA4C859B452EED7860C2F7E051580427B6C3CC6D7FEE,  # noqa: E501
                ret_offset=0x9A3805D8C55157A82B7660EF2A049CFBF79C15FA8E3261F121D213590FA391,  # noqa: E501
                ret_size=0xD552603C57,
            )
            + Op.PUSH17[0xE93D5ED0B213FED7AE59294537D4864C0E]
            + Op.PUSH9[0xBBE30EC5D1E6B85402]
            + Op.PUSH25[0x62CFCBEA15E8367DFAA080EE0DA2B0D2CA892F5A7643543704]
            + Op.PUSH7[0xCCDDD03115EC8A]
            + Op.PUSH27[
                0xD2E6C62C29425A45EC842FB74C369FB15A42E4B4E48B3EB70BE2A0
            ]
            + Op.DUP5
            + Op.PUSH21[0x69987980E6EAA539365A491D2366334F78F03ACB17]
            + Op.PUSH25[0x9E7525ADD39A234D3D2EF1CF8544A52389411EF846D3CD7F3]
            + Op.PUSH14[0xD1DB7F414860020171F07598CFB]
            + Op.PUSH3[0xE15A9]
            + Op.PUSH9[0x1C843D60AEE9FB8A4E]
            + Op.PUSH31[
                0x37713AFBF6EF9D1667513975C76F26AC35CE209B1E0A3BB7C1982136893153  # noqa: E501
            ]
            + Op.PUSH28[
                0x4095EA42B32BAF1BA596B9AF5CCE961AE705F8C9C5465E3496335298
            ]
            + Op.PUSH18[0xF64351169E7FE48CCBB866952FABBFCF40DF]
            + Op.PUSH19[0x3C564E109DBD4C9C15EE9AD625E96A5765F6F5]
            + Op.PUSH15[0xE0601677961DA7EBAD5F583F6EB6DA]
            + Op.PUSH29[
                0x8348425FE784F532F288963CCDBF9DE3AC3EBC38B75A806B40E51B895C
            ]
            + Op.PUSH7[0x2D0BCAB255A04B]
            + Op.PUSH19[0x3F1E500517D17EB720E02F445CB046BD0FE7D2]
            + Op.PUSH22[0x9438C79AA2DFCAEF1CF57E4EB9C832F7EF449A9C32F6]
            + Op.PUSH20[0x728F4B0DCCDFA8FB1D447E2F681076AC51A98F76]
            + Op.PUSH1[0xA]
            + Op.PUSH7[0xB4692CA7E1E9C8]
            + Op.SWAP16
            + Op.LOG2(
                offset=0x95CE4AC7601160EA2D6656C8F2A554B43E263CC3A60E9FD0,
                size=0xBCA28F2EC8BB3A092BD0C30849558FE16A4B7070CB05AEC329C0286C26FFF5,  # noqa: E501
                topic_1=0x551497,
                topic_2=0xCDF879CB0C,
            )
            + Op.PUSH13[0xA5F7202F02888A731E84AB326]
            + Op.PUSH2[0xC77]
            + Op.PUSH24[0x1F85025EB8C552943D2DA5DE48786015F5B8B5921D26C1E2]
            + Op.PUSH24[0xD5A4CDA5F1F77EC5F3A83E6ED6821FF025370E2FAD05A0F3]
            + Op.PUSH5[0xF58F3705C8]
            + Op.PUSH23[0x1904D63E0F2E5BDBE2B0B1DDF82BB441C547634E8C1864]
            + Op.PUSH20[0x7333E845FFA373C102303F727BFA14F4C445711F]
            + Op.PUSH16[0x9695C36F3627DF02A1FE2D7ECA55FAED]
            + Op.PUSH10[0x84000AB2A99545148BBE]
            + Op.PUSH20[0x69A47367BC24256ACD6A3A22D5FB32434B199829]
            + Op.PUSH27[
                0xE6B2EDF08B72DC4598AA600E16707699A84E55EF611EA0E6DA482F
            ]
            + Op.PUSH13[0x6E9D05D54BBB4AD06CD62622E4]
            + Op.PUSH10[0xFBCD3E637A8F0D2AC914]
            + Op.SWAP12
            + Op.LOG0(
                offset=0x46AA1FDC218D936E56F55B5A38BBD798361040E1BADB1AB06ADC38A723BADF,  # noqa: E501
                size=0x76CCE991CB5D4B4DE1229E3DECBCF46A3C,
            )
            + Op.PUSH27[
                0x95F78553DE4DF879855274A1904A31276D7938818021E69D8F5B92
            ]
            + Op.PUSH26[0x478808A236DEEFD761DF6BC151FDED80BBE4BA725E7DB7B9FC50]
            + Op.PUSH32[
                0xB8121A009384C7BC4443747BD1AC9DC7682B32BEC0937C7FB27BA3926ACD0D6  # noqa: E501
            ]
            + Op.PUSH28[
                0x41BA6C951788F1BB1B1168229D15CAFDC63209C95DF646566024013D
            ]
            + Op.PUSH23[0x6A01D6B8051C357243C9F464F423A2AE8EFA4F9EFD9577]
            + Op.PUSH17[0x99EAC9B0825D18018A5AFCB6CECD9AB9A9]
            + Op.PUSH6[0x5AE262DB08A2]
            + Op.PUSH18[0xD8ADEDBC3E7EB6ACFD2D576EC297C09C4BD4]
            + Op.PUSH27[
                0x80DACD2B123E4E4E6232EF6D70ACB10F2F44A62BBCEF65A7257650
            ]
            + Op.PUSH15[0xA119B051880B515F4414920BADCD6F]
            + Op.PUSH19[0x6C04E821516F6123C9C52F29E19BFE0FB10FAB]
            + Op.PUSH23[0x536535CC0E01115C83369D4083DB2D669654C2FE8C00E3]
            + Op.PUSH28[
                0xD78F663A2CE2425D2CE358E213D6C601208BB644FA656678DE763314
            ]
            + Op.PUSH32[
                0xBD152C2AE682DEC269245F07BA3C79F4E6E1978D40F42A494D44EBA128B9D022  # noqa: E501
            ]
            + Op.DUP14
            + Op.PUSH4[0x7900CBAB]
            + Op.PUSH20[0x455423156417FAE331D26494D1ED4D06ECF20673]
            + Op.PUSH16[0x4292D5470D5091C48A80BA737372C35]
            + Op.PUSH19[0x9C829AF30DB3625785BA0B3CFC4240D0022767]
            + Op.PUSH1[0xF2]
            + Op.PUSH24[0xEAD609B52DB934A53063EC1C05488188FB37CE61059909B]
            + Op.PUSH13[0x975C0E9401EF3B71B6D0DDAE39]
            + Op.DUP7
            + Op.PUSH32[
                0x3F0878BD172851A98A233FCAFAE289FC634C36C8B3064926D92DEDA3D8C5074D  # noqa: E501
            ]
            + Op.PUSH11[0x56DAA511E7E693AAB3D434]
            + Op.PUSH29[
                0xEBDD5B63238ACDEEDC3D8EB8F69EA18CB429EE8F09C26845507BA28EBA
            ]
            + Op.SWAP2
            + Op.PUSH13[0x74FD62CD9E587A8F013122D935]
            + Op.PUSH26[0xB6B7DA091527251A4B70051BE4F0F96F61E5DC4AB713C473174C]
            + Op.PUSH31[
                0x2EBB463615B03C4787B74E8C204975399439FA553838F186AE028A47F3CCD4  # noqa: E501
            ]
            + Op.PUSH13[0x5FCC46C11A36219F3BA1D34DEF]
            + Op.PUSH28[
                0xEE989FA61E60A2ABD3652DF9F8E5A1B53D9608E3BB04F5E852333D9C
            ]
            + Op.PUSH30[
                0x761836EF5761178BD07FDE9A0DED16E1659A6C80281C259CE42E3FDBE236
            ]
            + Op.PUSH5[0xCE783B58D5]
            + Op.SWAP6
        ),
        balance=0x33498455,
        nonce=233,
        address=Address("0x97bc67b6ee773e59e516d02edb13b971c3cbd856"),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex(
            "73151af76abac2a99afe60eff5cfd8f68daf1b35e0608a690494ef4b1d043bf90e00916a"  # noqa: E501
            "cf5f0332c3ef3aa972eba960aa557dc165d1a3c726953fc637fe643a60543de4159f3bc0"  # noqa: E501
            "9673cd054235ddb44769fa2d6edb61b6e71feff2662043418ac9d2337bce1df4b842fbf8"  # noqa: E501
            "f07395b44bb506e8955d22a12176e2fb8e25bc546d77a6f5049a09f3126c915f14979d8c"  # noqa: E501
            "7c0cf88425567c6b8a6865b78e6d76208a641cb0d0651a758d9afdd5e36b2dcf740a8a1e"  # noqa: E501
            "2b19ebb0bc8ad6ac032577f3b5d483e40d0c9a40aaf32cebc478c0962e1ac5f6c648f476"  # noqa: E501
            "65f0850054ab4caab6eca1a24242087387c96452ad72e76a42a175db6c69a2d8cbcd7075"  # noqa: E501
            "9249b040a797894765385557e947875851cfe9734edc8b613cbb6bf40b41b762fa3bcbc6"  # noqa: E501
            "b59ecc66971fef9e8ed16d691702b224f0e2f8ad12577a943401f57334d3207b884a40ed"  # noqa: E501
            "472960f03e4cab61c98268b5a73b6372ab45a7a4"
        ),
        gas_limit=8653299,
        gas_price=29,
        value=9168830121677901416,
    )

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
