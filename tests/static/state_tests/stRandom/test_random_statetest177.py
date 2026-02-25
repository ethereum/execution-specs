"""
Ported from:
tests/static/state_tests/stRandom/randomStatetest177Filler.json

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
    push31 0x24654d920bee1c2af8b3225f6035ea04b87e1d3f2486057268ed05d8d6e5a6
    push32 0x3da4409848b450c9ab9713bf10ec5124e50fda175accc13d0db75bbc03a25a06
    push14 0x85332a97eae6e7219bc62ce53f23
    push10 0x0f1df7f7b11c1659165b
    push29 0x438533bc1f73a59ae2c28e633d8c971763576dd25386518678a15c64a2
    push9 0x2c68bf3c1a7433af2e
    push14 0xd0276f494254235fe7b28b1f9976
    push2 0xeba4
    push23 0x7c05f37a8b9b7980106e2bbe8744bed6d0f782ac6a99e0
    push30 0x9486451ab20e48c9e99f083973d5a10a57f4c3e7e3fa3bfd63a39006f35f
    push20 0x25ae8b67348d74c87e78d6dc699541fdf8d08569
    push31 0x58b02f9fef3f78554901cc888449b92fe07e74fb3069f7be725f408005886e
    push20 0xe720275f04f63284f6f10b6df25694b3a55936d0
    push15 0xd8c18d03d868d30b7766bd0d6a111f
    push20 0x4650113a9f6b31ef3be38904ccd66a304bbf877e
    swap14
    push13 0xcc3e98fa65a685b0bf181c6dd6
    push29 0x9db728914ff2977b8c19193f67b9053f72c819b5bc5542945bd6a90799
    push6 0xd91f47a11f38
    push3 0xd346cb
    ... (62 more instructions)
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
    ["tests/static/state_tests/stRandom/randomStatetest177Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_random_statetest177(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x4f3f701464972e74606d6ea82d4d3080599a0e79")
    sender = Address("0x2e3d0156d2b99a6eacba540c55f423c8f5a33143")
    contract = Address("0xd18174aba5b877bd17dc67a4272d8a567cfa8925")

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
        Op.PUSH31[0x24654d920bee1c2af8b3225f6035ea04b87e1d3f2486057268ed05d8d6e5a6]
        + Op.PUSH32[0x3da4409848b450c9ab9713bf10ec5124e50fda175accc13d0db75bbc03a25a06]
        + Op.PUSH14[0x85332a97eae6e7219bc62ce53f23] + Op.PUSH10[0xf1df7f7b11c1659165b]
        + Op.PUSH29[0x438533bc1f73a59ae2c28e633d8c971763576dd25386518678a15c64a2]
        + Op.PUSH9[0x2c68bf3c1a7433af2e] + Op.PUSH14[0xd0276f494254235fe7b28b1f9976]
        + Op.PUSH2[0xeba4]
        + Op.PUSH23[0x7c05f37a8b9b7980106e2bbe8744bed6d0f782ac6a99e0]
        + Op.PUSH30[0x9486451ab20e48c9e99f083973d5a10a57f4c3e7e3fa3bfd63a39006f35f]
        + Op.PUSH20[0x25ae8b67348d74c87e78d6dc699541fdf8d08569]
        + Op.PUSH31[0x58b02f9fef3f78554901cc888449b92fe07e74fb3069f7be725f408005886e]
        + Op.PUSH20[0xe720275f04f63284f6f10b6df25694b3a55936d0]
        + Op.PUSH15[0xd8c18d03d868d30b7766bd0d6a111f]
        + Op.PUSH20[0x4650113a9f6b31ef3be38904ccd66a304bbf877e] + Op.SWAP14
        + Op.PUSH13[0xcc3e98fa65a685b0bf181c6dd6]
        + Op.PUSH29[0x9db728914ff2977b8c19193f67b9053f72c819b5bc5542945bd6a90799]
        + Op.PUSH6[0xd91f47a11f38] + Op.PUSH3[0xd346cb]
        + Op.PUSH12[0x70d29eca71b0d12d01996b89]
        + Op.PUSH23[0x3f13059617d671ddc626d93a3e3fda99999484470e3427]
        + Op.PUSH32[0x9ac904a6be6b8b9f0a91e98e2759a946222e419d34089491db069bbeeea7d198]
        + Op.PUSH9[0xe6fef55cd7440fbbdd]
        + Op.PUSH28[0xf7cab153de2f407fc2c1f51952d5d5388159f73c98deb0a3f75d04eb]
        + Op.PUSH17[0xcee4f3dd886b6ba2ab3d1e110db841c507]
        + Op.PUSH8[0xa4e0ed4abca1bd1d] + Op.PUSH7[0x88861c4bb169fa] + Op.DUP12
        + Op.PUSH4[0xd253f1a4] + Op.PUSH4[0x6a397939]
        + Op.PUSH10[0x65ae9c16c2197c57851d] + Op.PUSH9[0xf1ee6fff3c92e794d0]
        + Op.PUSH29[0xc6d2f5b964448fee1c3f52921cd138bfe26f57a3ce26ae8e622c80fcfb]
        + Op.PUSH32[0x414b5750048e67dd2c715bdf907a881ef7a77dc8b166b413ebb4261bda628c26]
        + Op.PUSH7[0x6d7ec3d2d20bdc]
        + Op.PUSH31[0x117960da38d995574327fc1b63764875b839f395793a937b5f2793db93b23b]
        + Op.PUSH18[0x60bb44cf7bf515a85769d5f51851260f0739]
        + Op.PUSH10[0xb185817c3e5b65875394]
        + Op.PUSH32[0x6ae534b0e68afa57a476ff52028737e7d342c1ddc7c5dc786fe6216838882c6f]
        + Op.PUSH15[0x8519b16b2d9451ea2f048765576af4] + Op.PUSH2[0xaab4]
        + Op.PUSH3[0x31f6a] + Op.PUSH5[0xf0ae07fa9a] + Op.PUSH5[0xd4772252eb]
        + Op.SWAP15 + Op.PUSH11[0xa14429a7e2a1d434826990] + Op.PUSH6[0xe44695fbea17]
        + Op.PUSH14[0x63d01d22231d221b6f8dfda47f51] + Op.PUSH5[0xa47454ab39]
        + Op.PUSH16[0x17257ddec269f67ed7c6d17ffac1c613]
        + Op.PUSH19[0xaaf587427eee43772c5f28fde9d395b65bf2d7]
        + Op.PUSH31[0x4eaa635bea61396414a53508797e2506ed2f921f29bf2fda1796f4396c4edb]
        + Op.PUSH16[0x6ecc6d79fd82d9838a512df1454ce722]
        + Op.PUSH9[0xd8a32e0971c718b683] + Op.PUSH15[0x4bcb788766f266a3edfdd24686274f]
        + Op.PUSH9[0x4c4b0a7fd708215976]
        + Op.PUSH16[0x4670a09a9e231bf61fe5f955a75b8870]
        + Op.PUSH21[0x4ec89c81940d46be921c40917862e1c186679f354a]
        + Op.PUSH17[0x4fd5537ceb310616acf9779c43c8f585c0] + Op.PUSH5[0xfafa775d27]
        + Op.SWAP14 + Op.PUSH3[0xaec380] + Op.PUSH3[0x5fc16d] + Op.PUSH1[0x1e]
        + Op.CREATE + Op.PUSH8[0xeddffdf0f1359f38] + Op.PUSH10[0x70fe2eb95c063421601a]
        + Op.PUSH27[0x5f9256a6398651be88998deb83d16edd603992a27f758bda8c1bf9]
        + Op.PUSH21[0xe49a52cf19c9bc32a79db4778535677e3caeae7f2f]
        + Op.PUSH11[0xc54f147d2729c30d694bcb] + Op.PUSH3[0x2c1310]
        + Op.PUSH13[0x3382d4c27bc4ee55eadb4921d9]
        + Op.PUSH26[0x65e605bd3daa1c233230119dce876049813474dc4b3ec1d0ea8d]
        + Op.PUSH20[0xd182beb19cd3c8f198578d863907a60fd633a658]
        + Op.PUSH19[0xd93e47dc134fc815d9800bad3f2d58bb97b577]
        + Op.PUSH16[0x42800f1f182951ba5aced03a7c3abd85] + Op.SWAP10
        + Op.PUSH10[0x483189606297788fbf55] + Op.PUSH6[0x10d13f07077]
        + Op.PUSH22[0x2867293dbfe29b7346020ef70d18cacd7508ccb3731b] + Op.CODECOPY
    ),
    )

    tx = Transaction(
        secret_key=Hash(
            "0xb1f4cbc3a50042184425a6f9e996d0910f7ba879457ce5dac5c71e498ad3c005"
        ),
        to=contract,
        data=bytes.fromhex(
            "387814bf0652a6f3aefce6ef7be00599328bbf7e802e1ea22644a96fbf319d273c0e7150"
            "67e4e5e74ecfc3ae60fd917b9224a4bbaa6db919506fc9e3cd4792dbecb1427e907653a3"
            "e359acf57c1e4afae77816fdc406706133e14efc6fe3ed1dc01f663f8e79c5fb6a32685e"
            "c748da76ab766d20766430b1775afa280f1c02e5617230d3b68fa16d4d73a1b27ae07b10"
            "96d44b02414374765d0907504a2f25e45aee4fdbb17b244e93714f36d9c035346d67ce3c"
            "18bf3d3af42f3b5f807689e8f429c0070a5812d602d25c4664cccfa7ddff8188f174c046"
            "eef00dcd5355c37d900a2ce940246fcaada0526acdd4eaf98a420bae34e22b37"
        ),
        gas_limit=100000,
        gas_price=10,
        nonce=0,
        value=1928806571,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
