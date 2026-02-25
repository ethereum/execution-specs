"""
Ported from:
tests/static/state_tests/stRandom/randomStatetest150Filler.json

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
    push7 0x8254d76c6f24d4
    dup1
    push7 0x77d83f3a46a1a6
    push16 0x20ae2688cf4b75842ac7265966f5f5ca
    push1 0x3e
    push1 0x62
    log2
    push9 0xaba89067dc278e1f86
    push18 0x0462dae624ac683889038d26894af02617c0
    push12 0x39c4988a5a60a12c0d9ad0ca
    push6 0x839c92f7c75c
    push11 0xd3d6a7b617ac7fbd41f5a2
    swap4
    push24 0xca6ad48748a94e31302254147fb3b5857568e516cb6e8aa2
    calldataload
    push24 0xaf85d0e508dc17dc50e246130be577cb59826adc86af6c10
    push32 0xd8a98f47cccd9d22a867a43cd8ad77bbe8bb737af5acc0be67fd7b054f7281e7
    push18 0x891dc4aad180996b9cb71c6016d0f6a9148c
    push24 0x5e57ac8456a883eedc3182623898f32b5c83760465a2061c
    push23 0x52e785e7eef7a97b0aa6d6c15b5c296bcf05ee2e9b87aa
    ... (52 more instructions)
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
    sender = Address("0x2e3d0156d2b99a6eacba540c55f423c8f5a33143")
    contract = Address("0xa00c267da6e57a9318a096c6333c4bced51306da")

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
        Op.PUSH7[0x8254d76c6f24d4] + Op.DUP1 + Op.PUSH7[0x77d83f3a46a1a6]
        + Op.PUSH16[0x20ae2688cf4b75842ac7265966f5f5ca] + Op.PUSH1[0x3e]
        + Op.PUSH1[0x62] + Op.LOG2 + Op.PUSH9[0xaba89067dc278e1f86]
        + Op.PUSH18[0x462dae624ac683889038d26894af02617c0]
        + Op.PUSH12[0x39c4988a5a60a12c0d9ad0ca] + Op.PUSH6[0x839c92f7c75c]
        + Op.PUSH11[0xd3d6a7b617ac7fbd41f5a2] + Op.SWAP4
        + Op.PUSH24[0xca6ad48748a94e31302254147fb3b5857568e516cb6e8aa2]
        + Op.CALLDATALOAD
        + Op.PUSH24[0xaf85d0e508dc17dc50e246130be577cb59826adc86af6c10]
        + Op.PUSH32[0xd8a98f47cccd9d22a867a43cd8ad77bbe8bb737af5acc0be67fd7b054f7281e7]
        + Op.PUSH18[0x891dc4aad180996b9cb71c6016d0f6a9148c]
        + Op.PUSH24[0x5e57ac8456a883eedc3182623898f32b5c83760465a2061c]
        + Op.PUSH23[0x52e785e7eef7a97b0aa6d6c15b5c296bcf05ee2e9b87aa] + Op.PUSH1[0xb5]
        + Op.PUSH21[0x1b3f7d69a1df03df117b848b3a75f81c12dee2244f]
        + Op.PUSH23[0xe56bb261e9c75fb5ccc769db72bfaeadee3f68cf22bbca]
        + Op.PUSH7[0x5b0647ac74c140] + Op.SWAP8
        + Op.PUSH25[0xc71b73ed4adaa2c6ba1c181b0747c27506478c403b3943129e]
        + Op.PUSH26[0x223e788bf8b81f60abecb73be035d03a8bbdfa112cd8cb2f7a10]
        + Op.PUSH6[0x250292740d2d]
        + Op.PUSH19[0x259b4d7e3ef844783da8118b72912b9f96a61f] + Op.PUSH2[0x68f1]
        + Op.PUSH1[0xef] + Op.PUSH10[0xd7dd3dfc7e4ef204766f]
        + Op.PUSH25[0x9cbaf2abeceadcf5bdd8dddfef773f0a628afdf3988861662b]
        + Op.PUSH24[0x882a5cebffc61e75f11835b109e81f7c915a91c13b09097b]
        + Op.PUSH26[0x2d3d59de0ef5b0f00f95ea49860917656263925da2fd6685359c]
        + Op.PUSH14[0x7e4c3c4d2001a30111de14c56503]
        + Op.PUSH25[0x8453df98a29b8715561b2c2021cf78e0ccc4701b192ebf67bb]
        + Op.PUSH16[0x522656788b3d21428b50a2fa16224d92]
        + Op.PUSH13[0xe2ea5944760d501bfa0774238c] + Op.PUSH4[0x51dd224b]
        + Op.PUSH21[0x3d3fc4d5a309166016a71b1c230fe9afd647932471]
        + Op.PUSH15[0x71e3b27bdd3fb18cccc42f6ec97312] + Op.SWAP16
        + Op.PUSH26[0x58435f45da181aeb1608ed31713c33330ab4d2d4af54dd92d1df]
        + Op.ISZERO + Op.PUSH1[0x8] + Op.PUSH1[0x14] + Op.PUSH1[0x1d] + Op.PUSH1[0x1f]
        + Op.PUSH4[0x6b1d9a35] + Op.PUSH20[0xa00c267da6e57a9318a096c6333c4bced51306da]
        + Op.PUSH4[0x2aec0540] + Op.CALL + Op.PUSH13[0xfb040c16bd7c3761bdb86dd6be]
        + Op.PUSH6[0x8d2aefe15739] + Op.PUSH3[0x173936] + Op.PUSH4[0x769965a6]
        + Op.PUSH5[0x79176d702e]
        + Op.PUSH31[0x2d5697681aac1beccc55825241cd77551f39526cfa77838faa9c4759aafa5c]
        + Op.PUSH5[0xdf5e919997] + Op.PUSH16[0x35f8298acd398d1913c1fd2ddacbbeac]
        + Op.PUSH29[0xc29daee12c057385808f19d07110f30cfd900a130b0a713468bceaf423]
        + Op.PUSH2[0x53ab] + Op.PUSH13[0x7bdc39cf86d0a5b03684624d18]
        + Op.PUSH21[0x73b42a2968f1128872724b3d42218dbac11f5a9492]
        + Op.PUSH6[0x1f09a866f61a]
        + Op.PUSH19[0x535c373274618d5914163abc7481bb7789394e] + Op.PUSH3[0xf247e7]
        + Op.DUP15
        + Op.PUSH32[0x83af55a5686926972af7c6519658aee40a564e3c2950f874def7a2110af0526f]
        + Op.PUSH22[0x629b20a108e1cfba0db03fcdee497ee2f8bcf78ef143] + Op.OR
    ),
    )

    tx = Transaction(
        secret_key=Hash(
            "0xb1f4cbc3a50042184425a6f9e996d0910f7ba879457ce5dac5c71e498ad3c005"
        ),
        to=contract,
        data=bytes.fromhex(
            "70afe04f9b9074d39383f0718bb0b14ecdb6680c54b4c20ae65044c572a5c832c15f55e8"
            "c1b63ffbb7da41d4c8faa43f087b1960b54938bbdb14f35e3552723ad2053a3c74b98d03"
            "20f74bbe4ff06630f30e1caa6e13797a14d07bb94ae4972ce38da7aefa2ab07aedb81397"
            "137b698a63675aa8895c5b1207be9262507b0866acfa180cfbbdff5572fb9a74b245d118"
            "0e80a93b2dc5bcf891e1b84d6c66ab13b03e937d4268f4e9be0381417c1db9b7341c9912"
            "e685e38ee499f1fb82b027b84e01ef235f18b95b0bf567fcfcc5181f51c6dd0465d063d0"
            "f11f267ccd81aa8d4fda65e7e213e5ae4a6da0c6493209753a089323c5bfdde091556681"
            "b0648f59b8b2684d82a240f7d5b8eefd645e6320270660e960467877a8561129b7114a61"
            "7d36423905813b7dc594d88b0eb751ba946f54595f624b07da116f0971fc6e540a966364"
            "c8a1df698688b1ba91f9ac7a74f878a61c87ad3240d656c9ee80fd90d4f8c01ca89c8bc5"
            "37380df079ba8a2e6f2a3cbeb6bfb9687a7cc323f2a9eafd81789ae783355764b23354ba"
            "3f693c4d774ed6ab89da8846604172ad96ab938a4beff64adf9594812f491a0ba98e6f77"
            "d4c40454047c20cfb2625c43608dc26d032e6f8b53bfc1243fbd23a14c077e2071997635"
            "fdb2ffb317cd0e116f1ea7649dcf80ead9dea010cc4e456893f16d7c534f980d27c3312f"
            "34fbf5c8ba9b"
        ),
        gas_limit=2042667010,
        gas_price=10,
        nonce=0,
        value=1816460087,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
