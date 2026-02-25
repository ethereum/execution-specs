"""
Ported from:
tests/static/state_tests/stRandom/randomStatetest211Filler.json

coinbase code:
    push1 0x00
    calldataload
    sload
    iszero
    push1 0x09
    jumpi
    stop
    jumpdest
    push1 0x20
    calldataload
    push1 0x00
    calldataload
    sstore

contract code:
    push31 0x7a980b5b1c50ebb63d8e2211d3a79e841ee5e5946b7969dfb6ca1309c99e8f
    push9 0xd4ee9a50996902ee4e
    push10 0x37e1d07ad872cf04eb2a
    push2 0xfc33
    push1 0x25
    log3
    push5 0x8d5818a645
    push30 0xc24f19f38d3deebb09968c812740339c6df46af95b7b0283acb1944a8ca3
    push32 0xbaaafeac115b9ec5adc16fea5a3a828d3483e495506a790ca75d8238ebbed647
    push29 0x213d0177c10b33b6cf9362273973809ac39f11dffee928f3fb18e97518
    push16 0xb4a74e56142d4431bfa392dd5f71d32b
    push13 0x40a2bd0beb6a8b24fc592b25f0
    push9 0x0306f11e049124ec39
    push15 0xa3858d3339145af8c1c16747bea056
    push4 0x9a7faf44
    push13 0xd9c7bf446ed2de67f1665adc47
    swap9
    push21 0x053c2c53f0fc53a12af3c1951fdc7a5d20aee8f968
    push21 0xf392a4aa2a84a99c9390ab4bd4c39f521a2b91c2ea
    swap1
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Environment,
    Hash,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["tests/static/state_tests/stRandom/randomStatetest211Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_random_statetest211(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x4f3f701464972e74606d6ea82d4d3080599a0e79")
    sender = Address("0x2e3d0156d2b99a6eacba540c55f423c8f5a33143")
    contract = Address("0xd7eb1ddc2f83f5620bd387bc6409be3cc2d2422f")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(
        balance=46,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.SLOAD + Op.ISZERO + Op.PUSH1[0x9]
        + Op.JUMPI + Op.STOP + Op.JUMPDEST + Op.PUSH1[0x20] + Op.CALLDATALOAD
        + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.SSTORE
    ),
    )
    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH31[0x7a980b5b1c50ebb63d8e2211d3a79e841ee5e5946b7969dfb6ca1309c99e8f]
        + Op.PUSH9[0xd4ee9a50996902ee4e] + Op.PUSH10[0x37e1d07ad872cf04eb2a]
        + Op.PUSH2[0xfc33] + Op.PUSH1[0x25] + Op.LOG3 + Op.PUSH5[0x8d5818a645]
        + Op.PUSH30[0xc24f19f38d3deebb09968c812740339c6df46af95b7b0283acb1944a8ca3]
        + Op.PUSH32[0xbaaafeac115b9ec5adc16fea5a3a828d3483e495506a790ca75d8238ebbed647]
        + Op.PUSH29[0x213d0177c10b33b6cf9362273973809ac39f11dffee928f3fb18e97518]
        + Op.PUSH16[0xb4a74e56142d4431bfa392dd5f71d32b]
        + Op.PUSH13[0x40a2bd0beb6a8b24fc592b25f0] + Op.PUSH9[0x306f11e049124ec39]
        + Op.PUSH15[0xa3858d3339145af8c1c16747bea056] + Op.PUSH4[0x9a7faf44]
        + Op.PUSH13[0xd9c7bf446ed2de67f1665adc47] + Op.SWAP9
        + Op.PUSH21[0x53c2c53f0fc53a12af3c1951fdc7a5d20aee8f968]
        + Op.PUSH21[0xf392a4aa2a84a99c9390ab4bd4c39f521a2b91c2ea] + Op.SWAP1
    ),
    )

    tx = Transaction(
        secret_key=Hash(
            "0xb1f4cbc3a50042184425a6f9e996d0910f7ba879457ce5dac5c71e498ad3c005"
        ),
        to=contract,
        data=bytes.fromhex(
            "7205d6a65458a0cdecda703b9d5440616f95b179076dfa7631cbf765dab81235497f97dd"
            "b6e8d399d5294ea49cfd736cdfa49a08a76dc08eff97542b54399a1b5f86b168d33cd083"
            "ac41074aa37e2f3f77a248d5db21a54d72c5053f2a79b2048d142fd588c56c48e39fa86b"
            "d16645ae7e31281c806dc847b38aba609fb88b5a3c6ce02d711bc1cb89419d740c65fcd7"
            "cd9abc94d8aaf97bfb874ed35e242cee6a462cac825efc8b53b43f7687a32b635c969cb7"
            "79fecda8dcbd0dd35ef6ab482083a8b91f6199bb8050971caa227ac9ad77edf44708d99a"
            "c08e92c8c1ff6e536a3eb4625c2d8c514c8a799391a90cb528870e725560136162fb2632"
            "b2485e26d9604de562740ee89a2a5b4b1976272d046167f2151feea60ecc547dc9dc31b9"
            "1ee0a712579874ebef218c4f015cbd8e76040f19d828eed7f9c070a127ce6067ad983136"
            "3977e2846559c8b97cfb3b0e8502cd54779657ab8571534f06e34b0d78259338706fac01"
            "057e66310e07ef4017629f7bf12ca747aafe8d7ccfcb78b5535dd267e3b445028e40113e"
            "1b9ccb7174b36264cfc5606cc1b4815c744393665f0a1c2ce78ff3679513083c95496a68"
            "69fe735535b8751fc5455769b44d7c9689576f2b76cb63bae9b5a47f8afd0c0466e798bf"
            "78d10b0efecc7e30695891cdc85e5f7a2827dc0b2ad41f92666faa9578ad77aa79aef036"
            "3cf4c69574bdfb74601f99ca8df4fbb481dd921b4b580a789e59c7557f305a1804f30d08"
            "c10394bc281772eef178800e0f79161010fdff6e028d5be7c0dfc295520e9b5f7fb781fb"
            "23ebd9657a42d8623d58350d43a9031a8b7e23c72ea3af0b137386987549539d695dd3e1"
            "9c2cac0855644773b40cae7e824e3912190e7a6aec7bb06e5c923de8750674988f11efac"
            "6aabfc209262900167c7c18e7826b18c6e65696c94c79ed8f574d69ffb0de2046a602f2e"
            "9eeb57a764e01cae63fc0e6c11703a61af60fd0c2a6af1e06d545b5ed713146d8b98783d"
            "a81f50ff3aa0e244e15e73dc099f2266d4ee2fc130375a1cf3341167c5c0586d179a0d6f"
            "622951a8e0fc895e4edf64bb1ec825496d2d85c826a263045936448e65d6608d729e8aeb"
            "3f8cf65a8addee9da3fe2b2ba4a0e6de6576a5221a372b64abb962d43a76c4519471d55c"
            "4425b57b3fef0f46bc07b1e1b4126cab307a91392cedd4fab180e6a943c648703e5058ea"
            "2aaa6aa3c1b019a9538e604a7581ea0f2b78b7ad3673313b8d926ab9ad21f10f2c305573"
            "2cf0b787838b61e5b85a079913a88cff7819d4066d551729495f62f0f4710cb0962d2460"
            "b57e5a5d09a316f7bdd937dd7f809b72c2e4b898648da7f7aea76ec34a016ab863705ad6"
            "7458a497014e10e75f7d7710fc7784743cc30aa920ad10d24a82a074fa0db118dd5887c4"
            "346712f22b6d2e55e99769224338e00cd62030907f6df46f4b14bbd57d01102d02153fb5"
            "69e432111eaafdd9bb68ff7d35f7590dff5a35eeea2bf69beae63c3e4e6fcbdc19d79f7b"
            "b919b2165aab76ce9cc9882ea258d9fd497168b5e9ed5ea3f323f94d5c6a6de663222b59"
            "71a8238121faeed83a8e"
        ),
        gas_limit=600000,
        gas_price=10,
        nonce=0,
        value=1548974135,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
