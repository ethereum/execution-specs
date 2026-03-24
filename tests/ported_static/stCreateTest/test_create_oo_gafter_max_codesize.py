"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stCreateTest/CreateOOGafterMaxCodesizeFiller.yml
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
        "tests/static/state_tests/stCreateTest/CreateOOGafterMaxCodesizeFiller.yml",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.parametrize(
    "tx_data_hex, expected_post",
    [
        (
            "a6f227c000000000000000000000000000000000000000000000000000000000000000fa00000000000000000000000000000000000000000000000000000000000000fa00000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            {
                Address("0x00000000000000000000000000000000000c0dea"): Account(
                    storage={1: 1}
                ),
                Address("0x008fe4a99394ff41d3689b06e1206ebb5e841b05"): Account(
                    storage={0: 24576}
                ),
                Address("0x009f2c334b4957b72c252ab42bbd0dc7c3289edf"): Account(
                    storage={0: 24576}
                ),
                Address("0x00c7a731691874e9e97493e2b16e7c6787197e48"): Account(
                    storage={0: 24576}
                ),
                Address("0x01295f79874d5247b4b665a92f73931900f1af6d"): Account(
                    storage={0: 24576}
                ),
                Address("0x0171dea2507cc731b1ba8bdbf35008111f59f619"): Account(
                    storage={0: 24576}
                ),
                Address("0x030d1f67dd69d59b426d610dc4965702eb155b6a"): Account(
                    storage={0: 24576}
                ),
                Address("0x036f16e234d8a011d864210d0d3e70494ae1a3a0"): Account(
                    storage={0: 24576}
                ),
                Address("0x038955d1e23d253db998914d068201cd814d52b4"): Account(
                    storage={0: 24576}
                ),
                Address("0x039cd5ea0a9bf718b11e0b649692bd15fb0f298d"): Account(
                    storage={0: 24576}
                ),
                Address("0x03bc5e3b1d12e870bfa0372aed3b121c0761f199"): Account(
                    storage={0: 24576}
                ),
                Address("0x041218fe5a5552adf0bfc447cecf0715fc34b890"): Account(
                    storage={0: 24576}
                ),
                Address("0x0461e813a48f3589693639de73c14fe6f3e3b114"): Account(
                    storage={0: 24576}
                ),
                Address("0x0583ad2e135ac542b1ef85c150b94322853158c9"): Account(
                    storage={0: 24576}
                ),
                Address("0x067cc58d35dd7591cc4203b79c709c8a1035d366"): Account(
                    storage={0: 24576}
                ),
                Address("0x071d4688164ccd18e2e53260285796bcb164f2db"): Account(
                    storage={0: 24576}
                ),
                Address("0x074a7dabb0c390eafbee22baa0575637da1d42fb"): Account(
                    storage={0: 24576}
                ),
                Address("0x07c32f644fbf840aa4815a6e1b16f7d8e27ffe54"): Account(
                    storage={0: 24576}
                ),
                Address("0x07f65ca20efa11bb369d6380745a26a995a6d990"): Account(
                    storage={0: 24576}
                ),
                Address("0x084c10d2bcf80dfaeae486a4cd8741b990145977"): Account(
                    storage={0: 24576}
                ),
                Address("0x08ce0c79d24ec8b39aff98c87c1467067ceee26e"): Account(
                    storage={0: 24576}
                ),
                Address("0x090744f767347333e2a5e08fae58f2ca7eb434d9"): Account(
                    storage={0: 24576}
                ),
                Address("0x097a1dadf2e42ac2d3a61aa0a74f4485150b7fc8"): Account(
                    storage={0: 24576}
                ),
                Address("0x0a005a10daa8947d7986cef760cbab34e2aa19fa"): Account(
                    storage={0: 24576}
                ),
                Address("0x0b8eccd09ac0ccad79e27441d10979c9bc880213"): Account(
                    storage={0: 24576}
                ),
                Address("0x0f6339ac04e016cc2bf11910912597b65e27fe1a"): Account(
                    storage={0: 24576}
                ),
                Address("0x1088f8abbbe5e2d16e7105e70f6cc8b47529559b"): Account(
                    storage={0: 24576}
                ),
                Address("0x12388e20268ad46d1a9d10b47050fa45a58e0670"): Account(
                    storage={0: 24576}
                ),
                Address("0x12b4ca840fc837233d4760863b242954d896641d"): Account(
                    storage={0: 24576}
                ),
                Address("0x142b0c4c07d7592c1018e9c5133b8a535482a3ab"): Account(
                    storage={0: 24576}
                ),
                Address("0x14a65aef3fbdb53d66b97abf4bee064e4af74831"): Account(
                    storage={0: 24576}
                ),
                Address("0x1544b32742f0ef65b83bef63d8da3f79747a122b"): Account(
                    storage={0: 24576}
                ),
                Address("0x18e03de511a3191c75505fa99adee652682a60dc"): Account(
                    storage={0: 24576}
                ),
                Address("0x190922de67df80176c3a3af07e9372438b1e5057"): Account(
                    storage={0: 24576}
                ),
                Address("0x19a62f6e9c37c0daccb7fb627663bf22dc20ca5b"): Account(
                    storage={0: 24576}
                ),
                Address("0x19e84fa14eaa2d667245981c08baa7e93ae94b92"): Account(
                    storage={0: 24576}
                ),
                Address("0x1a2dfe43e35a2a2bc4719ef2126af20066b636e5"): Account(
                    storage={0: 24576}
                ),
                Address("0x1aa67b714216e355be2b374609f98f2372631702"): Account(
                    storage={0: 24576}
                ),
                Address("0x1e4802f8e20a034148f9f7e9f7ff8fcf89a1f3c8"): Account(
                    storage={0: 24576}
                ),
                Address("0x1ea15370a48589c62ca0de7aaa001ff14290d651"): Account(
                    storage={0: 24576}
                ),
                Address("0x1f03637d1c15acf5c8f41fbe4caa43fd5be5cd8e"): Account(
                    storage={0: 24576}
                ),
                Address("0x20543219cb5496cdb12905720e336a36ab8584a3"): Account(
                    storage={0: 24576}
                ),
                Address("0x20ae87c7b64ae11a7b9930b87157f18124cfe82c"): Account(
                    storage={0: 24576}
                ),
                Address("0x20d1c37d492b7ebaca028f1048a898189b18d13f"): Account(
                    storage={0: 24576}
                ),
                Address("0x22959e4445ef9eef4c56a735d5d83611b2733b04"): Account(
                    storage={0: 24576}
                ),
                Address("0x25ec69783ad564c5089b35529705c813bf36dbe4"): Account(
                    storage={0: 24576}
                ),
                Address("0x27c860b8374013394fbeb583b67dc9d5819007b8"): Account(
                    storage={0: 24576}
                ),
                Address("0x27fad120d123a456afff7901a618249a1cb402fc"): Account(
                    storage={0: 24576}
                ),
                Address("0x286000ed447bee4415eb336abce3d58f2f41a667"): Account(
                    storage={0: 24576}
                ),
                Address("0x2b13e6d598d1ff118f1e7c8004933ff8ed19ebb5"): Account(
                    storage={0: 24576}
                ),
                Address("0x2b2308528a9d4ae9dd0d4fd128a936cccd49606e"): Account(
                    storage={0: 24576}
                ),
                Address("0x2d84a0f4a5c0431731c561f07da860cee6a685ca"): Account(
                    storage={0: 24576}
                ),
                Address("0x2f0411b3af6e4925b16e23fff8abbee62083619b"): Account(
                    storage={0: 24576}
                ),
                Address("0x30d71546cd3769b96ddc33d1b2fbf7e6afa5c816"): Account(
                    storage={0: 24576}
                ),
                Address("0x30f35a56e64cce71d4939a89433a62cdd041c33d"): Account(
                    storage={0: 24576}
                ),
                Address("0x31ce43f969bd048e8c02c12b95e29a0c5c4cd90f"): Account(
                    storage={0: 24576}
                ),
                Address("0x333354aa92066991501f72cf48ba3aacb4d284a5"): Account(
                    storage={0: 24576}
                ),
                Address("0x336debb8ce5a3cf4b40be471ac04f77b51f2d2e1"): Account(
                    storage={0: 24576}
                ),
                Address("0x34eca9e866a93f9a817d4e8c2a634488a1995549"): Account(
                    storage={0: 24576}
                ),
                Address("0x3963c5ba8ec666e841450ad411c7ee46f5916cdb"): Account(
                    storage={0: 24576}
                ),
                Address("0x396b47fae89161b1959b5a833acf816be526b860"): Account(
                    storage={0: 24576}
                ),
                Address("0x39e86858df5a34c9a2625bcf973cf289931c415a"): Account(
                    storage={0: 24576}
                ),
                Address("0x3a74fefeb9841b01a56e80ae0d353a0028b4c73a"): Account(
                    storage={0: 24576}
                ),
                Address("0x3df4a81ea5b969a1b6883a78a8c5467bd59723c6"): Account(
                    storage={0: 24576}
                ),
                Address("0x4380c6b5ce52da72b7c144bd040f0dc142c100d2"): Account(
                    storage={0: 24576}
                ),
                Address("0x45c60faf3bac6b671b29fb6c756a5db8fece2b73"): Account(
                    storage={0: 24576}
                ),
                Address("0x45f8b2981c97ffbcb5712808678b539ce7089b9d"): Account(
                    storage={0: 24576}
                ),
                Address("0x461d621b21d3484e5967063bbdabe432236b6d1e"): Account(
                    storage={0: 24576}
                ),
                Address("0x464e9263b5ec030efff98377d7b0af65b91a6d12"): Account(
                    storage={0: 24576}
                ),
                Address("0x46d195d72aaf347a802fdc1273f647db8abda19c"): Account(
                    storage={0: 24576}
                ),
                Address("0x47d608e9eb2a9603cad5f0ce10029434efcd873e"): Account(
                    storage={0: 24576}
                ),
                Address("0x497d3d33f7c079fc7ab53f5baa7d96ccd802c96f"): Account(
                    storage={0: 24576}
                ),
                Address("0x4a5de374d69c1de39cbfb7f3963ce460a64c6495"): Account(
                    storage={0: 24576}
                ),
                Address("0x4b2c1b96e4b881960f7241f496a85155136528c6"): Account(
                    storage={0: 24576}
                ),
                Address("0x4ccb281d5393f491edb218da6fe87e7383e5f8c2"): Account(
                    storage={0: 24576}
                ),
                Address("0x4d70a4f9d072ad765bce998b8ccb5e61c29cd6d2"): Account(
                    storage={0: 24576}
                ),
                Address("0x4e799c8bdc45c386d64c005e7784fff3e44807dd"): Account(
                    storage={0: 24576}
                ),
                Address("0x50db39e8efeff6e63ab8228feaec3a6e24a6e95e"): Account(
                    storage={0: 24576}
                ),
                Address("0x53acf65110278d0917b0218ea70c5c82a50ae78a"): Account(
                    storage={0: 24576}
                ),
                Address("0x5518286da4b2adc58f17b4ad52fc3f9a38a8c552"): Account(
                    storage={0: 24576}
                ),
                Address("0x55bbb55f14ca906c870f8e2898a2a3279b72782b"): Account(
                    storage={0: 24576}
                ),
                Address("0x56f8eefb2f0d9b3fddbcca160d7adb0f06ee2798"): Account(
                    storage={0: 24576}
                ),
                Address("0x57f440c1e3896e48c29d59c02ec330f8858d1f98"): Account(
                    storage={0: 24576}
                ),
                Address("0x5806f1701c5e1fa25c406f30ae3258df58acf078"): Account(
                    storage={0: 24576}
                ),
                Address("0x584549b2d2211d49289a27d5b1ce2c15f13eb577"): Account(
                    storage={0: 24576}
                ),
                Address("0x59612f767697ed38e477238326f3372aa3e5eb6a"): Account(
                    storage={0: 24576}
                ),
                Address("0x5baac4dce052912f038c5e003ef3b4ea15c9306e"): Account(
                    storage={0: 24576}
                ),
                Address("0x5bbf0533d9045f72efe987c4674e112c7300d07c"): Account(
                    storage={0: 24576}
                ),
                Address("0x5da99b5c1a17088158989bf3641459bcea07975d"): Account(
                    storage={0: 24576}
                ),
                Address("0x5e37a04adf836d7c1b1dbc84ce065955d4e51f68"): Account(
                    storage={0: 24576}
                ),
                Address("0x5ea06af477885dbd9eaaf073edf03f8f14e20601"): Account(
                    storage={0: 24576}
                ),
                Address("0x6186e6dd86ffd92e6d9203db6ebdd2a52cece6f6"): Account(
                    storage={0: 24576}
                ),
                Address("0x6355ac4b9d8b9a0280d85bca5fc5d7178bd8f895"): Account(
                    storage={0: 24576}
                ),
                Address("0x63f4c7e61ac2b5276bdaa7dae7110561be17e98b"): Account(
                    storage={0: 24576}
                ),
                Address("0x672b53b234366400ecc07d1cf0e8a28f7ee204f8"): Account(
                    storage={0: 24576}
                ),
                Address("0x67828d8484ce84789f9ace803f5fa6375427ee74"): Account(
                    storage={0: 24576}
                ),
                Address("0x67ddaac192b9e0a7c977e027ec71641ad2d1e17c"): Account(
                    storage={0: 24576}
                ),
                Address("0x69063beaa2ccc2af95d158fe33443c61ca08b306"): Account(
                    storage={0: 24576}
                ),
                Address("0x69bbf6b71f9895aede8b7d72c04d83d386746858"): Account(
                    storage={0: 24576}
                ),
                Address("0x6ab290e1599c21399b71281f9d5a3a907f794796"): Account(
                    storage={0: 24576}
                ),
                Address("0x6f90f79698c2df7072b254f44298c21bc900a2fd"): Account(
                    storage={0: 24576}
                ),
                Address("0x6fb954faac7af474042ca4ed99a494608a6b2034"): Account(
                    storage={0: 24576}
                ),
                Address("0x70179a1e41ca5110788e3906a987282e091fa582"): Account(
                    storage={0: 24576}
                ),
                Address("0x706eec6be586e6faaccd7c08fe500cdb762f9a03"): Account(
                    storage={0: 24576}
                ),
                Address("0x70983d6bacc64c167901a0756ccecb9c2756f76c"): Account(
                    storage={0: 24576}
                ),
                Address("0x713df334cbd70c9e2dd027f6d9820854a03297ab"): Account(
                    storage={0: 24576}
                ),
                Address("0x73281f5dbd975c5b9335dbb3220451d4550ec187"): Account(
                    storage={0: 24576}
                ),
                Address("0x74ce5dfe5278e34c844f9526e835754d8f2a4853"): Account(
                    storage={0: 24576}
                ),
                Address("0x7603643a3c2fd2120ed9d28500e2da905b4a4c30"): Account(
                    storage={0: 24576}
                ),
                Address("0x76398682b927b04cfd13473d001c8152c66bb05f"): Account(
                    storage={0: 24576}
                ),
                Address("0x79243f03010f35335bdc5dd8bac8fd053b0ed5dd"): Account(
                    storage={0: 24576}
                ),
                Address("0x79d0076fa2213249c34ecf0f4cd85d01c8059106"): Account(
                    storage={0: 24576}
                ),
                Address("0x7b544c88e59949827e3b90698af52957f0abc279"): Account(
                    storage={0: 24576}
                ),
                Address("0x7b7884b6efdd6c91862a7065487277a39abac083"): Account(
                    storage={0: 24576}
                ),
                Address("0x7b80ecab4092371721de2015dbdc35dccd3fcf5c"): Account(
                    storage={0: 24576}
                ),
                Address("0x7c8b3524fffc0e8eb78704b27de270a016ae75c8"): Account(
                    storage={0: 24576}
                ),
                Address("0x7cd8a3c6b9680e9891e60404ef6567fde5dcec98"): Account(
                    storage={0: 24576}
                ),
                Address("0x7e3bd590a907dd2efd9a59ff5a323060ef22d805"): Account(
                    storage={0: 24576}
                ),
                Address("0x7e6095002ed2d430bc4b2878a6b450b29009b16b"): Account(
                    storage={0: 24576}
                ),
                Address("0x7e916fa8af1b00423505d9a2f160d023d9c6af99"): Account(
                    storage={0: 24576}
                ),
                Address("0x7eb2135adfbd65150b8e2a9e0c4fe8713a8e386c"): Account(
                    storage={0: 24576}
                ),
                Address("0x7eeaf9e649b762242a1034392e084bafd2a8aff6"): Account(
                    storage={0: 24576}
                ),
                Address("0x81bd8848da166eaf3454dd7d4193d2f90045b420"): Account(
                    storage={0: 24576}
                ),
                Address("0x81da7e005190adde1e6cb19603f71546d8f8dc72"): Account(
                    storage={0: 24576}
                ),
                Address("0x823bd47cf1dd771fe33b75e8e391a198b696cf96"): Account(
                    storage={0: 24576}
                ),
                Address("0x82e0efdcc3624e23e978fa09df7def295320238a"): Account(
                    storage={0: 24576}
                ),
                Address("0x831dff3eeb5fad5fc684f480870703287d559d47"): Account(
                    storage={0: 24576}
                ),
                Address("0x863e236652e374c1dc8734330abede9b6bb164a7"): Account(
                    storage={0: 24576}
                ),
                Address("0x88441d8123594b08ccb9716a77193fc45bb55c5f"): Account(
                    storage={0: 24576}
                ),
                Address("0x8b6ed72e9fc557e79819e4cf3f806d85a68d0b33"): Account(
                    storage={0: 24576}
                ),
                Address("0x8bbafbd848a59cdc3108087d83b94280ec69b5a8"): Account(
                    storage={0: 24576}
                ),
                Address("0x8bd7418790ee476f2a30a29598684aadbb10f6c3"): Account(
                    storage={0: 24576}
                ),
                Address("0x8cab2bbd02c94f4b35265b07aefa257c82647a28"): Account(
                    storage={0: 24576}
                ),
                Address("0x8d852742356d237ffe887a0b54bb561918558ac2"): Account(
                    storage={0: 24576}
                ),
                Address("0x8dba3fba0e82e23675d9e27ad38ba3133814fdd9"): Account(
                    storage={0: 24576}
                ),
                Address("0x910ace9558901f0dc6818b5d71eb753cf65f56e2"): Account(
                    storage={0: 24576}
                ),
                Address("0x91394dff8adea637c7953b9cd1dfaa306f09c6a8"): Account(
                    storage={0: 24576}
                ),
                Address("0x9205d637c34fd000dedbd577f4c3fd082acc0202"): Account(
                    storage={0: 24576}
                ),
                Address("0x92ccd8ac1dda8d6f1c2a8cd9b51dc56c44febe74"): Account(
                    storage={0: 24576}
                ),
                Address("0x935cd6233eeca8b850842868f2b61ed396de3c0c"): Account(
                    storage={0: 24576}
                ),
                Address("0x955faee8bb23113f60de8288e27464520625d14d"): Account(
                    storage={0: 24576}
                ),
                Address("0x97480fb5804ba35e012bcb30880c64c92b1948a8"): Account(
                    storage={0: 24576}
                ),
                Address("0x97752d900db15f9799c49af7799fbb47aac58cff"): Account(
                    storage={0: 24576}
                ),
                Address("0x98cb664adcedfb7f04b94bbc935f2bf68a53a447"): Account(
                    storage={0: 24576}
                ),
                Address("0x995576eccf99c1152b573e092fc068f9809ebabf"): Account(
                    storage={0: 24576}
                ),
                Address("0x9999bf853301842aa9f6dd1aa0e1e811b2a00f49"): Account(
                    storage={0: 24576}
                ),
                Address("0x99e62e63345e1e76b8e7cbafb433544e2fe99512"): Account(
                    storage={0: 24576}
                ),
                Address("0x9ad039a0ead301cfdefcdd927c649f7eb60b05ee"): Account(
                    storage={0: 24576}
                ),
                Address("0x9c191b43e684189f0bb14204f0b60f52e7e31800"): Account(
                    storage={0: 24576}
                ),
                Address("0x9cefd6dfd201466bcc8660fadfe779ad84e51035"): Account(
                    storage={0: 24576}
                ),
                Address("0x9d10dcbc98f78393a77f384c2d5a85ac77dc03fb"): Account(
                    storage={0: 24576}
                ),
                Address("0x9da6b16741ad3fea4cbc6fec1cbf40222edf8428"): Account(
                    storage={0: 24576}
                ),
                Address("0x9dbc2d09bb39017b664df01a88116ae746f41e87"): Account(
                    storage={0: 24576}
                ),
                Address("0x9f06236f6bbc43f8e9dc6cc27535fbc5b4df2968"): Account(
                    storage={0: 24576}
                ),
                Address("0x9f13f558023e03e7dfb170a255366bdf10f6cc5b"): Account(
                    storage={0: 24576}
                ),
                Address("0xa0b22b335f81bf3ef9aa288ef42552a01d34dcf3"): Account(
                    storage={0: 24576}
                ),
                Address("0xa0cc667684a51bd538e5d7602cd6fc55b1ce6718"): Account(
                    storage={0: 24576}
                ),
                Address("0xa28e6aa3788e693b543a17080e01f791144f2e9b"): Account(
                    storage={0: 24576}
                ),
                Address("0xa2e43c5a3581af1eede0e10f4003b84eb9368638"): Account(
                    storage={0: 24576}
                ),
                Address("0xa30cf3d83271b69e6197fa49d9f018304e212567"): Account(
                    storage={0: 24576}
                ),
                Address("0xa351ff71f4fd8b6f3874b04b6263d680288fe811"): Account(
                    storage={0: 24576}
                ),
                Address("0xa3c759b6f18c232a1341ed2304cbd5952c9e3c55"): Account(
                    storage={0: 24576}
                ),
                Address("0xa4b939c22ace39e879f458e720d855fc0f6b5c93"): Account(
                    storage={0: 24576}
                ),
                Address("0xa51223385dd45a032f44ffd7941e032cac410ada"): Account(
                    storage={0: 24576}
                ),
                Address("0xa6e9ab9401062d4235410d5b86b251ab4de8407d"): Account(
                    storage={0: 24576}
                ),
                Address("0xa6ee313e03f64eecca90630cb4298e7246b7b058"): Account(
                    storage={0: 24576}
                ),
                Address("0xa6f4afe1dccafc6d36fea6c64b0732268d09cf66"): Account(
                    storage={0: 24576}
                ),
                Address("0xa75e4a2ca659acabce9517b58ce590613c7671a8"): Account(
                    storage={0: 24576}
                ),
                Address("0xaa4680e68d6a2a169e5e732a73c57c02570cda32"): Account(
                    storage={0: 24576}
                ),
                Address("0xac480c906cf962ee3c280babb088bd6b738c8830"): Account(
                    storage={0: 24576}
                ),
                Address("0xac57a076a56bae969b09ae83acd86e1e74688cc0"): Account(
                    storage={0: 24576}
                ),
                Address("0xac80ac315dc1820f3fc02c1e84ebeefe63a5cf6b"): Account(
                    storage={0: 24576}
                ),
                Address("0xac9f2596ca3df3b4d0f7726e4269f728fc3b5513"): Account(
                    storage={0: 24576}
                ),
                Address("0xad501ee176ef7eeff9a7b405c5ba7ebd65f0b3d8"): Account(
                    storage={0: 24576}
                ),
                Address("0xb17ad9ade2750fddb466f227822a9641ddf4b368"): Account(
                    storage={0: 24576}
                ),
                Address("0xb36e4bd752a91835d63187d1a76028633f446717"): Account(
                    storage={0: 24576}
                ),
                Address("0xb9bdd9506b309419030783e39fb338a9d0657b50"): Account(
                    storage={0: 24576}
                ),
                Address("0xbaea4cd4f2c66b8e86231569acfac98105fb371f"): Account(
                    storage={0: 24576}
                ),
                Address("0xbb9815ee614931c4b647fcff59903bd85d43a195"): Account(
                    storage={0: 24576}
                ),
                Address("0xbbda9bf1d8293fd1dcb8b5acd094f0b0be9854a1"): Account(
                    storage={0: 24576}
                ),
                Address("0xbceba3b431a27d67b0d5d1e9e2e543f996dcb1c5"): Account(
                    storage={0: 24576}
                ),
                Address("0xbd205415c24eb289b6a275baae74527b92b49fe2"): Account(
                    storage={0: 24576}
                ),
                Address("0xbea91c3bf16bf4e6682a83cafd23e51d07320c3d"): Account(
                    storage={0: 24576}
                ),
                Address("0xbf2fa91409040bccf9a3057e7b44fed6180964d5"): Account(
                    storage={0: 24576}
                ),
                Address("0xbfb2c6fd3f376fe54cdf43528ea75c4d654520a9"): Account(
                    storage={0: 24576}
                ),
                Address("0xc0c6609d8fec3dbc72fe75b58741c0adc8017d5b"): Account(
                    storage={0: 24576}
                ),
                Address("0xc1aed2b66223b9945bfc1ded7b8ebd1a2b0b558c"): Account(
                    storage={0: 24576}
                ),
                Address("0xc3b253f5eebfbd146945c8c8f9a6387548724793"): Account(
                    storage={0: 24576}
                ),
                Address("0xc412ac76da31762387ebf037b7ab858630be14fb"): Account(
                    storage={0: 24576}
                ),
                Address("0xc4640f70c30da2a012c272fb6b35ac3bdf2faa1d"): Account(
                    storage={0: 24576}
                ),
                Address("0xc5b42bd4e227777fa40fcc664361a4b2aa92cd2e"): Account(
                    storage={0: 24576}
                ),
                Address("0xc61255fc2d9231a8ad0ff0bcdd1dc18e0bc36716"): Account(
                    storage={0: 24576}
                ),
                Address("0xc812181698640e4d903d48905300d09d0b6aca44"): Account(
                    storage={0: 24576}
                ),
                Address("0xcbd155ea3136979e3dd290b98d9213c2378156e7"): Account(
                    storage={0: 24576}
                ),
                Address("0xcd0e1ca16526f06894785b0c3f70da8e12c840c7"): Account(
                    storage={0: 24576}
                ),
                Address("0xcd7dab3a880d717525774e609007fe293fb3c6f2"): Account(
                    storage={0: 24576}
                ),
                Address("0xcf88cbac56d349d1d84608fd65f326335f9d231b"): Account(
                    storage={0: 24576}
                ),
                Address("0xcf95a24035f540e1d4f4c2d5dd23907c65d25c25"): Account(
                    storage={0: 24576}
                ),
                Address("0xd02bf23894916bed08d673bd9137e250a05cbe24"): Account(
                    storage={0: 24576}
                ),
                Address("0xd1266923606dbf8316d9a309d11dfe01046bdcca"): Account(
                    storage={0: 24576}
                ),
                Address("0xd151f07b9d42f35be65e24648c6666e2cbf6eb65"): Account(
                    storage={0: 24576}
                ),
                Address("0xd26f2c133e89a7529f5b55eee3a69cad1c0d162a"): Account(
                    storage={0: 24576}
                ),
                Address("0xd2fd46818ca3704f604fd8576d6949de46d2615f"): Account(
                    storage={0: 24576}
                ),
                Address("0xd3da3859340f1bceb3c9446dd317fcda11cdef8d"): Account(
                    storage={0: 24576}
                ),
                Address("0xd43081adf2b74142abe506a7a0876282a01ef49b"): Account(
                    storage={0: 24576}
                ),
                Address("0xd463d91663aa618c69c07806ba6f73b7f01e706e"): Account(
                    storage={0: 24576}
                ),
                Address("0xd4afca98581c37bf178054492f6dab0589ee711b"): Account(
                    storage={0: 24576}
                ),
                Address("0xd61f89dc08860ee934633c02f49b7085518f731b"): Account(
                    storage={0: 24576}
                ),
                Address("0xd6927a4164b187980d0a503535bb94af52571faa"): Account(
                    storage={0: 24576}
                ),
                Address("0xd6f074b660f8ad09331a383ed48db828204e1ea6"): Account(
                    storage={0: 24576}
                ),
                Address("0xd7b1c8b11acd78fa3125d7ee69932370fa9a533b"): Account(
                    storage={0: 24576}
                ),
                Address("0xd7cb633e099309c2a91161a933ef489e7d9671b7"): Account(
                    storage={0: 24576}
                ),
                Address("0xda1b4f166ae6d95a678d8a3c4eca060f0b2d6a57"): Account(
                    storage={0: 24576}
                ),
                Address("0xdafa6d1c2ea9f96df2ce75a706b8b1ee435bb7a7"): Account(
                    storage={0: 24576}
                ),
                Address("0xdb2ac5470240c92226eaed73a5c34533a9304766"): Account(
                    storage={0: 24576}
                ),
                Address("0xdc6bb7ce6f6eff34c2ee81ad05ec8d7631719b7b"): Account(
                    storage={0: 24576}
                ),
                Address("0xdc9765208a36a8aaf7f475389c868a14d961c441"): Account(
                    storage={0: 24576}
                ),
                Address("0xde6f03bdbba9eb4b8becc08112dae6215dfdb95c"): Account(
                    storage={0: 24576}
                ),
                Address("0xdebe3f92bd63cfdb1ab101cb4b1546b96170b716"): Account(
                    storage={0: 24576}
                ),
                Address("0xded1c9cd48d8a533d740319fbf315a68c1d65cbd"): Account(
                    storage={0: 24576}
                ),
                Address("0xdefd25b398b32da0afa86c952c858e274783dae1"): Account(
                    storage={0: 24576}
                ),
                Address("0xdf61cf5f503998e276d793e92a32af594040f937"): Account(
                    storage={0: 24576}
                ),
                Address("0xdf886c55b8f41489b52494a0ccb90ba70dda997e"): Account(
                    storage={0: 24576}
                ),
                Address("0xe0094e969365326a29193fcab569ae60f5e54945"): Account(
                    storage={0: 24576}
                ),
                Address("0xe0cae5c048a12782a2efdec6d562e56611396c45"): Account(
                    storage={0: 24576}
                ),
                Address("0xe790ad9580ac0bea21227734986f57f3ee3c1a84"): Account(
                    storage={0: 24576}
                ),
                Address("0xe910a8ca565ec674f2a46eda4d722ea1f1938d95"): Account(
                    storage={0: 24576}
                ),
                Address("0xeafabe69ca5e42707bf4d44f2ec4a782583ed97c"): Account(
                    storage={0: 24576}
                ),
                Address("0xebce9236147061a129aa9496c430e1bb0889f8e6"): Account(
                    storage={0: 24576}
                ),
                Address("0xed77f383abf53117deffe2e56d013e8087d41edb"): Account(
                    storage={0: 24576}
                ),
                Address("0xee181e7b8a23dd52c3560427a14a4e2339d28b1b"): Account(
                    storage={0: 24576}
                ),
                Address("0xee27c2a7b3b6f044c59d05555cbb81f473042cdc"): Account(
                    storage={0: 24576}
                ),
                Address("0xeea5c1baff7b7b1e8196bd5afa6c6d18b9be4b2d"): Account(
                    storage={0: 24576}
                ),
                Address("0xef0c6075b5cba0dfecda04952e19cc4264867a67"): Account(
                    storage={0: 24576}
                ),
                Address("0xf000b382b68194ed352685fc99c583225ecc5de0"): Account(
                    storage={0: 24576}
                ),
                Address("0xf13479778d51d2cc64c1d9f983306e8dfcdcac6c"): Account(
                    storage={0: 24576}
                ),
                Address("0xf2a3ea55e5dd2d0a119b6b1c4076baffa7ae6869"): Account(
                    storage={0: 24576}
                ),
                Address("0xf316028cf521c739d9ee401490316226be239860"): Account(
                    storage={0: 24576}
                ),
                Address("0xf38d8de0d20676358b74f0275f5a6874c68836db"): Account(
                    storage={0: 24576}
                ),
                Address("0xf39fcb2d6cdaf2a8d9bfd1a4d8ae7b3f179bebae"): Account(
                    storage={0: 24576}
                ),
                Address("0xf454233cead1d5e7e2b9fa211a9d53ef68596d8d"): Account(
                    storage={0: 24576}
                ),
                Address("0xf4d88c8a72b7e57149c2ea7b3f470503d774a79b"): Account(
                    storage={0: 24576}
                ),
                Address("0xf513793f67421ab27eb347562356faf1896d8666"): Account(
                    storage={0: 24576}
                ),
                Address("0xf669f56570a0b318051ea10c0bb6283feb1b2e7d"): Account(
                    storage={0: 24576}
                ),
                Address("0xf68aab9af66e3a0d817c122cd794f2bc1baa18d1"): Account(
                    storage={0: 24576}
                ),
                Address("0xfb4a3af2f0dd26eb2175e4125ace12f82d6f5050"): Account(
                    storage={0: 24576}
                ),
                Address("0xfc1fd51bddf33415d2518a8e2b334504e4698307"): Account(
                    storage={0: 24576}
                ),
                Address("0xfd10ec14dcb59438c9172dcdad21a45eb29a47b2"): Account(
                    storage={0: 24576}
                ),
                Address("0xfd2525a0ad5e89a50cca0220e071712deb4482e0"): Account(
                    storage={0: 24576}
                ),
                Address("0xfe5731d330bf0508c4eac46618d5c13bcf5db7a4"): Account(
                    storage={0: 24576}
                ),
                Address("0xfff4b3a27da4bb06d74a040bcff00d8e995f9a19"): Account(
                    storage={0: 24576}
                ),
            },
        ),
        (
            "a6f227c000000000000000000000000000000000000000000000000000000000000000fa00000000000000000000000000000000000000000000000000000000000000fa000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001ee",  # noqa: E501
            {
                Address("0x00000000000000000000000000000000000c0dea"): Account(
                    storage={1: 1}
                ),
                Address("0x00000000000000000000000000000000000c0deb"): Account(
                    storage={1: 1}
                ),
                Address("0x511c6c5591eacfc8b9bf2658916225418508f548"): Account(
                    storage={0: 24576}
                ),
                Address("0x782f34ee13897680a5000838ce53d07b9558b5e2"): Account(
                    storage={0: 24576}
                ),
                Address("0x9ca6a1cfda677fc2679fce570dd47120686cb7c0"): Account(
                    storage={0: 24576}
                ),
                Address("0xdf7cd0b9839e4d93b98f09bf4c79366b9ffbe638"): Account(
                    storage={0: 24576}
                ),
                Address("0xe0fad4310f169961f052ac02bb70707ebfa3ece2"): Account(
                    storage={0: 24576}
                ),
                Address("0xee8b40edee25283a8c934b9c3a2ad8c848dc61b9"): Account(
                    storage={0: 24576}
                ),
            },
        ),
        (
            "a6f227c0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000fa00000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            {
                Address("0x00000000000000000000000000000000000c0dea"): Account(
                    storage={1: 1}
                )
            },
        ),
        (
            "a6f227c0000000000000000000000000000000000000000000000000000000000000000a000000000000000000000000000000000000000000000000000000000000000a00000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            {
                Address("0x00000000000000000000000000000000000c0dea"): Account(
                    storage={1: 1}
                ),
                Address("0x1a2dfe43e35a2a2bc4719ef2126af20066b636e5"): Account(
                    storage={0: 24576}
                ),
                Address("0x1e4802f8e20a034148f9f7e9f7ff8fcf89a1f3c8"): Account(
                    storage={0: 24576}
                ),
                Address("0x396b47fae89161b1959b5a833acf816be526b860"): Account(
                    storage={0: 24576}
                ),
                Address("0x4b2c1b96e4b881960f7241f496a85155136528c6"): Account(
                    storage={0: 24576}
                ),
                Address("0x7e3bd590a907dd2efd9a59ff5a323060ef22d805"): Account(
                    storage={0: 24576}
                ),
                Address("0x92ccd8ac1dda8d6f1c2a8cd9b51dc56c44febe74"): Account(
                    storage={0: 24576}
                ),
                Address("0x995576eccf99c1152b573e092fc068f9809ebabf"): Account(
                    storage={0: 24576}
                ),
                Address("0xbd205415c24eb289b6a275baae74527b92b49fe2"): Account(
                    storage={0: 24576}
                ),
                Address("0xc412ac76da31762387ebf037b7ab858630be14fb"): Account(
                    storage={0: 24576}
                ),
                Address("0xc812181698640e4d903d48905300d09d0b6aca44"): Account(
                    storage={0: 24576}
                ),
            },
        ),
        (
            "a6f227c0000000000000000000000000000000000000000000000000000000000000000a000000000000000000000000000000000000000000000000000000000000000a0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000e",  # noqa: E501
            {
                Address("0x00000000000000000000000000000000000c0dea"): Account(
                    storage={1: 1}
                ),
                Address("0x00000000000000000000000000000000000c0deb"): Account(
                    storage={1: 1}
                ),
                Address("0x2e5a5ec103443f6b299cf31a52c69cf222ae4e6b"): Account(
                    storage={0: 24576}
                ),
                Address("0x67262aa10552371ec665c2f90c56d9d65c16715e"): Account(
                    storage={0: 24576}
                ),
                Address("0xb3210b741a5dfbddc1636521965b3558defa3e60"): Account(
                    storage={0: 24576}
                ),
                Address("0xbade62b355fe6b7117f4f7c913321b318ca3a4da"): Account(
                    storage={0: 24576}
                ),
                Address("0xd8a8f3569a1d76027f9ece5010489576897014ea"): Account(
                    storage={0: 24576}
                ),
                Address("0xfcdccc3b46b9fbe71221061091e8fe82b77e02f2"): Account(
                    storage={0: 24576}
                ),
            },
        ),
        (
            "a6f227c00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000a00000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            {
                Address("0x00000000000000000000000000000000000c0dea"): Account(
                    storage={1: 1}
                )
            },
        ),
    ],
    ids=["case0", "case1", "case2", "case3", "case4", "case5"],
)
@pytest.mark.pre_alloc_mutable
def test_create_oo_gafter_max_codesize(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    expected_post: dict,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=4294967296,
    )

    # Source: Yul
    # {
    #   // If calldata > 0, self-destruct, otherwise
    #   sstore(0, codesize())
    #   if gt(calldatasize(), 0) {
    #     selfdestruct(0)
    #   }
    # }
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=Op.CODESIZE)
            + Op.JUMPI(pc=0xC, condition=Op.GT(Op.CALLDATASIZE, 0x0))
            + Op.STOP
            + Op.JUMPDEST
            + Op.SELFDESTRUCT(address=0x0)
        ),
        nonce=0,
        address=Address("0x00000000000000000000000000000000000c0de0"),  # noqa: E501
    )
    # Source: Yul
    # {
    #   // Init code that uses max codesize and can be called to selfdestruct
    #   let code_addr := 0x00000000000000000000000000000000000c0de0
    #   extcodecopy(code_addr, 0, 0, extcodesize(code_addr))
    #   return(0, 0x6000)
    # }
    pre.deploy_contract(
        code=(
            Op.PUSH3[0xC0DE0]
            + Op.PUSH1[0x0]
            + Op.DUP1
            + Op.EXTCODESIZE(address=Op.DUP3)
            + Op.SWAP3
            + Op.EXTCODECOPY
            + Op.RETURN(offset=0x0, size=0x6000)
        ),
        nonce=0,
        address=Address("0x00000000000000000000000000000000000c0de1"),  # noqa: E501
    )
    # Source: Yul
    # {
    #
    #   // Get the amount of contracts to create on this level
    #   let delegate_contract_count := calldataload(4)
    #
    #   // Get the amount of contracts to create on the sub level call
    #   let subcall_contract_count := calldataload(36)
    #
    #   // Get whether the subcall should oog
    #   let subcall_oog := calldataload(68)
    #
    #   // Get count of contracts to call to self-destruct
    #   let selfdestruct_count := calldataload(100)
    #
    #   // Delegate call for contract creation
    #   mstore(0, delegate_contract_count)
    #   mstore(32, 0)
    #   let returnStart := 64
    #   let returnLength := mul(delegate_contract_count, 32)
    #   let retcode := delegatecall(div(gas(), 2), 0x00000000000000000000000000000000000c0deb, 0, 64, returnStart, returnLength)  # noqa: E501
    #
    #   if eq(retcode, 0) {
    #     // We oog'd, fail test
    #     revert(0, 0)
    #   }
    #
    #   // Call for OOG contract creation
    #   mstore(0, subcall_contract_count)
    #   mstore(32, subcall_oog)
    #   returnStart := add(64, mul(delegate_contract_count, 32))
    # ... (30 more lines)
    contract = pre.deploy_contract(
        code=(
            Op.CALLDATALOAD(offset=0x4)
            + Op.CALLDATALOAD(offset=0x24)
            + Op.CALLDATALOAD(offset=0x44)
            + Op.SWAP1
            + Op.CALLDATALOAD(offset=0x64)
            + Op.SWAP3
            + Op.MSTORE(offset=0x0, value=Op.DUP1)
            + Op.MSTORE(offset=0x20, value=0x0)
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x40]
            + Op.MUL(Op.DUP4, 0x20)
            + Op.SWAP1
            + Op.PUSH1[0x40]
            + Op.DUP4
            + Op.PUSH3[0xC0DEB]
            + Op.JUMPI(
                pc=0xBF,
                condition=Op.EQ(Op.DELEGATECALL, Op.DIV(Op.GAS, 0x2)),
            )
            + Op.MSTORE(offset=0x0, value=Op.DUP2)
            + Op.MSTORE(offset=0x20, value=Op.DUP3)
            + Op.PUSH1[0x0]
            + Op.ADD(0x40, Op.MUL(Op.DUP3, 0x20))
            + Op.MUL(Op.DUP5, 0x20)
            + Op.SWAP1
            + Op.PUSH1[0x40]
            + Op.DUP4
            + Op.DUP1
            + Op.PUSH3[0xC0DEB]
            + Op.JUMPI(pc=0xBA, condition=Op.EQ(Op.CALL, Op.DIV(Op.GAS, 0x2)))
            + Op.JUMPDEST
            + Op.PUSH1[0x0]
            + Op.DUP2
            + Op.SWAP4
            + Op.JUMPI(pc=0xB1, condition=Op.EQ)
            + Op.JUMPDEST
            + Op.POP
            + Op.POP
            + Op.PUSH1[0x0]
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x94, condition=Op.LT(Op.DUP2, Op.DUP2))
            + Op.DUP3
            + Op.PUSH1[0x0]
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x77, condition=Op.LT(Op.DUP2, Op.DUP2))
            + Op.STOP
            + Op.JUMPDEST
            + Op.DUP1
            + Op.PUSH1[0x0]
            + Op.DUP1
            + Op.PUSH1[0x1]
            + Op.DUP2
            + Op.DUP1
            + Op.PUSH1[0x20]
            + Op.DUP4
            + Op.SWAP8
            + Op.MLOAD(offset=Op.ADD(0x40, Op.MUL))
            + Op.SUB(Op.GAS, 0x3E8)
            + Op.POP(Op.CALL)
            + Op.ADD
            + Op.JUMP(pc=0x6F)
            + Op.JUMPDEST
            + Op.DUP1
            + Op.PUSH1[0x0]
            + Op.DUP1
            + Op.DUP1
            + Op.DUP1
            + Op.DUP1
            + Op.PUSH1[0x20]
            + Op.PUSH1[0x1]
            + Op.SWAP8
            + Op.MLOAD(offset=Op.ADD(0x40, Op.MUL))
            + Op.SUB(Op.GAS, 0x3E8)
            + Op.POP(Op.CALL)
            + Op.ADD
            + Op.JUMP(pc=0x65)
            + Op.JUMPDEST
            + Op.ADD
            + Op.SWAP1
            + Op.POP
            + Op.CODESIZE
            + Op.DUP1
            + Op.JUMP(pc=0x60)
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x57, condition=Op.DUP3)
            + Op.JUMPDEST
            + Op.REVERT(offset=Op.DUP1, size=0x0)
        ),
        address=Address("0x00000000000000000000000000000000000c0dea"),  # noqa: E501
    )
    # Source: Yul
    # {
    #   sstore (1, 1)
    #   let contract_count := calldataload(0)
    #   let should_oog := calldataload(32)
    #
    #   // get the init code that returns max codesize from another contract
    #   let initcode_addr := 0x00000000000000000000000000000000000c0de1
    #   let initcode_size := extcodesize(initcode_addr)
    #   extcodecopy(initcode_addr, 0, 0, initcode_size)
    #
    #   // create contracts with max codesize in loop
    #   for { let i := 0 } lt(i, contract_count) { i := add(i, 1) }
    #   {
    #       let address_created := create(0, 0, initcode_size)
    #       mstore( add(initcode_size, mul(i, 32)), address_created )
    #   }
    #   if gt(should_oog, 0) {
    #     invalid()
    #   }
    #   return(initcode_size, mul(contract_count, 32))
    # }
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=Op.DUP1, value=0x1)
            + Op.PUSH1[0x0]
            + Op.CALLDATALOAD(offset=Op.DUP1)
            + Op.CALLDATALOAD(offset=0x20)
            + Op.PUSH3[0xC0DE1]
            + Op.DUP4
            + Op.EXTCODESIZE(address=Op.DUP2)
            + Op.SWAP5
            + Op.DUP6
            + Op.SWAP3
            + Op.EXTCODECOPY
            + Op.PUSH1[0x0]
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x2D, condition=Op.LT(Op.DUP2, Op.DUP3))
            + Op.POP
            + Op.PUSH1[0x0]
            + Op.JUMPI(pc=0x2B, condition=Op.LT)
            + Op.PUSH1[0x20]
            + Op.MUL
            + Op.SWAP1
            + Op.RETURN
            + Op.JUMPDEST
            + Op.INVALID
            + Op.JUMPDEST
            + Op.PUSH1[0x1]
            + Op.SWAP1
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP7, Op.MUL(Op.DUP3, 0x20)),
                value=Op.CREATE(value=Op.DUP1, offset=0x0, size=Op.DUP5),
            )
            + Op.ADD
            + Op.JUMP(pc=0x18)
        ),
        address=Address("0x00000000000000000000000000000000000c0deb"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xBA1A9CE0BA1A9CE)

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=contract,
        data=tx_data,
        gas_limit=4294967296,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
