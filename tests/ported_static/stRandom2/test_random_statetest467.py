"""
Test_random_statetest467.

Ported from:
state_tests/stRandom2/randomStatetest467Filler.json
"""

import pytest
from execution_testing import (
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
    ["state_tests/stRandom2/randomStatetest467Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.pre_alloc_mutable
def test_random_statetest467(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_random_statetest467."""
    coinbase = Address(0x4F3F701464972E74606D6EA82D4D3080599A0E79)
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
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
    # Source: raw
    # 0x700ab6605e03171122aeebd20b63699a72d454628639346ffaf92bcd1855c6dde5c90ba78a966a256c777ce8880c23f90f4a2ecc999a6cd42da7121d5e1fde1c9c340f9660b571a71e20a5753bc4e291adbd41a228289a0be175a606bc44dd2079ece46a2cba498bee0d80a41673d8016e7232f97a66b29954364570f6e2d08b6d429c6a75f737c594aca21580bc0d60e67c38a50ce1ddf0ce9963fd79da8a590429f5fcfb6e7fd9ee2d27201f95707235ce3dbc5997e44baa174111977f51dc6b333a9a63483e6a3d6f423ed5778057702664b65d4af9aab14d773a787d60bd24c439b29533c6b172278b6a78e64f8e319fbd6b45eeca466afd1eb2eecbaeed773da8711c4c65787e0a0a1297f525b7418f49fbc1b2446a847d74bb0a66e3b06ef70d8a8aa09a910a6be623c6a8239960381512da962eb868a21f99d90741128fcb711e029cff42f4f8f5d35947c4a7b39cff7fd46f916cc8612b146bbf52db1cd36e6c2fce7cd9ed232e21946081d78d87e61bc42fce313fa32b458d1e898e52cc2e607570a7e1d2ae3b5b7d58e0a70396bcfaae0789cd9202876488bb595d457a45bc48e190f5d56b34be6d244070ffe02107ceaf9313db08d9a1809b366fc956e6c5567da1d8a656406871eb0dd46268b5127366225cb464667bd081c949847a95e2821f589dad60c061ef2fa36b9e17c2b3a94181a8f8a89b486734ca1a8a0c86c26d076004601160066012635e0d738673<contract:target:0x095e7baea6a6c7c4c2dfeb977efac326af552d87>636158e2e1f166e10de5d590572335  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SLOAD(key=0xAB6605E03171122AEEBD20B63699A72D4)
        + Op.PUSH3[0x863934]
        + Op.PUSH16[0xFAF92BCD1855C6DDE5C90BA78A966A25]
        + Op.PUSH13[0x777CE8880C23F90F4A2ECC999A]
        + Op.PUSH13[0xD42DA7121D5E1FDE1C9C340F96]
        + Op.PUSH1[0xB5]
        + Op.PUSH18[0xA71E20A5753BC4E291ADBD41A228289A0BE1]
        + Op.PUSH22[0xA606BC44DD2079ECE46A2CBA498BEE0D80A41673D801]
        + Op.PUSH15[0x7232F97A66B29954364570F6E2D08B]
        + Op.PUSH14[0x429C6A75F737C594ACA21580BC0D]
        + Op.PUSH1[0xE6]
        + Op.PUSH29[
            0x38A50CE1DDF0CE9963FD79DA8A590429F5FCFB6E7FD9EE2D27201F9570
        ]
        + Op.PUSH19[0x35CE3DBC5997E44BAA174111977F51DC6B333A]
        + Op.SWAP11
        + Op.PUSH4[0x483E6A3D]
        + Op.PUSH16[0x423ED5778057702664B65D4AF9AAB14D]
        + Op.PUSH24[0x3A787D60BD24C439B29533C6B172278B6A78E64F8E319FBD]
        + Op.PUSH12[0x45EECA466AFD1EB2EECBAEED]
        + Op.PUSH24[0x3DA8711C4C65787E0A0A1297F525B7418F49FBC1B2446A84]
        + Op.PUSH30[
            0x74BB0A66E3B06EF70D8A8AA09A910A6BE623C6A8239960381512DA962EB8
        ]
        + Op.PUSH9[0xA21F99D90741128FCB]
        + Op.PUSH18[0x1E029CFF42F4F8F5D35947C4A7B39CFF7FD4]
        + Op.PUSH16[0x916CC8612B146BBF52DB1CD36E6C2FCE]
        + Op.PUSH29[
            0xD9ED232E21946081D78D87E61BC42FCE313FA32B458D1E898E52CC2E60
        ]
        + Op.PUSH22[0x70A7E1D2AE3B5B7D58E0A70396BCFAAE0789CD920287]
        + Op.PUSH5[0x88BB595D45]
        + Op.PUSH27[0x45BC48E190F5D56B34BE6D244070FFE02107CEAF9313DB08D9A180]
        + Op.SWAP12
        + Op.CALLDATASIZE
        + Op.LOG3(
            offset=0xEF2F,
            size=0xC0,
            topic_1=0x66225CB464667BD081C949847A95E2821F589DAD,
            topic_2=0x68B512,
            topic_3=0xC956E6C5567DA1D8A656406871EB0DD4,
        )
        + Op.SMOD(0x34CA1A8A0C86C26D, 0x9E17C2B3A94181A8F8A89B48)
        + Op.CALL(
            gas=0x6158E2E1,
            address=0x79940E2F1225EBA4FAB3405B111535075C733270,
            value=0x5E0D7386,
            args_offset=0x12,
            args_size=0x6,
            ret_offset=0x11,
            ret_size=0x4,
        )
        + Op.CALLDATALOAD(offset=0xE10DE5D5905723),
        nonce=0,
        address=Address(0x79940E2F1225EBA4FAB3405B111535075C733270),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(
            "6f42af68ebb8fbfe65896d2993c75a18b06dbf26336197db938986312c4ea88b7aab8c2cd436a05c5b765989d8ad6c97257fe7c4f1f33d9644b8e03c6898c8946d19a4dfed187482dd95f88ea4f0c43f39f4ab261808bf1b1f658f0979b867eeb00baeadab37700449f879522b0bba9c6f2d87d2541b0b943275c57530b3790b225dd318baeca448b045ccf1477837e4156d992ad881869b91a5f7f71de5884a703c659316ab330af945c7fd906936c695fe79134e48e46153702e81da6d3da14e05b90ae63b037d7b9e4fb17367c1e737162043aa587f4bb580e87cfaad897bc8e3152e3741f1ba345cc4c762c99caede0c3c0de9f33e7c89de151164142941ef1cc6b81f618255c88f3e04316de6ff3f8b87fb187d3661e8d861b8134d518cfe5123377034be1a24c27e19133f7fdcbddcadd272d4eb1f5205b897290ed5b28741f1d13f595f15604097426e31e5a64a6665f31f2ebca84c5be5d27a8632d85d7e123bac508bf47f6274f38f9f580ad68134f4d4e654d56693448be12412a37275c071ba6b6b017df1ec3d04f5b5fe7af2c0aa65ed17249093e9601064716ca4d232779ee3cf649bff458fb2a37fd534556a505f3dbc4f9afd77cb7e2e37e0a6a739404993d8f68975614f1988a7130cadc9245f9616c4776a3bfe77f48bb80ed67553de915c99302d13cc7ab0253d6f415cb1499866f3a0512a188aa35477c52c8b4cce48dd291dc9fabd99de813a0e0db12447a11917353860c06efdf1c9532e0cf08a7c0a3185ab81d417"  # noqa: E501
        ),
        gas_limit=1762815149,
        value=0x6E30A0E3,
    )

    post = {
        target: Account(storage={}, nonce=0),
        coinbase: Account(storage={}, nonce=0),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
