"""
Ported from:
tests/static/state_tests/stRandom2/randomStatetest467Filler.json

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
    push17 0x0ab6605e03171122aeebd20b63699a72d4
    sload
    push3 0x863934
    push16 0xfaf92bcd1855c6dde5c90ba78a966a25
    push13 0x777ce8880c23f90f4a2ecc999a
    push13 0xd42da7121d5e1fde1c9c340f96
    push1 0xb5
    push18 0xa71e20a5753bc4e291adbd41a228289a0be1
    push22 0xa606bc44dd2079ece46a2cba498bee0d80a41673d801
    push15 0x7232f97a66b29954364570f6e2d08b
    push14 0x429c6a75f737c594aca21580bc0d
    push1 0xe6
    push29 0x38a50ce1ddf0ce9963fd79da8a590429f5fcfb6e7fd9ee2d27201f9570
    push19 0x35ce3dbc5997e44baa174111977f51dc6b333a
    swap11
    push4 0x483e6a3d
    push16 0x423ed5778057702664b65d4af9aab14d
    push24 0x3a787d60bd24c439b29533c6b172278b6a78e64f8e319fbd
    push12 0x45eeca466afd1eb2eecbaeed
    push24 0x3da8711c4c65787e0a0a1297f525b7418f49fbc1b2446a84
    ... (29 more instructions)
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
    ["tests/static/state_tests/stRandom2/randomStatetest467Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.pre_alloc_mutable
def test_random_statetest467(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x4f3f701464972e74606d6ea82d4d3080599a0e79")
    sender = Address("0x2e3d0156d2b99a6eacba540c55f423c8f5a33143")
    contract = Address("0x79940e2f1225eba4fab3405b111535075c733270")

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
        Op.PUSH17[0xab6605e03171122aeebd20b63699a72d4] + Op.SLOAD
        + Op.PUSH3[0x863934] + Op.PUSH16[0xfaf92bcd1855c6dde5c90ba78a966a25]
        + Op.PUSH13[0x777ce8880c23f90f4a2ecc999a]
        + Op.PUSH13[0xd42da7121d5e1fde1c9c340f96] + Op.PUSH1[0xb5]
        + Op.PUSH18[0xa71e20a5753bc4e291adbd41a228289a0be1]
        + Op.PUSH22[0xa606bc44dd2079ece46a2cba498bee0d80a41673d801]
        + Op.PUSH15[0x7232f97a66b29954364570f6e2d08b]
        + Op.PUSH14[0x429c6a75f737c594aca21580bc0d] + Op.PUSH1[0xe6]
        + Op.PUSH29[0x38a50ce1ddf0ce9963fd79da8a590429f5fcfb6e7fd9ee2d27201f9570]
        + Op.PUSH19[0x35ce3dbc5997e44baa174111977f51dc6b333a] + Op.SWAP11
        + Op.PUSH4[0x483e6a3d] + Op.PUSH16[0x423ed5778057702664b65d4af9aab14d]
        + Op.PUSH24[0x3a787d60bd24c439b29533c6b172278b6a78e64f8e319fbd]
        + Op.PUSH12[0x45eeca466afd1eb2eecbaeed]
        + Op.PUSH24[0x3da8711c4c65787e0a0a1297f525b7418f49fbc1b2446a84]
        + Op.PUSH30[0x74bb0a66e3b06ef70d8a8aa09a910a6be623c6a8239960381512da962eb8]
        + Op.PUSH9[0xa21f99d90741128fcb]
        + Op.PUSH18[0x1e029cff42f4f8f5d35947c4a7b39cff7fd4]
        + Op.PUSH16[0x916cc8612b146bbf52db1cd36e6c2fce]
        + Op.PUSH29[0xd9ed232e21946081d78d87e61bc42fce313fa32b458d1e898e52cc2e60]
        + Op.PUSH22[0x70a7e1d2ae3b5b7d58e0a70396bcfaae0789cd920287]
        + Op.PUSH5[0x88bb595d45]
        + Op.PUSH27[0x45bc48e190f5d56b34be6d244070ffe02107ceaf9313db08d9a180]
        + Op.SWAP12 + Op.CALLDATASIZE + Op.PUSH16[0xc956e6c5567da1d8a656406871eb0dd4]
        + Op.PUSH3[0x68b512] + Op.PUSH20[0x66225cb464667bd081c949847a95e2821f589dad]
        + Op.PUSH1[0xc0] + Op.PUSH2[0xef2f] + Op.LOG3
        + Op.PUSH12[0x9e17c2b3a94181a8f8a89b48] + Op.PUSH8[0x34ca1a8a0c86c26d]
        + Op.SMOD + Op.PUSH1[0x4] + Op.PUSH1[0x11] + Op.PUSH1[0x6] + Op.PUSH1[0x12]
        + Op.PUSH4[0x5e0d7386] + Op.PUSH20[0x79940e2f1225eba4fab3405b111535075c733270]
        + Op.PUSH4[0x6158e2e1] + Op.CALL + Op.PUSH7[0xe10de5d5905723]
        + Op.CALLDATALOAD
    ),
    )

    tx = Transaction(
        secret_key=Hash(
            "0xb1f4cbc3a50042184425a6f9e996d0910f7ba879457ce5dac5c71e498ad3c005"
        ),
        to=contract,
        data=bytes.fromhex(
            "6f42af68ebb8fbfe65896d2993c75a18b06dbf26336197db938986312c4ea88b7aab8c2c"
            "d436a05c5b765989d8ad6c97257fe7c4f1f33d9644b8e03c6898c8946d19a4dfed187482"
            "dd95f88ea4f0c43f39f4ab261808bf1b1f658f0979b867eeb00baeadab37700449f87952"
            "2b0bba9c6f2d87d2541b0b943275c57530b3790b225dd318baeca448b045ccf1477837e4"
            "156d992ad881869b91a5f7f71de5884a703c659316ab330af945c7fd906936c695fe7913"
            "4e48e46153702e81da6d3da14e05b90ae63b037d7b9e4fb17367c1e737162043aa587f4b"
            "b580e87cfaad897bc8e3152e3741f1ba345cc4c762c99caede0c3c0de9f33e7c89de1511"
            "64142941ef1cc6b81f618255c88f3e04316de6ff3f8b87fb187d3661e8d861b8134d518c"
            "fe5123377034be1a24c27e19133f7fdcbddcadd272d4eb1f5205b897290ed5b28741f1d1"
            "3f595f15604097426e31e5a64a6665f31f2ebca84c5be5d27a8632d85d7e123bac508bf4"
            "7f6274f38f9f580ad68134f4d4e654d56693448be12412a37275c071ba6b6b017df1ec3d"
            "04f5b5fe7af2c0aa65ed17249093e9601064716ca4d232779ee3cf649bff458fb2a37fd5"
            "34556a505f3dbc4f9afd77cb7e2e37e0a6a739404993d8f68975614f1988a7130cadc924"
            "5f9616c4776a3bfe77f48bb80ed67553de915c99302d13cc7ab0253d6f415cb1499866f3"
            "a0512a188aa35477c52c8b4cce48dd291dc9fabd99de813a0e0db12447a11917353860c0"
            "6efdf1c9532e0cf08a7c0a3185ab81d417"
        ),
        gas_limit=1762815149,
        gas_price=10,
        nonce=0,
        value=1848680675,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
