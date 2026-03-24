"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stRandom/randomStatetest306Filler.json
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
    ["tests/static/state_tests/stRandom/randomStatetest306Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.pre_alloc_mutable
def test_random_statetest306(
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
            Op.SIGNEXTEND(0x84517B3285B0867CD4144FF5F688D6, 0xD3)
            + Op.LOG3(
                offset=0x7DF7,
                size=0x19,
                topic_1=0xD169CDA4FC3C11E9A6F0B4CEC2F5,
                topic_2=0x78C9FA9E4B5E5DB5A4B6AC4CED,
                topic_3=0x7592395D95E37246C0673,
            )
            + Op.SGT(0x412582D556F06C6D5864CF4BE6A2D1318B8E40BA, 0x788C1554)
            + Op.SDIV(
                0x2B9D3E28F05FAF2587C4465094,
                0x454CC8D0510823591DEE680D7DDDC8C149BFCC24C65C69E6,
            )
            + Op.SGT(
                0x71A29FBE89F77C340DCBD7D67AEDF852,
                0x9901EC0946BF3D786827225FAF5DA81E158CD9B2B466,
            )
            + Op.PUSH12[0x6C76AFFB38BEB802E0AF269E]
            + Op.PUSH6[0xC22F52807C67]
            + Op.PUSH28[
                0x5E2C7D8C473AFF18FE912C7ED21AB60FE5D4916A76C93539332C6AB1
            ]
            + Op.PUSH12[0x3F81B990F4B34B0228C7F5B1]
            + Op.PUSH6[0x6BDD21D45871]
            + Op.PUSH20[0x30E4BE7D7BB91CC95818140EEF086CD82D2D6F0D]
            + Op.PUSH7[0xC92A7FFB27125A]
            + Op.PUSH3[0x5C77A8]
            + Op.SWAP7
            + Op.SDIV(
                0x2460EC0DCB4BA3B84A4DB899C29F08EF1B0F506B4F3C,
                0x68F212339508D6F60D9C93A9E201F2AE883CB9,
            )
            + Op.CALL(
                gas=0xA4EB375,
                address=0xCE8D3E84F685B2EED55366547289AC4D314DE277,
                value=0x28B0EB5F,
                args_offset=0x11,
                args_size=0x10,
                ret_offset=0x1,
                ret_size=0x1F,
            )
            + Op.PUSH30[
                0xF238E15D7D51240301521F173D628E7A68D01354FAAF406CE541F753DB89
            ]
            + Op.PUSH8[0x1F6AEDCF261F632E]
            + Op.PUSH3[0x44E8C3]
            + Op.PUSH26[0x9A2DE002F15BA4681FD3C609C0F522DFD964F95DEF9926F81232]
            + Op.PUSH24[0x81B2DE33196CC22776E9B26D8A0D65C57BDAC987D0B3E0DB]
            + Op.PUSH7[0xC0F1232C7ADD33]
            + Op.PUSH6[0xF209CC53592F]
            + Op.PUSH20[0x502D0C5889B1BBF131F8BB6A6B5E2E067B9EF676]
            + Op.PUSH23[0x8D48B3F5790C3304E046F0A9C8A838A0596583D6258F19]
            + Op.PUSH14[0xCF982A9DE5CEC4F871470E7A6C92]
            + Op.DUP10
            + Op.PUSH2[0x5E1E]
            + Op.PUSH30[
                0x140FDC038972916223FB8012E29350295F3919CB28A36411845930D5E91B
            ]
            + Op.PUSH9[0x510FAAC5E067795346]
            + Op.PUSH29[
                0xEDB653F73818749E8CBAF15A5D64BA7EE5CABC98137167B924A2AAC914
            ]
            + Op.PUSH32[
                0x159713D115E0225A84A54D6471DC7A01A7E4E814145305C9D04D2880C5BE42FC  # noqa: E501
            ]
            + Op.PUSH13[0x52CED3E983D91A580A4142021B]
            + Op.PUSH20[0xE99C3180117914B9AD03C580A8DAC862BE9B599A]
            + Op.PUSH20[0xCCFCFB230BCFFC425C13C265F3B06B8C9F104C10]
            + Op.PUSH22[0x2740765567374C211601A5F51501D18C48081998FF7B]
            + Op.PUSH27[
                0x8BFDF0BEC9EB4385B554870A996E0CAB662D991D0E5F9357F2F99F
            ]
            + Op.SWAP9
        ),
        nonce=0,
        address=Address("0xce8d3e84f685b2eed55366547289ac4d314de277"),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex(
            "79f7441ed5bec692c84f9c7783152d38908fea76de8a06eca5ebcf7e81423a68b78d5f1a"  # noqa: E501
            "84706bdb516f17a29dd779ee16374163c1ab2a85a2097e7b6235aecf7cc509b9d184688f"  # noqa: E501
            "56ccfe8638c51ee70858f690e71b338261fd2b72db56f2a0923a6d1bc51dd15ff9aae183"  # noqa: E501
            "48213d68fc8e120c307a7490f46b2d528d86e503a251fd188764646dd3b8bc3c7066a32d"  # noqa: E501
            "caa91da430f61aed0466338f17d9703f1c8648d0b19db4fcdcd0893f0f6f21c789306b8f"  # noqa: E501
            "8d110fbd563111fd088de367b9f001758786ced578880bb55e224855b0293f9277dc7201"  # noqa: E501
            "e63845a8d8eae7dc8e3e642820b61315716544e2fd297f018fe1df86427052e3a85c0c77"  # noqa: E501
            "48f6fa89b890be2a3b916794ecfff1e87a87582c991b0c61687637866981d0819020714f"  # noqa: E501
            "baee296a9ac19ac255226d4d2cf967104b669a622e77fc4c7469aee1553e5cf5cb2a7972"  # noqa: E501
            "6f07829adfa8a988fb07479add89c1a8947d88a9b361493025a66fd49776d7304a036894"  # noqa: E501
            "ecda2e148f7f87270cdd52727667c09ee625c7a37ac99ab8a195cd0a97fa9e7247f9d0f1"  # noqa: E501
            "7888132eb3f44d24d3d49c0a2e6d4850ee413c36893d04dfa9826f7236a10c77f7da3d31"  # noqa: E501
            "db8eae3070972c9d722347d4a95604d40ba66a2f53710451be8f1994756471ba4d09257f"  # noqa: E501
            "6abe619cc850f123d4715bacc2b9cf167be82e629cf36521b290bab47b9597664c0890a5"  # noqa: E501
            "d6242211d344805a3d75460c21ca9ad05dec187ddecc44c9b1c0b4c0d34c66926db22974"  # noqa: E501
            "c0bc059a6aa6354a43bf26f06e7dfa7f0e07f4f3607a8bc1227b7f0d65d660aa3c1eb773"  # noqa: E501
            "1850729f5dc3285b398806dd4b54aecbe7cb367573a1aa8f062b33e27db1e2fdef478ac3"  # noqa: E501
            "06ec57be3b6b0fd0fbbe558507ead60ce60a61eade67afdd8ba512300ecc686d51131057"  # noqa: E501
            "8908f49660d163e372ddd2636dbf1c1b6d39292b97dbd48fee420c354d341365e64505ae"  # noqa: E501
            "ffc89b6e764afc7f97200924ff8d68846e387f6bca4c4ea3f4e04ac8061efd5260577aa6"  # noqa: E501
            "9c34a7287609d2448bb32d2687a46d54c893ba21520ec26e792c836ebb8c9c1005ab55d9"  # noqa: E501
            "9c62150413fb7a7f8e2ec4766471e2452ee833fa10995e94d2c1cf89c64260836aab9b3c"  # noqa: E501
            "6a1f699776b5900f48b7c1f97dba13656a85fea0cc2d4fe85aa7a9766d767cfd6a3314ac"  # noqa: E501
            "c32eea93e15c3077fa26a3917a48af0765b5690af372219af6c2e7e5b194e6db7f76ca0b"  # noqa: E501
            "28647c5066bfbf142ac3eb1361b77953e328106b1e817e8649a9bdf4f27834bd25279dc2"  # noqa: E501
            "b7a6fab4d4e4830602f84d298f5d2682183a226118fc6c452c99ead827293548afcfeaf9"  # noqa: E501
            "655e76240e57846151bb7b1c1cc5971f0ad83dc7b02c05c2bc0a3adeb65bf608eb5c0aaf"  # noqa: E501
            "186a887a4357e31bdd83940e443289727a6e36bfc974bc20e97fa8983f18137be520500b"  # noqa: E501
            "388fe2f63185c5c66bcc71a48c7fc9c210f73a4a73c4561f62adb5ed9d7ae9a0e4833f19"  # noqa: E501
            "8dd3faa1af3ad59c282f3277fac135659e7eb7c9926fd5e954f6f42a9cd2cb6498da0767"  # noqa: E501
            "958716"
        ),
        gas_limit=1970726856,
        value=1525687154,
    )

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
