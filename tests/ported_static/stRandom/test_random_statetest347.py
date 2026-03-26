"""
test_random_statetest347

Ported from:
state_tests/stRandom/randomStatetest347Filler.json
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
    ["state_tests/stRandom/randomStatetest347Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_random_statetest347(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_random_statetest347"""
    coinbase = Address("0xa7f7c8ef9bbbcfb0f7e81c1fd46bb732fba60592")
    sender = EOA(
        key=0x1f2f6944f70460e655546d414267bd3491a2dd9dafb2280605404c858990d053
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=188473852,
    )

    # Source: raw
    # 0x64d552603c577e9a3805d8c55157a82b7660ef2a049cfbf79c15fa8e3261f121d213590fa3917d7d442a5e8734af2aaa4c859b452eed7860c2f7e051580427b6c3cc6d7fee617a0d64ef63e192256de5d2ea2689decfd971c7478effb06aa9e792747ce0492abde8c2f270e93d5ed0b213fed7ae59294537d4864c0e68bbe30ec5d1e6b854027862cfcbea15e8367dfaa080ee0da2b0d2ca892f5a764354370466ccddd03115ec8a7ad2e6c62c29425a45ec842fb74c369fb15a42e4b4e48b3eb70be2a0847469987980e6eaa539365a491d2366334f78f03acb177809e7525add39a234d3d2ef1cf8544a52389411ef846d3cd7f36d0d1db7f414860020171f07598cfb620e15a9681c843d60aee9fb8a4e7e37713afbf6ef9d1667513975c76f26ac35ce209b1e0a3bb7c19821368931537b4095ea42b32baf1ba596b9af5cce961ae705f8c9c5465e349633529871f64351169e7fe48ccbb866952fabbfcf40df723c564e109dbd4c9c15ee9ad625e96a5765f6f56ee0601677961da7ebad5f583f6eb6da7c8348425fe784f532f288963ccdbf9de3ac3ebc38b75a806b40e51b895c662d0bcab255a04b723f1e500517d17eb720e02f445cb046bd0fe7d2759438c79aa2dfcaef1cf57e4eb9c832f7ef449a9c32f673728f4b0dccdfa8fb1d447e2f681076ac51a98f76600a66b4692ca7e1e9c89f64cdf879cb0c625514977ebca28f2ec8bb3a092bd0c30849558fe16a4b7070cb05aec329c0286c26fff57795ce4ac7601160ea2d6656c8f2a554b43e263cc3a60e9fd0a26c0a5f7202f02888a731e84ab326610c77771f85025eb8c552943d2da5de48786015f5b8b5921d26c1e277d5a4cda5f1f77ec5f3a83e6ed6821ff025370e2fad05a0f364f58f3705c8761904d63e0f2e5bdbe2b0b1ddf82bb441c547634e8c1864737333e845ffa373c102303f727bfa14f4c445711f6f9695c36f3627df02a1fe2d7eca55faed6984000ab2a99545148bbe7369a47367bc24256acd6a3a22d5fb32434b1998297ae6b2edf08b72dc4598aa600e16707699a84e55ef611ea0e6da482f6c6e9d05d54bbb4ad06cd62622e469fbcd3e637a8f0d2ac9149b7076cce991cb5d4b4de1229e3decbcf46a3c7e46aa1fdc218d936e56f55b5a38bbd798361040e1badb1ab06adc38a723badfa07a95f78553de4df879855274a1904a31276d7938818021e69d8f5b9279478808a236deefd761df6bc151fded80bbe4ba725e7db7b9fc507f0b8121a009384c7bc4443747bd1ac9dc7682b32bec0937c7fb27ba3926acd0d67b41ba6c951788f1bb1b1168229d15cafdc63209c95df646566024013d766a01d6b8051c357243c9f464f423a2ae8efa4f9efd95777099eac9b0825d18018a5afcb6cecd9ab9a9655ae262db08a271d8adedbc3e7eb6acfd2d576ec297c09c4bd47a80dacd2b123e4e4e6232ef6d70acb10f2f44a62bbcef65a72576506ea119b051880b515f4414920badcd6f726c04e821516f6123c9c52f29e19bfe0fb10fab76536535cc0e01115c83369d4083db2d669654c2fe8c00e37bd78f663a2ce2425d2ce358e213d6c601208bb644fa656678de7633147fbd152c2ae682dec269245f07ba3c79f4e6e1978d40f42a494d44eba128b9d0228d637900cbab73455423156417fae331d26494d1ed4d06ecf206736f04292d5470d5091c48a80ba737372c35729c829af30db3625785ba0b3cfc4240d002276760f2770ead609b52db934a53063ec1c05488188fb37ce61059909b6c975c0e9401ef3b71b6d0ddae39867f3f0878bd172851a98a233fcafae289fc634c36c8b3064926d92deda3d8c5074d6a56daa511e7e693aab3d4347cebdd5b63238acdeedc3d8eb8f69ea18cb429ee8f09c26845507ba28eba916c74fd62cd9e587a8f013122d93579b6b7da091527251a4b70051be4f0f96f61e5dc4ab713c473174c7e2ebb463615b03c4787b74e8c204975399439fa553838f186ae028a47f3ccd46c5fcc46c11a36219f3ba1d34def7bee989fa61e60a2abd3652df9f8e5a1b53d9608e3bb04f5e852333d9c7d761836ef5761178bd07fde9a0ded16e1659a6c80281c259ce42e3fdbe23664ce783b58d595
    target = pre.deploy_contract(
        code=Op.CALLCODE(gas=0xa9e792747ce0492abde8c2, address=0xe5d2ea2689decfd971c7478effb0, value=0xef63e19225, args_offset=0x7a0d, args_size=0x7d442a5e8734af2aaa4c859b452eed7860c2f7e051580427b6c3cc6d7fee, ret_offset=0x9a3805d8c55157a82b7660ef2a049cfbf79c15fa8e3261f121d213590fa391, ret_size=0xd552603c57)
        + Op.PUSH17[0xe93d5ed0b213fed7ae59294537d4864c0e]
        + Op.PUSH9[0xbbe30ec5d1e6b85402]
        + Op.PUSH25[0x62cfcbea15e8367dfaa080ee0da2b0d2ca892f5a7643543704]
        + Op.PUSH7[0xccddd03115ec8a]
        + Op.PUSH27[0xd2e6c62c29425a45ec842fb74c369fb15a42e4b4e48b3eb70be2a0]
        + Op.DUP5 + Op.PUSH21[0x69987980e6eaa539365a491d2366334f78f03acb17]
        + Op.PUSH25[0x9e7525add39a234d3d2ef1cf8544a52389411ef846d3cd7f3]
        + Op.PUSH14[0xd1db7f414860020171f07598cfb] + Op.PUSH3[0xe15a9]
        + Op.PUSH9[0x1c843d60aee9fb8a4e]
        + Op.PUSH31[0x37713afbf6ef9d1667513975c76f26ac35ce209b1e0a3bb7c1982136893153]
        + Op.PUSH28[0x4095ea42b32baf1ba596b9af5cce961ae705f8c9c5465e3496335298]
        + Op.PUSH18[0xf64351169e7fe48ccbb866952fabbfcf40df]
        + Op.PUSH19[0x3c564e109dbd4c9c15ee9ad625e96a5765f6f5]
        + Op.PUSH15[0xe0601677961da7ebad5f583f6eb6da]
        + Op.PUSH29[0x8348425fe784f532f288963ccdbf9de3ac3ebc38b75a806b40e51b895c]
        + Op.PUSH7[0x2d0bcab255a04b]
        + Op.PUSH19[0x3f1e500517d17eb720e02f445cb046bd0fe7d2]
        + Op.PUSH22[0x9438c79aa2dfcaef1cf57e4eb9c832f7ef449a9c32f6]
        + Op.PUSH20[0x728f4b0dccdfa8fb1d447e2f681076ac51a98f76] + Op.PUSH1[0xa]
        + Op.PUSH7[0xb4692ca7e1e9c8] + Op.SWAP16
        + Op.LOG2(offset=0x95ce4ac7601160ea2d6656c8f2a554b43e263cc3a60e9fd0, size=0xbca28f2ec8bb3a092bd0c30849558fe16a4b7070cb05aec329c0286c26fff5, topic_1=0x551497, topic_2=0xcdf879cb0c)
        + Op.PUSH13[0xa5f7202f02888a731e84ab326] + Op.PUSH2[0xc77]
        + Op.PUSH24[0x1f85025eb8c552943d2da5de48786015f5b8b5921d26c1e2]
        + Op.PUSH24[0xd5a4cda5f1f77ec5f3a83e6ed6821ff025370e2fad05a0f3]
        + Op.PUSH5[0xf58f3705c8]
        + Op.PUSH23[0x1904d63e0f2e5bdbe2b0b1ddf82bb441c547634e8c1864]
        + Op.PUSH20[0x7333e845ffa373c102303f727bfa14f4c445711f]
        + Op.PUSH16[0x9695c36f3627df02a1fe2d7eca55faed]
        + Op.PUSH10[0x84000ab2a99545148bbe]
        + Op.PUSH20[0x69a47367bc24256acd6a3a22d5fb32434b199829]
        + Op.PUSH27[0xe6b2edf08b72dc4598aa600e16707699a84e55ef611ea0e6da482f]
        + Op.PUSH13[0x6e9d05d54bbb4ad06cd62622e4]
        + Op.PUSH10[0xfbcd3e637a8f0d2ac914] + Op.SWAP12
        + Op.LOG0(offset=0x46aa1fdc218d936e56f55b5a38bbd798361040e1badb1ab06adc38a723badf, size=0x76cce991cb5d4b4de1229e3decbcf46a3c)
        + Op.PUSH27[0x95f78553de4df879855274a1904a31276d7938818021e69d8f5b92]
        + Op.PUSH26[0x478808a236deefd761df6bc151fded80bbe4ba725e7db7b9fc50]
        + Op.PUSH32[0xb8121a009384c7bc4443747bd1ac9dc7682b32bec0937c7fb27ba3926acd0d6]
        + Op.PUSH28[0x41ba6c951788f1bb1b1168229d15cafdc63209c95df646566024013d]
        + Op.PUSH23[0x6a01d6b8051c357243c9f464f423a2ae8efa4f9efd9577]
        + Op.PUSH17[0x99eac9b0825d18018a5afcb6cecd9ab9a9]
        + Op.PUSH6[0x5ae262db08a2]
        + Op.PUSH18[0xd8adedbc3e7eb6acfd2d576ec297c09c4bd4]
        + Op.PUSH27[0x80dacd2b123e4e4e6232ef6d70acb10f2f44a62bbcef65a7257650]
        + Op.PUSH15[0xa119b051880b515f4414920badcd6f]
        + Op.PUSH19[0x6c04e821516f6123c9c52f29e19bfe0fb10fab]
        + Op.PUSH23[0x536535cc0e01115c83369d4083db2d669654c2fe8c00e3]
        + Op.PUSH28[0xd78f663a2ce2425d2ce358e213d6c601208bb644fa656678de763314]
        + Op.PUSH32[0xbd152c2ae682dec269245f07ba3c79f4e6e1978d40f42a494d44eba128b9d022]
        + Op.DUP14 + Op.PUSH4[0x7900cbab]
        + Op.PUSH20[0x455423156417fae331d26494d1ed4d06ecf20673]
        + Op.PUSH16[0x4292d5470d5091c48a80ba737372c35]
        + Op.PUSH19[0x9c829af30db3625785ba0b3cfc4240d0022767] + Op.PUSH1[0xf2]
        + Op.PUSH24[0xead609b52db934a53063ec1c05488188fb37ce61059909b]
        + Op.PUSH13[0x975c0e9401ef3b71b6d0ddae39] + Op.DUP7
        + Op.PUSH32[0x3f0878bd172851a98a233fcafae289fc634c36c8b3064926d92deda3d8c5074d]
        + Op.PUSH11[0x56daa511e7e693aab3d434]
        + Op.PUSH29[0xebdd5b63238acdeedc3d8eb8f69ea18cb429ee8f09c26845507ba28eba]
        + Op.SWAP2 + Op.PUSH13[0x74fd62cd9e587a8f013122d935]
        + Op.PUSH26[0xb6b7da091527251a4b70051be4f0f96f61e5dc4ab713c473174c]
        + Op.PUSH31[0x2ebb463615b03c4787b74e8c204975399439fa553838f186ae028a47f3ccd4]
        + Op.PUSH13[0x5fcc46c11a36219f3ba1d34def]
        + Op.PUSH28[0xee989fa61e60a2abd3652df9f8e5a1b53d9608e3bb04f5e852333d9c]
        + Op.PUSH30[0x761836ef5761178bd07fde9a0ded16e1659a6c80281c259ce42e3fdbe236]
        + Op.PUSH5[0xce783b58d5] + Op.SWAP6,
        balance=0x33498455,
        nonce=233,
        address=Address("0x97bc67b6ee773e59e516d02edb13b971c3cbd856"),  # noqa: E501
    )
    # Source: raw
    # 0x36
    addr_0x945304eb96065b2a98b57a48a06ae28d285a71b5 = pre.deploy_contract(
        code=Op.CALLDATASIZE,
        balance=0x4ea91708,
        nonce=89,
        address=Address("0x79d9fbe6ac70917cb2e16ec4cd32968ce19c724d"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x1024d289465fa51769)


    tx = Transaction(
        sender=sender,
        to=target,
        data=bytes.fromhex("73151af76abac2a99afe60eff5cfd8f68daf1b35e0608a690494ef4b1d043bf90e00916acf5f0332c3ef3aa972eba960aa557dc165d1a3c726953fc637fe643a60543de4159f3bc09673cd054235ddb44769fa2d6edb61b6e71feff2662043418ac9d2337bce1df4b842fbf8f07395b44bb506e8955d22a12176e2fb8e25bc546d77a6f5049a09f3126c915f14979d8c7c0cf88425567c6b8a6865b78e6d76208a641cb0d0651a758d9afdd5e36b2dcf740a8a1e2b19ebb0bc8ad6ac032577f3b5d483e40d0c9a40aaf32cebc478c0962e1ac5f6c648f47665f0850054ab4caab6eca1a24242087387c96452ad72e76a42a175db6c69a2d8cbcd70759249b040a797894765385557e947875851cfe9734edc8b613cbb6bf40b41b762fa3bcbc6b59ecc66971fef9e8ed16d691702b224f0e2f8ad12577a943401f57334d3207b884a40ed472960f03e4cab61c98268b5a73b6372ab45a7a4"),  # noqa: E501
        gas_limit=8653299,
        value=0x7f3e3a6ac8834e68,
        nonce=0,
        gas_price=29,
    )

    post = {
        target: Account(storage={}, nonce=233),
        addr_0x945304eb96065b2a98b57a48a06ae28d285a71b5: Account(storage={}, code=bytes.fromhex("36"), nonce=89),  # noqa: E501
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
