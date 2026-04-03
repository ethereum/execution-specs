"""
Test_random_statetest211.

Ported from:
state_tests/stRandom/randomStatetest211Filler.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stRandom/randomStatetest211Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_random_statetest211(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_random_statetest211."""
    coinbase = Address(0x4F3F701464972E74606D6EA82D4D3080599A0E79)
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

    # Source: raw
    # 0x7e7a980b5b1c50ebb63d8e2211d3a79e841ee5e5946b7969dfb6ca1309c99e8f68d4ee9a50996902ee4e6937e1d07ad872cf04eb2a61fc336025a3648d5818a6457dc24f19f38d3deebb09968c812740339c6df46af95b7b0283acb1944a8ca37fbaaafeac115b9ec5adc16fea5a3a828d3483e495506a790ca75d8238ebbed6477c213d0177c10b33b6cf9362273973809ac39f11dffee928f3fb18e975186fb4a74e56142d4431bfa392dd5f71d32b6c40a2bd0beb6a8b24fc592b25f0680306f11e049124ec396ea3858d3339145af8c1c16747bea056639a7faf446cd9c7bf446ed2de67f1665adc479874053c2c53f0fc53a12af3c1951fdc7a5d20aee8f96874f392a4aa2a84a99c9390ab4bd4c39f521a2b91c2ea90  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.LOG3(
            offset=0x25,
            size=0xFC33,
            topic_1=0x37E1D07AD872CF04EB2A,
            topic_2=0xD4EE9A50996902EE4E,
            topic_3=0x7A980B5B1C50EBB63D8E2211D3A79E841EE5E5946B7969DFB6CA1309C99E8F,  # noqa: E501
        )
        + Op.PUSH5[0x8D5818A645]
        + Op.PUSH30[
            0xC24F19F38D3DEEBB09968C812740339C6DF46AF95B7B0283ACB1944A8CA3
        ]
        + Op.PUSH32[
            0xBAAAFEAC115B9EC5ADC16FEA5A3A828D3483E495506A790CA75D8238EBBED647
        ]
        + Op.PUSH29[
            0x213D0177C10B33B6CF9362273973809AC39F11DFFEE928F3FB18E97518
        ]
        + Op.PUSH16[0xB4A74E56142D4431BFA392DD5F71D32B]
        + Op.PUSH13[0x40A2BD0BEB6A8B24FC592B25F0]
        + Op.PUSH9[0x306F11E049124EC39]
        + Op.PUSH15[0xA3858D3339145AF8C1C16747BEA056]
        + Op.PUSH4[0x9A7FAF44]
        + Op.PUSH13[0xD9C7BF446ED2DE67F1665ADC47]
        + Op.SWAP9
        + Op.PUSH21[0x53C2C53F0FC53A12AF3C1951FDC7A5D20AEE8F968]
        + Op.PUSH21[0xF392A4AA2A84A99C9390AB4BD4C39F521A2B91C2EA]
        + Op.SWAP1,
        nonce=0,
        address=Address(0xD7EB1DDC2F83F5620BD387BC6409BE3CC2D2422F),  # noqa: E501
    )
    # Source: raw
    # 0x6000355415600957005b60203560003555
    coinbase = pre.deploy_contract(  # noqa: F841
        code=Op.JUMPI(
            pc=0x9,
            condition=Op.ISZERO(Op.SLOAD(key=Op.CALLDATALOAD(offset=0x0))),
        )
        + Op.STOP
        + Op.JUMPDEST
        + Op.SSTORE(
            key=Op.CALLDATALOAD(offset=0x0), value=Op.CALLDATALOAD(offset=0x20)
        ),
        balance=46,
        nonce=0,
        address=Address(0x4F3F701464972E74606D6EA82D4D3080599A0E79),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(
            "7205d6a65458a0cdecda703b9d5440616f95b179076dfa7631cbf765dab81235497f97ddb6e8d399d5294ea49cfd736cdfa49a08a76dc08eff97542b54399a1b5f86b168d33cd083ac41074aa37e2f3f77a248d5db21a54d72c5053f2a79b2048d142fd588c56c48e39fa86bd16645ae7e31281c806dc847b38aba609fb88b5a3c6ce02d711bc1cb89419d740c65fcd7cd9abc94d8aaf97bfb874ed35e242cee6a462cac825efc8b53b43f7687a32b635c969cb779fecda8dcbd0dd35ef6ab482083a8b91f6199bb8050971caa227ac9ad77edf44708d99ac08e92c8c1ff6e536a3eb4625c2d8c514c8a799391a90cb528870e725560136162fb2632b2485e26d9604de562740ee89a2a5b4b1976272d046167f2151feea60ecc547dc9dc31b91ee0a712579874ebef218c4f015cbd8e76040f19d828eed7f9c070a127ce6067ad9831363977e2846559c8b97cfb3b0e8502cd54779657ab8571534f06e34b0d78259338706fac01057e66310e07ef4017629f7bf12ca747aafe8d7ccfcb78b5535dd267e3b445028e40113e1b9ccb7174b36264cfc5606cc1b4815c744393665f0a1c2ce78ff3679513083c95496a6869fe735535b8751fc5455769b44d7c9689576f2b76cb63bae9b5a47f8afd0c0466e798bf78d10b0efecc7e30695891cdc85e5f7a2827dc0b2ad41f92666faa9578ad77aa79aef0363cf4c69574bdfb74601f99ca8df4fbb481dd921b4b580a789e59c7557f305a1804f30d08c10394bc281772eef178800e0f79161010fdff6e028d5be7c0dfc295520e9b5f7fb781fb23ebd9657a42d8623d58350d43a9031a8b7e23c72ea3af0b137386987549539d695dd3e19c2cac0855644773b40cae7e824e3912190e7a6aec7bb06e5c923de8750674988f11efac6aabfc209262900167c7c18e7826b18c6e65696c94c79ed8f574d69ffb0de2046a602f2e9eeb57a764e01cae63fc0e6c11703a61af60fd0c2a6af1e06d545b5ed713146d8b98783da81f50ff3aa0e244e15e73dc099f2266d4ee2fc130375a1cf3341167c5c0586d179a0d6f622951a8e0fc895e4edf64bb1ec825496d2d85c826a263045936448e65d6608d729e8aeb3f8cf65a8addee9da3fe2b2ba4a0e6de6576a5221a372b64abb962d43a76c4519471d55c4425b57b3fef0f46bc07b1e1b4126cab307a91392cedd4fab180e6a943c648703e5058ea2aaa6aa3c1b019a9538e604a7581ea0f2b78b7ad3673313b8d926ab9ad21f10f2c3055732cf0b787838b61e5b85a079913a88cff7819d4066d551729495f62f0f4710cb0962d2460b57e5a5d09a316f7bdd937dd7f809b72c2e4b898648da7f7aea76ec34a016ab863705ad67458a497014e10e75f7d7710fc7784743cc30aa920ad10d24a82a074fa0db118dd5887c4346712f22b6d2e55e99769224338e00cd62030907f6df46f4b14bbd57d01102d02153fb569e432111eaafdd9bb68ff7d35f7590dff5a35eeea2bf69beae63c3e4e6fcbdc19d79f7bb919b2165aab76ce9cc9882ea258d9fd497168b5e9ed5ea3f323f94d5c6a6de663222b5971a8238121faeed83a8e"  # noqa: E501
        ),
        gas_limit=600000,
        value=0x5C537837,
    )

    post = {
        target: Account(storage={}, nonce=0),
        coinbase: Account(storage={}, nonce=0),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
