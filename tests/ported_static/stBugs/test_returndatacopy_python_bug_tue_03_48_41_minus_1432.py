"""
Fuzzer generated bug. No code source.

Ported from:
tests/static/state_tests/stBugs
returndatacopyPythonBug_Tue_03_48_41-1432Filler.json
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
    [
        "tests/static/state_tests/stBugs/returndatacopyPythonBug_Tue_03_48_41-1432Filler.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit, tx_value, expected_post",
    [
        (8777204, 2759170368, {}),
        (8777204, 0, {}),
        (3000000, 2759170368, {}),
        (3000000, 0, {}),
    ],
    ids=["case0", "case1", "case2", "case3"],
)
@pytest.mark.pre_alloc_mutable
def test_returndatacopy_python_bug_tue_03_48_41_minus_1432(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
    tx_value: int,
    expected_post: dict,
) -> None:
    """Fuzzer generated bug. No code source."""
    coinbase = Address("0x1000000000000000000000000000000000000000")
    sender = EOA(
        key=0x7B8E1B8983BDCF0DF1A8A35F27CE0D6E94E340D0C15BD288E587771F560B3570
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=23826461031063688,
    )

    pre[sender] = Account(balance=0x38BEEC8FEECA2598)
    # Source: raw bytecode
    pre.deploy_contract(
        code=bytes.fromhex(
            "6102dd6103e06103146052632318d76f7332f4d5419b41e6887cca98e0943f141a5c66df"  # noqa: E501
            "986347cfe65df16abd0c6d6c4cec6593afaa8c7de1769c96cd0751aa76a98c8196fa8c92"  # noqa: E501
            "e70d7bda1799c91c7f05de318110659b819438774667f9ec15a6e0233f75669e43360bd4"  # noqa: E501
            "e0a0764e9f395117afcd072774ce12d13dc73305858002a921407eb6508e3a3be377d482"  # noqa: E501
            "5dbf618a393c7c061e75a8a496a33afe0f017f2e3354789e321838b083d48893f23dced4"  # noqa: E501
            "592e9ea08fe3f80970d6334b626c6f1f6ede8bcc81d03a7ccc244231cb6606db986101d7"  # noqa: E501
            "61010761031c61025673ffffffffffffffffffffffffffffffffffffffff6311ecd01bfa"  # noqa: E501
            "7aa6d0c1c5158ef0db6994192acbd4cac6abc8449d80fc2c3247194668e0d9606bd39026"  # noqa: E501
            "6d7f78712766f4765076283ad67450d7ab4df6f3f6ee014ab802ec9d55727ed96dc0b9ce"  # noqa: E501
            "7bd14b193dc1f0d11ce19283c77ef651d4d2e7c180715ff7fcbc995ea8b27613cc516dad"  # noqa: E501
            "16d17f29a93220ce0d6edb0a65d3d474dbc39cba5bcb3d4fcf6a9fef19107dc04511df27"  # noqa: E501
            "52fb346103ce6101c163459d135bf0712ab2475fbb2ba0720711a903dbecfa0429bf6811"  # noqa: E501
            "e6e90cbb0f13d4ee61050c7052c865e0216b4096186fc604fb563fa59f761263ee91d55e"  # noqa: E501
            "407fdffe82ca1558f793f3a218dd9ba69084621fdea97de498f0b0e1874331115e31aaad"  # noqa: E501
            "4d87227362a9ec3e1c1be11cdb23097bbc600c64692eeadfa97f1616b8aec24564487dc7"  # noqa: E501
            "4f8e17e6a133b5dbe576838697de73f856197203ef1a733a54f7edb0dbd60f9d52db6b5c"  # noqa: E501
            "1477169b77f0d86917ed731a20db4b9e5b836bd26bffefab084a31c4afda166f8156612f"  # noqa: E501
            "281da0be688e5bdb1f31ed7869bc62343a7665abad657369482449e68b3acfe820997d3d"  # noqa: E501
            "df5785384d51aaa0612dab5ddbf2a9bf550736ad42293387d70693587d74f6ccfae5218d"  # noqa: E501
            "01559bac159497edb6a665eae52f52784975568a159c0cae9044d258c55b10f4d1008d29"  # noqa: E501
            "ab1df7fceb76b789e2a8cdbaa9c67c42cd1ebe81716ead0e94c721279d77d3a0b3de3115"  # noqa: E501
            "96d547292878449ccce511e6991b3dc636a16278159a9f61014a6102216342ce224df06f"  # noqa: E501
            "3d9a062274cd9a67ccba17c2cb06de46628e0bf703610106602e636db4b55bf061020561"  # noqa: E501
            "02c9633ff89b31f0788e55af17e19973f2c3f5d4c21c169890b9a92491f91aa1e714605d"  # noqa: E501
            "526103a1601f609b6103ee73d94f5374fce5edbc8e2a8697c15331677e6ebf0b6335adea"  # noqa: E501
            "bdf46d26060d385ed594e21b02b23a6c4c157350e7ab6a3ef66f83a29845b4ba85c4fdfb"  # noqa: E501
            "d0054a620123ad6893eff4b525b0f4b08d73285f36f3bcac6a985b906c348472b7cbc5a0"  # noqa: E501
            "2e61678666f0c50eecdc1167f20fc1dc41c2fd95856d7752e55ede4e56f4f536a04d436a"  # noqa: E501
            "7fd418a1ca44c0173c10f1806ba284f9c9c7c13670005de594dec538cd56c2743b66fdfa"  # noqa: E501
            "7683ae0df6917b8bbcb53461be606ef617322e6448e3e4124dbe061257a8f486529de369"  # noqa: E501
            "97f08ce92502957f85587a18082b5b5b49e36de5a83e8a270663088571bf2fdf8f5f29b9"  # noqa: E501
            "49976b41e3859928a237f5e5df84c17d3c431e82328f9093e64defbdd07d74d848358009"  # noqa: E501
            "99791abc41260472d96f9362604d077b198e859adc806beae7200cf116d2b55e89ddd564"  # noqa: E501
            "abc3900e69a68b0f6f0e9e4f12998728815d01c42f3b109ed25561027b610132635f4495"  # noqa: E501
            "86f06101726101ec631fe4bdc3f06101316101246103b33e60bd19610284610305fd6102"  # noqa: E501
            "db6102e4631ea09dc6f06b72a6cf13500241c2a5e5c4e1777ea9ed9b05ba9b57d70dd270"  # noqa: E501
            "ece76ecf21d3a41ad554f795167084dcab761d4c8437774cad4bb13b2bece16d40358df9"  # noqa: E501
            "3ec0f49abe102cd44e475560476101f3fd605b61030a6328f7e2e9f032604a547db71c02"  # noqa: E501
            "37247865fa2add74c8b27041c5718a2554a72662720296dff5b3b5327d59df4558b8a5b2"  # noqa: E501
            "c9e7d15eb3947a70064f935c8fdf0a4e6f644aa31b42c17d0280e50ea92a366c3d060c12"  # noqa: E501
            "c6a16a75522fbeb3d7cca702807f521781ab6101b252639cceb9e27f37ee8fde4ed3a23d"  # noqa: E501
            "3ec8db334ac1caa7e06523b0132dd615cf3fc16140d34c19761617823c3af47c42bc36b6"  # noqa: E501
            "9cb4385463595c7f6f9ea451396fe05303603e0cd401e13df744e2a67382774d94394155"  # noqa: E501
            "1704ff14dfa8646efbb2d8abc4ac6e258e99240372924b8001f8f0650d66b37411d484b1"  # noqa: E501
            "8f41e779702bd1c169fa52bbfc8af4a45f20acb0ef956edb2ecbc0d4eadbbbf6732f8bd3"  # noqa: E501
            "3b367a33c0faf0cf1970bcd38093a50a44fd253b0e74f2706239c499217b7bdae332e21d"  # noqa: E501
            "5d5e7e795c998cceed14cf46977e7d3cbb3c79ef0530c36fa8ac3fd8d49f10bb0ae919fa"  # noqa: E501
            "149adead7f67dae0b9ba628e056e0e87e029b8e5f42821d775338e6774301ecb428b3938"  # noqa: E501
            "237c6ee22b0b5edf2ad6997869f427ba0672a7168614233e85f61dae5ed428643a53f605"  # noqa: E501
            "116d6dad586dce62833a62ca8c914c646b1f861a5b1c4ea7298a95029e63cb849fe08b6c"  # noqa: E501
            "943cb9d854c7d50ad04cfdfe64718e2868b8f2b53e55fe01a152c8496cbcc69956787447"  # noqa: E501
            "062b734cebde6c6452e9efc4aba5bf071cbff56208a52561a8ef635f52399b724f3369d9"  # noqa: E501
            "88884f58166d734881774eff46d77b76b189c89c55b1c6591f178d2d21bf2b023adf9bc5"  # noqa: E501
            "b862127935e3346d98d56047a3f71241fd5a24abbb0cfc463fb8a5e67e327b055696fe51"  # noqa: E501
            "258dd07526ebd8439bcebb514ae26dc12d653a5c1263707c5109097ec5dcdb3918ab1149"  # noqa: E501
            "85f709d3003b50e58fba91007825a6b80073f644eaa306051808460fc3b2d8e276b2187c"  # noqa: E501
            "583f7ef29ee0b0c34f9ee57bac9ebb996402e3300ddf06c760fc5f531f6b1e2beda77fa1"  # noqa: E501
            "5c07f90f92422822e8d33c5d2409ea75197f7cd6d61770eddb078206cfc7c57b006cd0e9"  # noqa: E501
            "a9ec65fa4fc683da22cfaf6dfc995feb5f8386a052851fc58b7402f32e7ef9343d4633de"  # noqa: E501
            "f4c0a4b9be12f2cd7c646073e14ca3fb977524f677714c3d994ea05f1997a246537d2fc0"  # noqa: E501
            "ab20ed2a5958f3712602bee2a270429abbd3ff3b9945f72f58dcf4f86eb344417a87dfa1"  # noqa: E501
            "ebd701a0ff381bb40b620bb8287cd7781d2ef7c0fd8695f705465fbadf99fdffef2afd94"  # noqa: E501
            "b0e76531b6ea0d537a23d2332d13c20368a0724e41bc1130a6b1ebc3464527e34c26a437"  # noqa: E501
            "51649f9dfe4f8e7957981a9fc08558c90d38079f1921b60fe6fa448171fec55c4c630575"  # noqa: E501
            "e811712211cf72f489a4e83a2f5427eab647b075a91064929de0a65517"
        ),
        balance=0x161150E7531F1933,
        nonce=29,
        address=Address("0x47a24dd3a5f1a6a8238efdb32782a0b56ab9a1dd"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=bytes.fromhex(
            "610326610100fd79c940b5f2046740058558468f238b85db7f6bbe3f3d51e92a3e326102"  # noqa: E501
            "d85268b7f7c4147541c695f376705288410b81b217e80726fb9e4c5c7b4c49eca0c1b6b9"  # noqa: E501
            "137e117c16c26c9816459f38396ffc36da48d65defdc7d055cbc846c07e81cfab0607c6c"  # noqa: E501
            "bc968774d4de7df8e3236f581e688cc2081a96b1cad9e0fb6103ca601361019f61010163"  # noqa: E501
            "64b68c8e73ffffffffffffffffffffffffffffffffffffffff63200fbd63f16017610215"  # noqa: E501
            "610161610119635af7465b73000000000000000000000000000000000000000863792c69"  # noqa: E501
            "16f1799bf4fddda49ae97714e7d325ceab23acd5f4a15b52104741161261023f608ff360"  # noqa: E501
            "197021a04ff3f933b9ad91b735bfbfe41da7066b499c5d47b6de1fe398cb91fd68f681cb"  # noqa: E501
            "b8661dd457cf713cef75dabf5ea496d7012f4c56b9fee6c4208461022d61021661036e61"  # noqa: E501
            "0200630277795a73ffffffffffffffffffffffffffffffffffffffff6333d3d55ff16447"  # noqa: E501
            "20e3ce666101ad526b874cead08499d57a5497d3776102fa60ff60f561014863202b2ea8"  # noqa: E501
            "73d94f5374fce5edbc8e2a8697c15331677e6ebf0b6302e83dbef1327144ce205e051f29"  # noqa: E501
            "6fb116fc9e5f3c280919af70f3c93c5d5cefff338db2b1165b4918f1780a73852663192a"  # noqa: E501
            "9579a68b50eefdc639ca0b62ab4d5230"
        ),
        balance=0x442F5872DD93B01A,
        nonce=28,
        address=Address("0x786208c0f93dac2045bec6a3f8a41b73ab845593"),  # noqa: E501
    )
    # Source: raw bytecode
    contract = pre.deploy_contract(
        code=bytes.fromhex(
            "7e4fc1426b49cd8e2c770339616ce9c501fb746715dd4a20219229d0673ac05575993bd0"  # noqa: E501
            "89a6663f6dff488574195b848fbb357eb7be1f61026352605861011761027f60e373c94f"  # noqa: E501
            "5374fce5edbc8e2a8697c15331677e6ebf0b63748b4abbfa60e76101bc6103f33e60d861"  # noqa: E501
            "036a6315193f47f07aff076e997770d03b70288679871dc28aa5a1399b21c8afa8155ecd"  # noqa: E501
            "7e75dd05f9d7eb42fa3e79c6a2109dff2a1e53e612fbe000bed18eec8345f00574f537c7"  # noqa: E501
            "2820d8b97350ae523a8f7467ae14a8bd9aae6be55862b685e32476cc67ae2c6a40cf5572"  # noqa: E501
            "9540d111f44c63629458da68e7ad2a9b389ed3bb60682169ea8a7b3a1bcf92621919c062"  # noqa: E501
            "413cb5986101236103596101776103be73d94f5374fce5edbc8e2a8697c15331677e6ebf"  # noqa: E501
            "0b631f6d9dfffa6103716101f760163e76d609ca9a51645238e4f1f8268f973c3a01a0b6"  # noqa: E501
            "7479a34563d1e70065610173525b64e6d218af5474c3d8045447d06c726801695cfa26fd"  # noqa: E501
            "faa6460a868569cd662855a55716140ae07eb1e25aeaf04ae7cf54e8aa7a22206da5a6e5"  # noqa: E501
            "2bdd3ef82ad40a4681d25811167f7b0a3f66a727652592924dc1291a6085d537c5da2d62"  # noqa: E501
            "72a54f882460bc76407d666361c40cc56bc8778a8bc9a9b45d44c78cfe4333fe0c49418d"  # noqa: E501
            "d61f183d41132f755340e48ababb825a26ebc0ca693a8b465121200fd21a727b4c365a65"  # noqa: E501
            "a3255278f6705e5ca0f6146fccd3766a6e5b9decfb6e50968851e829313a2cc9d5b518e2"  # noqa: E501
            "586166c31ba04ed3f5a377310bd9993aa534b007858d9545342410ce8c156d780a8cb477"  # noqa: E501
            "a65efed30aa9d6bd63c48a134c9cb0c677ecda48aacef0c17c91de37e3cfdae691537424"  # noqa: E501
            "06995ea81bbae6a201663b9b37a6a9f597ae8d5a634f40e44e517174ea92616bc228ced0"  # noqa: E501
            "d712c265c2925470326102f26102146101b13e601d6103a360726103ec73ffffffffffff"  # noqa: E501
            "ffffffffffffffffffffffffffff6319628a1bf4740e5f285d15a08a263b0a444516266b"  # noqa: E501
            "d51fe7266771604469df3c080d07dd47c4eb9e7344a87541ddc5a6971632a021033eb354"  # noqa: E501
            "2b375cd06bd0dfb48f6acde07152794b556839563efff1afed3b0a857615166526175e71"  # noqa: E501
            "84b83cc2dedf61ec5d65d1eee66efcb87b4f2c73335db9fba49e3d40638cd7f462f1d3b3"  # noqa: E501
            "15f18dc1f692a68b24036102c16101f36102f23e783d6331b166ee517c71a4ba159dd322"  # noqa: E501
            "b9fa5f3237dfb85d2594edd580948177bd72d2244f767352371e3428d28bc6356c553b18"  # noqa: E501
            "d00e6b3cf602061672c2abbd7763059f61940b0d19fde33f7b5a960861025b61021d6101"  # noqa: E501
            "d361035173b94f5374fce5edbc8e2a8697c15331677e6ebf0b635ba25f69f4790d251e9a"  # noqa: E501
            "e89c718dd41c3f57b0c304fbb83978de28d23499bdd1729c04301ff527ccc9f7ed74a8db"  # noqa: E501
            "d906b468d4487ffba738f193e3047b02e40beb08b4f11707681ef103ec1b00585a85f272"  # noqa: E501
            "27a179917ef15e97a359268b06ff34bcee23a869974fbca6e201cb16179743ac0f8c9f86"  # noqa: E501
            "7003d5e26a5aad5217ebfff31407169237230772efaab6cd87fbc9fd408d4ac5a048e43f"  # noqa: E501
            "b4e7a261037c6101f76103e13e"
        ),
        balance=0x16B3E0323B4F717D,
        nonce=28,
        address=Address("0xd1f0befc94d951fb4b787ada0927f60a9a94ce12"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SLOAD(
                key=0x1DB054CCC801C0666B34B3C6242BBFC5E98F20C14FB95E0118BE9AD0,
            )
            + Op.ORIGIN
            + Op.JUMP(pc=0x33D50E215FF59297861847EA911A6A9D)
            + Op.CALLCODE(
                gas=0x2C1E2816,
                address=0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B,
                value=0x42A46F50,
                args_offset=0xCB,
                args_size=0xFB,
                ret_offset=0xA8,
                ret_size=0x3A5,
            )
            + Op.MUL(
                0x8732A34B873C7D943050B8659794F0BD3E841D35A2231EF6,
                0x135E2F826DC603850E0DB21D105B,
            )
            + Op.PUSH31[
                0x97F8CDE11728FA2051E87933CF858E4E5E91BAA74FC1E9FFE4C7B15BA600E8  # noqa: E501
            ]
            + Op.EXP(0xD704BE2B41C7F867, 0x8F095989DC68F47E)
        ),
        balance=0x2CE99FC81ED55962,
        nonce=63,
        address=Address("0xf4c98e0dda63a5c89847ca3e6ddf34f23443370f"),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex(
            "79b94053bf1fb725756225cde415738a99e1a7690cbe409744b73761038f5277367dedc8"  # noqa: E501
            "2e30635bc57e35fcb2038306d9a3a6e4ddcb9d306c879e470f5dd81e1148184f62bd6361"  # noqa: E501
            "ae97087aff61cee25c694a734342be5043b1fde117ba383682ba0d91e0db8b6a29c882a0"  # noqa: E501
            "44d0c8bb4925a6796d8480df1b1ccc25641df94f43d5802aa8f44bf70a6817ed784e6757"  # noqa: E501
            "25bdc7718a54d686307da5234286085240ba84575dac25d7fc32c59999a9d38fee0d25e7"  # noqa: E501
            "c23986006e9c5bb022f7d28a2cab01a4bb37dd4210608d6101bf6101606079637be1ae43"  # noqa: E501
            "73c94f5374fce5edbc8e2a8697c15331677e6ebf0b63627cbc7df161023161030a60213e"  # noqa: E501
            "60686102596102c861032b73b94f5374fce5edbc8e2a8697c15331677e6ebf0b630a549e"  # noqa: E501
            "50f461036761038161026c6103d1633aded16b73b94f5374fce5edbc8e2a8697c1533167"  # noqa: E501
            "7e6ebf0b6320edf4a4f161ea427bd5141d55f5730cd82bf08bff3928aea77e7153bcc4a3"  # noqa: E501
            "a53996be367e77c98cb6fe85797e1d020284d4d302c8b4ebe6b28a9c64a9ae6b2ad68947"  # noqa: E501
            "16732f245e7fdc527443f79a0ae9b8d8900caa1c5796a2854ceddb00a82bfb724ec01b51"  # noqa: E501
            "3ed61cce89400a06fe90a109bad6d57ae028143e7552930136347eb71a49db0072c87bd4"  # noqa: E501
            "37b9cd7b2f7e6e609f653a85875c9ede69360f9d06d4c2e82caf2e6a87043c0bf5a23543"  # noqa: E501
            "1acbb394775dcbfc7b86074b99c9e6f959d84184e5e40c854c280218c07fcd4e98dc3bc4"  # noqa: E501
            "4f7d651d7191ead4be3aaa6657719af4fbf6b9741d3c2c1eca740b7c46e7b87ce36eb18a"  # noqa: E501
            "407fca527573156e83888dff152dc41fd0f98972d378a02f8465d755c426de2e81e23ed5"  # noqa: E501
            "b68990e3c73c65071b0c7b046cae8cdd18828c27f10a8ba8e3616103f76103786363763a"  # noqa: E501
            "4bf078faa8e34791ed3692f5784a35b7bbe3db838dcea84ce1955eec"
        ),
        gas_limit=tx_gas_limit,
        value=tx_value,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
