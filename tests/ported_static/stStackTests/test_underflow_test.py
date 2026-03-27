"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
state_tests/stStackTests/underflowTestFiller.yml
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
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"

REFERENCE_SPEC_VERSION = "N/A"

TX_DATA = [
    "693c61390000000000000000000000003aac251f428dcd7cb57e01c7dbb8bc3a76d5d628",
    "693c6139000000000000000000000000cc44bebaeb76a6568aa26ae045f8516fa29b0f9c",
    "693c6139000000000000000000000000e383f3e5b45fa86d5b37cdfeb146cf903641c76c",
    "693c6139000000000000000000000000da3ec48d60f1cf78ecc154fa0c6181cf833916aa",
    "693c6139000000000000000000000000b50944b674eb20b0fe99a18bb764b45500c41144",
    "693c6139000000000000000000000000fcc0a7ebcab4f6d8c91c9062f2cd1148073253d2",
    "693c6139000000000000000000000000d54c502b5478a191e9a25bc0d1ba94669c5a5f4f",
    "693c6139000000000000000000000000836d0c3ce82596908935c3cc794da4603e135b1c",
    "693c6139000000000000000000000000c131d96e30386b63f89592008939dd517579f203",
    "693c613900000000000000000000000058cd7cc2b1b1cd459decc8ebbbd2fcbf9c68cef9",
    "693c61390000000000000000000000005df0dd6d100e8dd03d211b55d4a8cc7c7657c038",
    "693c61390000000000000000000000004e985c32a0f53ab426fe2bcdea720f0f71a4c1d1",
    "693c61390000000000000000000000009d8ea14af8d401208eb0687b8ae6f1e5ed6808d4",
    "693c613900000000000000000000000018c875e7eb21e50bad81e8940a2272fd6760e0dd",
    "693c6139000000000000000000000000c51017527cdd990d0c8e146ed36237694024021c",
    "693c613900000000000000000000000023d790b6f14975963ee30ff45cc4621c7e1eeaf7",
    "693c61390000000000000000000000000824de5bb894849fcdd60634275d6bcb8157d4a0",
    "693c6139000000000000000000000000da24ffd288756277e556671ae2306b7587ef0c63",
    "693c6139000000000000000000000000c36332f339266d7989b005864c48548883213125",
    "693c6139000000000000000000000000973b5cc7e4678bcb85618b38c910f8adc68703a6",
    "693c61390000000000000000000000001e27cc27790c60dde31215bf2be1d9a66c41c8fa",
    "693c61390000000000000000000000001523b84a9fb4a0d32f070847190d34f912c04c4e",
    "693c613900000000000000000000000077225976113d69eee2fd870ea02d670badabdcab",
    "693c61390000000000000000000000002947a82b8aabd0f80c7e215bc066ea92bdd65b31",
    "693c6139000000000000000000000000f9a965915f18a6108b842a40148dc5fd47ec7140",
    "693c6139000000000000000000000000d60ab3d73fd71f071ede5eead527db298236b162",
    "693c6139000000000000000000000000e519ac21322361b960bed6ccbbf538840e85f76e",
    "693c6139000000000000000000000000c74809261edc3edd91ec17dbf4b898233c42ddb4",
    "693c6139000000000000000000000000cc9ffede5b0d7f58002f852181d0b4b35c0dabee",
    "693c61390000000000000000000000000bdf35fc6c5c2a3e1e9711112ff7ef71e2419532",
    "693c61390000000000000000000000002b3bc02cabba968640fd86614f855a406b5c32e2",
    "693c61390000000000000000000000005029d082367aa4510d5a6e3b5cf83cd41e05c7f4",
    "693c6139000000000000000000000000c744cf16cf5e2eb3c97e641e63801b8af3015def",
    "693c6139000000000000000000000000be25986eb0ee281252e783918d867630e5119455",
    "693c61390000000000000000000000001029b338aa781a64308000fa49515769618f176e",
    "693c6139000000000000000000000000c8d2eb10090f9940b7e816e6a278ae2ec943d232",
    "693c61390000000000000000000000007d00c3c2cbb3b64bbb4f0f518ef779f6df875f6e",
    "693c6139000000000000000000000000e8565720ba47032e7b0edcb4bce06303f83ff450",
    "693c61390000000000000000000000004c47590ab3f1dfe486900d0ec41510f85545b182",
    "693c61390000000000000000000000009b0edd3cf5b6ccc09b3c9d15646ef629a7767ba8",
    "693c613900000000000000000000000010df9321d0355308a994d3709e30609bd72655b7",
    "693c6139000000000000000000000000c52f28d6433f203eae23f5f2fc642938a25aafe7",
    "693c61390000000000000000000000001be71f78fcfbc7e4002db615e7fc878e7f090c50",
    "693c6139000000000000000000000000f04fe60ad6f92fa14a53a0882943a66ea4e49ef1",
    "693c6139000000000000000000000000a7b1cd72ebc0b8f3e353885ef17b04aa28d8f0fa",
    "693c6139000000000000000000000000701a7d6aa6ef15a38fd8311e074a96c09b434a2a",
    "693c6139000000000000000000000000c024f0f81b1c2c1ab6362e5ecf79a7be3de2f60e",
    "693c6139000000000000000000000000a49e66f497a85d949d334a20724bc6b75da3d3ae",
    "693c6139000000000000000000000000b37c41d445866ceb36edc4e6456cae78949c9f97",
    "693c61390000000000000000000000008e689eee6c7387a37612a42f8ee44dd7a823fb5c",
    "693c6139000000000000000000000000ec8b92806c1ad0f2dcf5b0207db7eddb464df0ca",
    "693c613900000000000000000000000011ffe11bb835b6ce89fc91d65b1f6c0919b07a1d",
    "693c6139000000000000000000000000943b918e625b3ecb5d186d820a60c8eebd1c71ec",
    "693c613900000000000000000000000058a413dde8ddd92c793fca0b18ce89bd3dfba0e8",
    "693c6139000000000000000000000000c24790535cfea9781d66d59b81d9b92a576bb9ef",
    "693c6139000000000000000000000000488a9b0f0e885b96f67c113f0979799f801d70d3",
    "693c613900000000000000000000000059f8c0328e432df7467313742e1effc9ee2bac4e",
    "693c6139000000000000000000000000bc57a2f2490132b8f8980cd242f7dc76b4b3f1c3",
    "693c613900000000000000000000000050a33da19f003aec73bc65754e12a7f94c9b1c34",
    "693c6139000000000000000000000000866777eaddc2be0a50b3d3f76f2064876ea42802",
    "693c6139000000000000000000000000664f23c7af786dc61b6a068b3f9bde0051716384",
    "693c613900000000000000000000000075a2a8afa2446ec88a716ef7074351accfaccadf",
    "693c613900000000000000000000000093d0507f681ba7de662d14ae8de922d161698c8e",
    "693c6139000000000000000000000000bf337119d0b966cc500cd3ff5ab9f3c7fddaa91d",
    "693c61390000000000000000000000007142d01ed8802179659127719398fa679ac41292",
    "693c6139000000000000000000000000a3d5aecbf6541cd2a0df5ae2e1294abc682180e6",
    "693c61390000000000000000000000006f72794f9c9d8a693ff6c1134d611d353678fcf0",
    "693c6139000000000000000000000000b8479583829f24d888a0493a9132845b3d6a5305",
    "693c61390000000000000000000000005f750bad38b37c4ebcc5fee4eed5639283a09a38",
    "693c613900000000000000000000000014ed6c71ebccdf69007d79fe699d368102533929",
    "693c613900000000000000000000000092bfb1aa73e92c1f591d8b6854514df6672bbb90",
    "693c6139000000000000000000000000b2e76a6fdfc66a93a2354748ec2d107a818fe73c",
    "693c6139000000000000000000000000ec26e590a6f5da137088aee0c4d6b0f8870eb1ad",
    "693c6139000000000000000000000000ac95d1d1c86af90f5a0cf44c104d0da04ab3a467",
    "693c6139000000000000000000000000a1903db9aa9aa2665ca7da383db9291d93f1d576",
    "693c6139000000000000000000000000891e304c4126f24bf762df079c7683420b16ff57",
    "693c61390000000000000000000000007aedaf23d4e9afb84baa67824cebfec01339afc1",
    "693c61390000000000000000000000005096db6b2ea6ace8e2aeb3610faaad183a51ca8d",
    "693c613900000000000000000000000017f25a871ea2ea564cffe99d31dedcf1fcff0a63",
    "693c6139000000000000000000000000fb5dbfcd64b16ab0129b99278b9d5ccfb9b605b9",
    "693c6139000000000000000000000000c70e97b872035f925b07db55b85a3eac04e724d6",
    "693c6139000000000000000000000000d051afb76160844eb32df55e052044de76250ebc",
    "693c6139000000000000000000000000dac05b6fc9dc9c0b65ecc5032f2313f7a7dd2586",
    "693c61390000000000000000000000003fd249e0be1d7bf6386b7dc90d92bf95f9f98bc4",
    "693c6139000000000000000000000000a7eec8574dbfc883575f2b20a80f14f335a809b6",
    "693c613900000000000000000000000022d7d32459b46a9b69542c31545cb3a0d887064c",
    "693c6139000000000000000000000000715f213243cd7baeefd3a52434353015a4fc8de2",
    "693c613900000000000000000000000079d8aedd70f8a99a15e3083d3335a028d69af9fa",
    "693c613900000000000000000000000016a80f6c0bbed421a0d6b392e891a52fca715213",
    "693c61390000000000000000000000009bd8e7c30198bd73a39e51d6866b72026272773e",
    "693c6139000000000000000000000000f465862e7bf5085fb692e16d3181afaba87550cc",
    "693c61390000000000000000000000008ce099e0d9e5e5153e578f7cbfa9fd071b714142",
    "693c61390000000000000000000000008e3ab300e3d93ac55727c65510ff8bd96ea76928",
    "693c6139000000000000000000000000af6ead2e1a296b787d4b084d30b0733518fd2462",
    "693c613900000000000000000000000084798b4fb35d09db14ecab9d65a4a280e483fe29",
    "693c61390000000000000000000000007d002cacbe954f4360fe634fbe23f5b67c686cbf",
    "693c6139000000000000000000000000799721e570bcd85be50c0d7a399af369be561fbe",
    "693c61390000000000000000000000009386c3cce8cab9f8c3bc1a89c82a0e55588ced9d",
    "693c6139000000000000000000000000933cb75e0e03a16aa3d3e7114d269a6fe4db46f9",
    "693c6139000000000000000000000000f1cfc656c8d8e2bcfdfea0e0e9cabcc0b743dd19",
    "693c6139000000000000000000000000ee8790666225df6f97ae194e20853f2907bbaebc",
    "693c613900000000000000000000000045952ed2c957691ae4de05032b429a8a0f0ced5b",
    "693c61390000000000000000000000008ceb89e3037b7ac8b58e3765ea3eb65f1a9e4a7c",
    "693c61390000000000000000000000005782c86be10d218c82d509f3257e9dfdbf6dead8",
    "693c6139000000000000000000000000e6d703c31f83bc617a62f78e3c3a615001d3dd2c",
    "693c6139000000000000000000000000113855e9aa747f6ae6fd74667d7a288b2288caf6",
    "693c61390000000000000000000000002c2938555e004cbb0ce4481bad8a15857d983d06",
    "693c613900000000000000000000000063e21ad1535b95aaeed05e893b5b7947d6b0f15a",
    "693c61390000000000000000000000005bce589f39f0eff323bcbeac539dc9fd0f429bd2",
    "693c61390000000000000000000000008030a1eb20b388143f12fb547b5e53a4c164a621",
    "693c61390000000000000000000000005bb0e367bec7d734cb0fc9c27eb85af479b39673",
    "693c6139000000000000000000000000e594a68387d42d18bb8e460cef74876f05985e3a",
    "693c61390000000000000000000000009a90a463d916b189eee17b331f27a54142b79961",
    "693c6139000000000000000000000000029d8125096a81237be857845270ab34afab88ac",
    "693c61390000000000000000000000000d423fa4896aca0a02cba41462e754c3241427f0",
    "693c6139000000000000000000000000ca098deb4ab81002cddbd3c93261d6d1cb5113b5",
    "693c6139000000000000000000000000fbc09ac707fcca4ae8e348f01457ea18825bd139",
    "693c6139000000000000000000000000662d9872215dde44ec296918a0fd96c45c97b332",
    "693c6139000000000000000000000000aeec863f85b9a222ac1ffff774a881d46ec3ad37",
    "693c61390000000000000000000000005d4fa1456fbf03872b922dc0e8e48ec49f5faf9e",
    "693c61390000000000000000000000004da0082f56c3cae860eb6fb0fe36bc17cfba2c27",
    "693c6139000000000000000000000000444a2203a30517f4a8becca90192b193a7b6ecf3",
    "693c6139000000000000000000000000d5765c6e58b373df78d7311fe80a67de0ddf987e",
    "693c6139000000000000000000000000742bf896d715c00eb77f340fcaa65bacaee2467c",
    "693c6139000000000000000000000000c698050f674750bbcafa30c433633dee22b8a9d3",
    "693c61390000000000000000000000006ce1b9fedca232f6829f0831ed2c23bd9c2f99a2",
    "693c613900000000000000000000000091605658e9533e831c9f855874faa14c363dc795",
    "693c6139000000000000000000000000f2578fadcdd5cd7b55f7046c88a7a77e195a7b17",
    "693c613900000000000000000000000034fb465a898787f7ed08bc2f5de86a896f8bc4da",
    "693c6139000000000000000000000000f84f405591be4ab47ca2ca1841dcb57cc43f076f",
    "693c61390000000000000000000000002cd79f853ec648b7c3ec3fac7c7ce82d7d83ea1e",
    "693c61390000000000000000000000000cd1b3e02e0bc556b0c7d4779c69a9a383c0c7cd",
    "693c6139000000000000000000000000175de68007e136237a4f26b6983dbce27a87fb5b",
    "693c61390000000000000000000000009c8fc002a1dcd0edcf93c20dc9d674031dc5a28d",
    "693c61390000000000000000000000008b62b65db3bd1be727290b490c679c0e84585498",
    "693c61390000000000000000000000006c6bc4f9ccde5da559a3e5dddb6b60a8675c0076",
    "693c6139000000000000000000000000e98c1ab0ff23d5c5005c639781d1a635b9af887b",
    "693c6139000000000000000000000000acda51eb0d678a0d52bfa44e4354d8f371f43438",
    "693c61390000000000000000000000009768a9bb367830f3331b0c09d7183c131e44a7fc",
    "693c6139000000000000000000000000d6bb0ea7c7f60c967d3deeeaaba555daafbc52cb",
    "693c613900000000000000000000000019598106d1cede298b275523e64593c95d5c431c",
    "693c6139000000000000000000000000b44c7350f24bb5482057b53911a1d3c91c263eaf",
    "693c61390000000000000000000000000d0e14670e6e8718377bc2fae6b6814d558d3dee",
    "693c6139000000000000000000000000a15fe2669809ddc6640e94572907a53411b2aa6e",
    "693c6139000000000000000000000000d435f13e92f7db306b9b32e1d61db6ecd9c135bd",
    "693c6139000000000000000000000000c3fce336558080ef8b1a20a209b173e6d163e548",
    "693c6139000000000000000000000000620d85c5acc41cbfa47a763bbb9e326054b1819d",
    "693c61390000000000000000000000009b9d04770c429114574c11780fc9658d3257e80b",
    "693c613900000000000000000000000044c420a5b1a9071eb7ff6f1027c167c002c7f355",
    "693c6139000000000000000000000000dcb6a7c9b64471effdd8bbf72d32d271deeec8c5",
    "693c61390000000000000000000000003ad6053af54d703f7e7229bd5bf120c908c8513d",
    "693c6139000000000000000000000000d9292de838cd8839d91b496d8a9d25ac102cd821",
    "693c61390000000000000000000000002ac63027195da2ee9ce4cc1dff225ca97d3c2f0c",
    "693c6139000000000000000000000000723a69480f074f5df2544cacf63347fb5f0f36d1",
    "693c613900000000000000000000000073f7599a216d98d9ff1559788a9771d78895a6a3",
    "693c61390000000000000000000000004289634ebf793179377faa7140610bb80db21b45",
    "693c613900000000000000000000000066a62a0af37886b9b057a1bad714665525e7687f",
    "693c61390000000000000000000000001bb096578fe2f1be79e03ea88551a8bdd0692bea",
    "693c6139000000000000000000000000745a759f45602915eab7bdc87bc8d1c1675d4e29",
    "693c6139000000000000000000000000bf99ad09fc2f72924cbe6da6020f985e65f78901",
    "693c6139000000000000000000000000727fd27941dbe4d8f1e2e9daa0df70288fd73772",
    "693c61390000000000000000000000001eb3790937f47fe31a45f55bd82f50107e7a463a",
    "693c6139000000000000000000000000cd63f547ee166a3feb23a945f488ccc5ee921eef",
    "693c61390000000000000000000000008fd69485a26470a721f6dd7e685da39ee2a3dc1c",
    "693c61390000000000000000000000006f631ae51ead55c8526aff13665fe5dd055e3561",
    "693c61390000000000000000000000001debd2afba875db8938ce64218b40fb210e1de0a",
]
TX_GAS = [8000000]
TX_VALUE = [1]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/stStackTests/underflowTestFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="ADD-1",
        ),
        pytest.param(
            1,
            0,
            0,
            id="ADD-2",
        ),
        pytest.param(
            2,
            0,
            0,
            id="MUL-1",
        ),
        pytest.param(
            3,
            0,
            0,
            id="MUL-2",
        ),
        pytest.param(
            4,
            0,
            0,
            id="SUB-1",
        ),
        pytest.param(
            5,
            0,
            0,
            id="SUB-2",
        ),
        pytest.param(
            6,
            0,
            0,
            id="DIV-1",
        ),
        pytest.param(
            7,
            0,
            0,
            id="DIV-2",
        ),
        pytest.param(
            8,
            0,
            0,
            id="SDIV-1",
        ),
        pytest.param(
            9,
            0,
            0,
            id="SDIV-2",
        ),
        pytest.param(
            10,
            0,
            0,
            id="MOD-1",
        ),
        pytest.param(
            11,
            0,
            0,
            id="MOD-2",
        ),
        pytest.param(
            12,
            0,
            0,
            id="SMOD-1",
        ),
        pytest.param(
            13,
            0,
            0,
            id="SMOD-2",
        ),
        pytest.param(
            14,
            0,
            0,
            id="ADDMOD-2",
        ),
        pytest.param(
            15,
            0,
            0,
            id="ADDMOD-3",
        ),
        pytest.param(
            16,
            0,
            0,
            id="MULMOD-2",
        ),
        pytest.param(
            17,
            0,
            0,
            id="MULMOD-3",
        ),
        pytest.param(
            18,
            0,
            0,
            id="EXP-1",
        ),
        pytest.param(
            19,
            0,
            0,
            id="EXP-2",
        ),
        pytest.param(
            20,
            0,
            0,
            id="SIGNEXTEND-1",
        ),
        pytest.param(
            21,
            0,
            0,
            id="SIGNEXTEND-2",
        ),
        pytest.param(
            22,
            0,
            0,
            id="LT-1",
        ),
        pytest.param(
            23,
            0,
            0,
            id="LT-2",
        ),
        pytest.param(
            24,
            0,
            0,
            id="GT-1",
        ),
        pytest.param(
            25,
            0,
            0,
            id="GT-2",
        ),
        pytest.param(
            26,
            0,
            0,
            id="SLT-1",
        ),
        pytest.param(
            27,
            0,
            0,
            id="SLT-2",
        ),
        pytest.param(
            28,
            0,
            0,
            id="SGT-1",
        ),
        pytest.param(
            29,
            0,
            0,
            id="SGT-2",
        ),
        pytest.param(
            30,
            0,
            0,
            id="EQ-1",
        ),
        pytest.param(
            31,
            0,
            0,
            id="EQ-2",
        ),
        pytest.param(
            32,
            0,
            0,
            id="ISZERO-0",
        ),
        pytest.param(
            33,
            0,
            0,
            id="ISZERO-1",
        ),
        pytest.param(
            34,
            0,
            0,
            id="AND-1",
        ),
        pytest.param(
            35,
            0,
            0,
            id="AND-2",
        ),
        pytest.param(
            36,
            0,
            0,
            id="OR-1",
        ),
        pytest.param(
            37,
            0,
            0,
            id="OR-2",
        ),
        pytest.param(
            38,
            0,
            0,
            id="XOR-1",
        ),
        pytest.param(
            39,
            0,
            0,
            id="XOR-2",
        ),
        pytest.param(
            40,
            0,
            0,
            id="NOT-0",
        ),
        pytest.param(
            41,
            0,
            0,
            id="NOT-1",
        ),
        pytest.param(
            42,
            0,
            0,
            id="BYTE-1",
        ),
        pytest.param(
            43,
            0,
            0,
            id="BYTE-2",
        ),
        pytest.param(
            44,
            0,
            0,
            id="SHL-1",
        ),
        pytest.param(
            45,
            0,
            0,
            id="SHL-2",
        ),
        pytest.param(
            46,
            0,
            0,
            id="SHR-1",
        ),
        pytest.param(
            47,
            0,
            0,
            id="SHR-2",
        ),
        pytest.param(
            48,
            0,
            0,
            id="SAR-1",
        ),
        pytest.param(
            49,
            0,
            0,
            id="SAR-2",
        ),
        pytest.param(
            50,
            0,
            0,
            id="SHA3-1",
        ),
        pytest.param(
            51,
            0,
            0,
            id="SHA3-2",
        ),
        pytest.param(
            52,
            0,
            0,
            id="BALANCE-0",
        ),
        pytest.param(
            53,
            0,
            0,
            id="BALANCE-1",
        ),
        pytest.param(
            54,
            0,
            0,
            id="CALLDATALOAD-0",
        ),
        pytest.param(
            55,
            0,
            0,
            id="CALLDATALOAD-1",
        ),
        pytest.param(
            56,
            0,
            0,
            id="CALLDATACOPY-2",
        ),
        pytest.param(
            57,
            0,
            0,
            id="CALLDATACOPY-3",
        ),
        pytest.param(
            58,
            0,
            0,
            id="CODECOPY-2",
        ),
        pytest.param(
            59,
            0,
            0,
            id="CODECOPY-3",
        ),
        pytest.param(
            60,
            0,
            0,
            id="EXTCODESIZE-0",
        ),
        pytest.param(
            61,
            0,
            0,
            id="EXTCODESIZE-1",
        ),
        pytest.param(
            62,
            0,
            0,
            id="EXTCODECOPY-3",
        ),
        pytest.param(
            63,
            0,
            0,
            id="EXTCODECOPY-4",
        ),
        pytest.param(
            64,
            0,
            0,
            id="EXTCODEHASH-0",
        ),
        pytest.param(
            65,
            0,
            0,
            id="EXTCODEHASH-1",
        ),
        pytest.param(
            66,
            0,
            0,
            id="BLOCKHASH-0",
        ),
        pytest.param(
            67,
            0,
            0,
            id="BLOCKHASH-1",
        ),
        pytest.param(
            68,
            0,
            0,
            id="POP-0",
        ),
        pytest.param(
            69,
            0,
            0,
            id="POP-1",
        ),
        pytest.param(
            70,
            0,
            0,
            id="MLOAD-0",
        ),
        pytest.param(
            71,
            0,
            0,
            id="MLOAD-1",
        ),
        pytest.param(
            72,
            0,
            0,
            id="MSTORE-1",
        ),
        pytest.param(
            73,
            0,
            0,
            id="MSTORE-2",
        ),
        pytest.param(
            74,
            0,
            0,
            id="MSTORE8-1",
        ),
        pytest.param(
            75,
            0,
            0,
            id="MSTORE8-2",
        ),
        pytest.param(
            76,
            0,
            0,
            id="SLOAD-0",
        ),
        pytest.param(
            77,
            0,
            0,
            id="SLOAD-1",
        ),
        pytest.param(
            78,
            0,
            0,
            id="LOG0-1",
        ),
        pytest.param(
            79,
            0,
            0,
            id="LOG0-2",
        ),
        pytest.param(
            80,
            0,
            0,
            id="LOG1-2",
        ),
        pytest.param(
            81,
            0,
            0,
            id="LOG1-3",
        ),
        pytest.param(
            82,
            0,
            0,
            id="LOG2-3",
        ),
        pytest.param(
            83,
            0,
            0,
            id="LOG2-4",
        ),
        pytest.param(
            84,
            0,
            0,
            id="LOG3-4",
        ),
        pytest.param(
            85,
            0,
            0,
            id="LOG3-5",
        ),
        pytest.param(
            86,
            0,
            0,
            id="LOG4-5",
        ),
        pytest.param(
            87,
            0,
            0,
            id="LOG4-6",
        ),
        pytest.param(
            88,
            0,
            0,
            id="CREATE-2",
        ),
        pytest.param(
            89,
            0,
            0,
            id="CREATE-3",
        ),
        pytest.param(
            90,
            0,
            0,
            id="CALL-6",
        ),
        pytest.param(
            91,
            0,
            0,
            id="CALL-7",
        ),
        pytest.param(
            92,
            0,
            0,
            id="CALLCODE-6",
        ),
        pytest.param(
            93,
            0,
            0,
            id="CALLCODE-7",
        ),
        pytest.param(
            94,
            0,
            0,
            id="RETURN-1",
        ),
        pytest.param(
            95,
            0,
            0,
            id="RETURN-2",
        ),
        pytest.param(
            96,
            0,
            0,
            id="DELEGATECALL-5",
        ),
        pytest.param(
            97,
            0,
            0,
            id="DELEGATECALL-6",
        ),
        pytest.param(
            98,
            0,
            0,
            id="CREATE2-3",
        ),
        pytest.param(
            99,
            0,
            0,
            id="CREATE2-4",
        ),
        pytest.param(
            100,
            0,
            0,
            id="STATICCALL-5",
        ),
        pytest.param(
            101,
            0,
            0,
            id="STATICCALL-6",
        ),
        pytest.param(
            102,
            0,
            0,
            id="DUP1-0",
        ),
        pytest.param(
            103,
            0,
            0,
            id="DUP1-1",
        ),
        pytest.param(
            104,
            0,
            0,
            id="DUP2-1",
        ),
        pytest.param(
            105,
            0,
            0,
            id="DUP2-2",
        ),
        pytest.param(
            106,
            0,
            0,
            id="DUP3-2",
        ),
        pytest.param(
            107,
            0,
            0,
            id="DUP3-3",
        ),
        pytest.param(
            108,
            0,
            0,
            id="DUP4-3",
        ),
        pytest.param(
            109,
            0,
            0,
            id="DUP4-4",
        ),
        pytest.param(
            110,
            0,
            0,
            id="DUP5-4",
        ),
        pytest.param(
            111,
            0,
            0,
            id="DUP5-5",
        ),
        pytest.param(
            112,
            0,
            0,
            id="DUP6-5",
        ),
        pytest.param(
            113,
            0,
            0,
            id="DUP6-6",
        ),
        pytest.param(
            114,
            0,
            0,
            id="DUP7-6",
        ),
        pytest.param(
            115,
            0,
            0,
            id="DUP7-7",
        ),
        pytest.param(
            116,
            0,
            0,
            id="DUP8-7",
        ),
        pytest.param(
            117,
            0,
            0,
            id="DUP8-8",
        ),
        pytest.param(
            118,
            0,
            0,
            id="DUP9-8",
        ),
        pytest.param(
            119,
            0,
            0,
            id="DUP9-9",
        ),
        pytest.param(
            120,
            0,
            0,
            id="DUP10-9",
        ),
        pytest.param(
            121,
            0,
            0,
            id="DUP10-10",
        ),
        pytest.param(
            122,
            0,
            0,
            id="DUP11-10",
        ),
        pytest.param(
            123,
            0,
            0,
            id="DUP11-11",
        ),
        pytest.param(
            124,
            0,
            0,
            id="DUP12-11",
        ),
        pytest.param(
            125,
            0,
            0,
            id="DUP12-12",
        ),
        pytest.param(
            126,
            0,
            0,
            id="DUP13-12",
        ),
        pytest.param(
            127,
            0,
            0,
            id="DUP13-13",
        ),
        pytest.param(
            128,
            0,
            0,
            id="DUP14-13",
        ),
        pytest.param(
            129,
            0,
            0,
            id="DUP14-14",
        ),
        pytest.param(
            130,
            0,
            0,
            id="DUP15-14",
        ),
        pytest.param(
            131,
            0,
            0,
            id="DUP15-15",
        ),
        pytest.param(
            132,
            0,
            0,
            id="DUP16-15",
        ),
        pytest.param(
            133,
            0,
            0,
            id="DUP16-16",
        ),
        pytest.param(
            134,
            0,
            0,
            id="SWAP1-1",
        ),
        pytest.param(
            135,
            0,
            0,
            id="SWAP1-2",
        ),
        pytest.param(
            136,
            0,
            0,
            id="SWAP2-2",
        ),
        pytest.param(
            137,
            0,
            0,
            id="SWAP2-3",
        ),
        pytest.param(
            138,
            0,
            0,
            id="SWAP3-3",
        ),
        pytest.param(
            139,
            0,
            0,
            id="SWAP3-4",
        ),
        pytest.param(
            140,
            0,
            0,
            id="SWAP4-4",
        ),
        pytest.param(
            141,
            0,
            0,
            id="SWAP4-5",
        ),
        pytest.param(
            142,
            0,
            0,
            id="SWAP5-5",
        ),
        pytest.param(
            143,
            0,
            0,
            id="SWAP5-6",
        ),
        pytest.param(
            144,
            0,
            0,
            id="SWAP6-6",
        ),
        pytest.param(
            145,
            0,
            0,
            id="SWAP6-7",
        ),
        pytest.param(
            146,
            0,
            0,
            id="SWAP7-7",
        ),
        pytest.param(
            147,
            0,
            0,
            id="SWAP7-8",
        ),
        pytest.param(
            148,
            0,
            0,
            id="SWAP8-8",
        ),
        pytest.param(
            149,
            0,
            0,
            id="SWAP8-9",
        ),
        pytest.param(
            150,
            0,
            0,
            id="SWAP9-9",
        ),
        pytest.param(
            151,
            0,
            0,
            id="SWAP9-10",
        ),
        pytest.param(
            152,
            0,
            0,
            id="SWAP10-10",
        ),
        pytest.param(
            153,
            0,
            0,
            id="SWAP10-11",
        ),
        pytest.param(
            154,
            0,
            0,
            id="SWAP11-11",
        ),
        pytest.param(
            155,
            0,
            0,
            id="SWAP11-12",
        ),
        pytest.param(
            156,
            0,
            0,
            id="SWAP12-12",
        ),
        pytest.param(
            157,
            0,
            0,
            id="SWAP12-13",
        ),
        pytest.param(
            158,
            0,
            0,
            id="SWAP13-13",
        ),
        pytest.param(
            159,
            0,
            0,
            id="SWAP13-14",
        ),
        pytest.param(
            160,
            0,
            0,
            id="SWAP14-14",
        ),
        pytest.param(
            161,
            0,
            0,
            id="SWAP14-15",
        ),
        pytest.param(
            162,
            0,
            0,
            id="SWAP15-15",
        ),
        pytest.param(
            163,
            0,
            0,
            id="SWAP15-16",
        ),
        pytest.param(
            164,
            0,
            0,
            id="SWAP16-16",
        ),
        pytest.param(
            165,
            0,
            0,
            id="SWAP16-17",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_underflow_test(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Ori Pomerantz qbzzt1@gmail."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x40AC0FC28C27E961EE46EC43355A094DE205856EDBD4654CF2577C2608D4EC1E
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    # Source: raw
    # 0x600160015560800100
    addr_0x0000000000000000000000000000000000000101 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1) + Op.PUSH1[0x80] + Op.ADD + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x3aac251f428dcd7cb57e01c7dbb8bc3a76d5d628"),  # noqa: E501
    )
    # Source: raw
    # 0x6001600155608060800100
    addr_0x0000000000000000000000000000000000000102 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1) + Op.ADD(0x80, 0x80) + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0xcc44bebaeb76a6568aa26ae045f8516fa29b0f9c"),  # noqa: E501
    )
    # Source: raw
    # 0x600160015560800200
    addr_0x0000000000000000000000000000000000000201 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1) + Op.PUSH1[0x80] + Op.MUL + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0xe383f3e5b45fa86d5b37cdfeb146cf903641c76c"),  # noqa: E501
    )
    # Source: raw
    # 0x6001600155608060800200
    addr_0x0000000000000000000000000000000000000202 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1) + Op.MUL(0x80, 0x80) + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0xda3ec48d60f1cf78ecc154fa0c6181cf833916aa"),  # noqa: E501
    )
    # Source: raw
    # 0x600160015560800300
    addr_0x0000000000000000000000000000000000000301 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1) + Op.PUSH1[0x80] + Op.SUB + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0xb50944b674eb20b0fe99a18bb764b45500c41144"),  # noqa: E501
    )
    # Source: raw
    # 0x6001600155608060800300
    addr_0x0000000000000000000000000000000000000302 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1) + Op.SUB(0x80, 0x80) + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0xfcc0a7ebcab4f6d8c91c9062f2cd1148073253d2"),  # noqa: E501
    )
    # Source: raw
    # 0x600160015560800400
    addr_0x0000000000000000000000000000000000000401 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1) + Op.PUSH1[0x80] + Op.DIV + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0xd54c502b5478a191e9a25bc0d1ba94669c5a5f4f"),  # noqa: E501
    )
    # Source: raw
    # 0x6001600155608060800400
    addr_0x0000000000000000000000000000000000000402 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1) + Op.DIV(0x80, 0x80) + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x836d0c3ce82596908935c3cc794da4603e135b1c"),  # noqa: E501
    )
    # Source: raw
    # 0x600160015560800500
    addr_0x0000000000000000000000000000000000000501 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80]
        + Op.SDIV
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0xc131d96e30386b63f89592008939dd517579f203"),  # noqa: E501
    )
    # Source: raw
    # 0x6001600155608060800500
    addr_0x0000000000000000000000000000000000000502 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1) + Op.SDIV(0x80, 0x80) + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x58cd7cc2b1b1cd459decc8ebbbd2fcbf9c68cef9"),  # noqa: E501
    )
    # Source: raw
    # 0x600160015560800600
    addr_0x0000000000000000000000000000000000000601 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1) + Op.PUSH1[0x80] + Op.MOD + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x5df0dd6d100e8dd03d211b55d4a8cc7c7657c038"),  # noqa: E501
    )
    # Source: raw
    # 0x6001600155608060800600
    addr_0x0000000000000000000000000000000000000602 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1) + Op.MOD(0x80, 0x80) + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x4e985c32a0f53ab426fe2bcdea720f0f71a4c1d1"),  # noqa: E501
    )
    # Source: raw
    # 0x600160015560800700
    addr_0x0000000000000000000000000000000000000701 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80]
        + Op.SMOD
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x9d8ea14af8d401208eb0687b8ae6f1e5ed6808d4"),  # noqa: E501
    )
    # Source: raw
    # 0x6001600155608060800700
    addr_0x0000000000000000000000000000000000000702 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1) + Op.SMOD(0x80, 0x80) + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x18c875e7eb21e50bad81e8940a2272fd6760e0dd"),  # noqa: E501
    )
    # Source: raw
    # 0x6001600155608060800800
    addr_0x0000000000000000000000000000000000000802 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80] * 2
        + Op.ADDMOD
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0xc51017527cdd990d0c8e146ed36237694024021c"),  # noqa: E501
    )
    # Source: raw
    # 0x60016001556080608060800800
    addr_0x0000000000000000000000000000000000000803 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.ADDMOD(0x80, 0x80, 0x80)
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x23d790b6f14975963ee30ff45cc4621c7e1eeaf7"),  # noqa: E501
    )
    # Source: raw
    # 0x6001600155608060800900
    addr_0x0000000000000000000000000000000000000902 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80] * 2
        + Op.MULMOD
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x0824de5bb894849fcdd60634275d6bcb8157d4a0"),  # noqa: E501
    )
    # Source: raw
    # 0x60016001556080608060800900
    addr_0x0000000000000000000000000000000000000903 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.MULMOD(0x80, 0x80, 0x80)
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0xda24ffd288756277e556671ae2306b7587ef0c63"),  # noqa: E501
    )
    # Source: raw
    # 0x600160015560800A00
    addr_0x0000000000000000000000000000000000000a01 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1) + Op.PUSH1[0x80] + Op.EXP + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0xc36332f339266d7989b005864c48548883213125"),  # noqa: E501
    )
    # Source: raw
    # 0x6001600155608060800A00
    addr_0x0000000000000000000000000000000000000a02 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1) + Op.EXP(0x80, 0x80) + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x973b5cc7e4678bcb85618b38c910f8adc68703a6"),  # noqa: E501
    )
    # Source: raw
    # 0x600160015560800B00
    addr_0x0000000000000000000000000000000000000b01 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80]
        + Op.SIGNEXTEND
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x1e27cc27790c60dde31215bf2be1d9a66c41c8fa"),  # noqa: E501
    )
    # Source: raw
    # 0x6001600155608060800B00
    addr_0x0000000000000000000000000000000000000b02 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.SIGNEXTEND(0x80, 0x80)
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x1523b84a9fb4a0d32f070847190d34f912c04c4e"),  # noqa: E501
    )
    # Source: raw
    # 0x600160015560801000
    addr_0x0000000000000000000000000000000000001001 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1) + Op.PUSH1[0x80] + Op.LT + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x77225976113d69eee2fd870ea02d670badabdcab"),  # noqa: E501
    )
    # Source: raw
    # 0x6001600155608060801000
    addr_0x0000000000000000000000000000000000001002 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1) + Op.LT(0x80, 0x80) + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x2947a82b8aabd0f80c7e215bc066ea92bdd65b31"),  # noqa: E501
    )
    # Source: raw
    # 0x600160015560801100
    addr_0x0000000000000000000000000000000000001101 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1) + Op.PUSH1[0x80] + Op.GT + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0xf9a965915f18a6108b842a40148dc5fd47ec7140"),  # noqa: E501
    )
    # Source: raw
    # 0x6001600155608060801100
    addr_0x0000000000000000000000000000000000001102 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1) + Op.GT(0x80, 0x80) + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0xd60ab3d73fd71f071ede5eead527db298236b162"),  # noqa: E501
    )
    # Source: raw
    # 0x600160015560801200
    addr_0x0000000000000000000000000000000000001201 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1) + Op.PUSH1[0x80] + Op.SLT + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0xe519ac21322361b960bed6ccbbf538840e85f76e"),  # noqa: E501
    )
    # Source: raw
    # 0x6001600155608060801200
    addr_0x0000000000000000000000000000000000001202 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1) + Op.SLT(0x80, 0x80) + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0xc74809261edc3edd91ec17dbf4b898233c42ddb4"),  # noqa: E501
    )
    # Source: raw
    # 0x600160015560801300
    addr_0x0000000000000000000000000000000000001301 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1) + Op.PUSH1[0x80] + Op.SGT + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0xcc9ffede5b0d7f58002f852181d0b4b35c0dabee"),  # noqa: E501
    )
    # Source: raw
    # 0x6001600155608060801300
    addr_0x0000000000000000000000000000000000001302 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1) + Op.SGT(0x80, 0x80) + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x0bdf35fc6c5c2a3e1e9711112ff7ef71e2419532"),  # noqa: E501
    )
    # Source: raw
    # 0x600160015560801400
    addr_0x0000000000000000000000000000000000001401 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1) + Op.PUSH1[0x80] + Op.EQ + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x2b3bc02cabba968640fd86614f855a406b5c32e2"),  # noqa: E501
    )
    # Source: raw
    # 0x6001600155608060801400
    addr_0x0000000000000000000000000000000000001402 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1) + Op.EQ(0x80, 0x80) + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x5029d082367aa4510d5a6e3b5cf83cd41e05c7f4"),  # noqa: E501
    )
    # Source: raw
    # 0x60016001551500
    addr_0x0000000000000000000000000000000000001500 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1) + Op.ISZERO + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0xc744cf16cf5e2eb3c97e641e63801b8af3015def"),  # noqa: E501
    )
    # Source: raw
    # 0x600160015560801500
    addr_0x0000000000000000000000000000000000001501 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1) + Op.ISZERO(0x80) + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0xbe25986eb0ee281252e783918d867630e5119455"),  # noqa: E501
    )
    # Source: raw
    # 0x600160015560801600
    addr_0x0000000000000000000000000000000000001601 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1) + Op.PUSH1[0x80] + Op.AND + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x1029b338aa781a64308000fa49515769618f176e"),  # noqa: E501
    )
    # Source: raw
    # 0x6001600155608060801600
    addr_0x0000000000000000000000000000000000001602 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1) + Op.AND(0x80, 0x80) + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0xc8d2eb10090f9940b7e816e6a278ae2ec943d232"),  # noqa: E501
    )
    # Source: raw
    # 0x600160015560801700
    addr_0x0000000000000000000000000000000000001701 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1) + Op.PUSH1[0x80] + Op.OR + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x7d00c3c2cbb3b64bbb4f0f518ef779f6df875f6e"),  # noqa: E501
    )
    # Source: raw
    # 0x6001600155608060801700
    addr_0x0000000000000000000000000000000000001702 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1) + Op.OR(0x80, 0x80) + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0xe8565720ba47032e7b0edcb4bce06303f83ff450"),  # noqa: E501
    )
    # Source: raw
    # 0x600160015560801800
    addr_0x0000000000000000000000000000000000001801 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1) + Op.PUSH1[0x80] + Op.XOR + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x4c47590ab3f1dfe486900d0ec41510f85545b182"),  # noqa: E501
    )
    # Source: raw
    # 0x6001600155608060801800
    addr_0x0000000000000000000000000000000000001802 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1) + Op.XOR(0x80, 0x80) + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x9b0edd3cf5b6ccc09b3c9d15646ef629a7767ba8"),  # noqa: E501
    )
    # Source: raw
    # 0x60016001551900
    addr_0x0000000000000000000000000000000000001900 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1) + Op.NOT + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x10df9321d0355308a994d3709e30609bd72655b7"),  # noqa: E501
    )
    # Source: raw
    # 0x600160015560801900
    addr_0x0000000000000000000000000000000000001901 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1) + Op.NOT(0x80) + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0xc52f28d6433f203eae23f5f2fc642938a25aafe7"),  # noqa: E501
    )
    # Source: raw
    # 0x600160015560801A00
    addr_0x0000000000000000000000000000000000001a01 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80]
        + Op.BYTE
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x1be71f78fcfbc7e4002db615e7fc878e7f090c50"),  # noqa: E501
    )
    # Source: raw
    # 0x6001600155608060801A00
    addr_0x0000000000000000000000000000000000001a02 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1) + Op.BYTE(0x80, 0x80) + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0xf04fe60ad6f92fa14a53a0882943a66ea4e49ef1"),  # noqa: E501
    )
    # Source: raw
    # 0x600160015560801B00
    addr_0x0000000000000000000000000000000000001b01 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1) + Op.PUSH1[0x80] + Op.SHL + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0xa7b1cd72ebc0b8f3e353885ef17b04aa28d8f0fa"),  # noqa: E501
    )
    # Source: raw
    # 0x6001600155608060801B00
    addr_0x0000000000000000000000000000000000001b02 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1) + Op.SHL(0x80, 0x80) + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x701a7d6aa6ef15a38fd8311e074a96c09b434a2a"),  # noqa: E501
    )
    # Source: raw
    # 0x600160015560801C00
    addr_0x0000000000000000000000000000000000001c01 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1) + Op.PUSH1[0x80] + Op.SHR + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0xc024f0f81b1c2c1ab6362e5ecf79a7be3de2f60e"),  # noqa: E501
    )
    # Source: raw
    # 0x6001600155608060801C00
    addr_0x0000000000000000000000000000000000001c02 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1) + Op.SHR(0x80, 0x80) + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0xa49e66f497a85d949d334a20724bc6b75da3d3ae"),  # noqa: E501
    )
    # Source: raw
    # 0x600160015560801D00
    addr_0x0000000000000000000000000000000000001d01 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1) + Op.PUSH1[0x80] + Op.SAR + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0xb37c41d445866ceb36edc4e6456cae78949c9f97"),  # noqa: E501
    )
    # Source: raw
    # 0x6001600155608060801D00
    addr_0x0000000000000000000000000000000000001d02 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1) + Op.SAR(0x80, 0x80) + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x8e689eee6c7387a37612a42f8ee44dd7a823fb5c"),  # noqa: E501
    )
    # Source: raw
    # 0x600160015560802000
    addr_0x0000000000000000000000000000000000002001 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80]
        + Op.SHA3
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0xec8b92806c1ad0f2dcf5b0207db7eddb464df0ca"),  # noqa: E501
    )
    # Source: raw
    # 0x6001600155608060802000
    addr_0x0000000000000000000000000000000000002002 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.SHA3(offset=0x80, size=0x80)
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x11ffe11bb835b6ce89fc91d65b1f6c0919b07a1d"),  # noqa: E501
    )
    # Source: raw
    # 0x60016001553100
    addr_0x0000000000000000000000000000000000003100 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1) + Op.BALANCE + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x943b918e625b3ecb5d186d820a60c8eebd1c71ec"),  # noqa: E501
    )
    # Source: raw
    # 0x600160015560803100
    addr_0x0000000000000000000000000000000000003101 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.BALANCE(address=0x80)
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x58a413dde8ddd92c793fca0b18ce89bd3dfba0e8"),  # noqa: E501
    )
    # Source: raw
    # 0x60016001553500
    addr_0x0000000000000000000000000000000000003500 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1) + Op.CALLDATALOAD + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0xc24790535cfea9781d66d59b81d9b92a576bb9ef"),  # noqa: E501
    )
    # Source: raw
    # 0x600160015560803500
    addr_0x0000000000000000000000000000000000003501 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.CALLDATALOAD(offset=0x80)
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x488a9b0f0e885b96f67c113f0979799f801d70d3"),  # noqa: E501
    )
    # Source: raw
    # 0x6001600155608060803700
    addr_0x0000000000000000000000000000000000003702 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80] * 2
        + Op.CALLDATACOPY
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x59f8c0328e432df7467313742e1effc9ee2bac4e"),  # noqa: E501
    )
    # Source: raw
    # 0x60016001556080608060803700
    addr_0x0000000000000000000000000000000000003703 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.CALLDATACOPY(dest_offset=0x80, offset=0x80, size=0x80)
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0xbc57a2f2490132b8f8980cd242f7dc76b4b3f1c3"),  # noqa: E501
    )
    # Source: raw
    # 0x6001600155608060803900
    addr_0x0000000000000000000000000000000000003902 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80] * 2
        + Op.CODECOPY
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x50a33da19f003aec73bc65754e12a7f94c9b1c34"),  # noqa: E501
    )
    # Source: raw
    # 0x60016001556080608060803900
    addr_0x0000000000000000000000000000000000003903 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.CODECOPY(dest_offset=0x80, offset=0x80, size=0x80)
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x866777eaddc2be0a50b3d3f76f2064876ea42802"),  # noqa: E501
    )
    # Source: raw
    # 0x60016001553B00
    addr_0x0000000000000000000000000000000000003b00 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1) + Op.EXTCODESIZE + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x664f23c7af786dc61b6a068b3f9bde0051716384"),  # noqa: E501
    )
    # Source: raw
    # 0x600160015560803B00
    addr_0x0000000000000000000000000000000000003b01 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.EXTCODESIZE(address=0x80)
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x75a2a8afa2446ec88a716ef7074351accfaccadf"),  # noqa: E501
    )
    # Source: raw
    # 0x60016001556080608060803C00
    addr_0x0000000000000000000000000000000000003c03 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80] * 3
        + Op.EXTCODECOPY
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x93d0507f681ba7de662d14ae8de922d161698c8e"),  # noqa: E501
    )
    # Source: raw
    # 0x600160015560806080608060803C00
    addr_0x0000000000000000000000000000000000003c04 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.EXTCODECOPY(
            address=0x80, dest_offset=0x80, offset=0x80, size=0x80
        )
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0xbf337119d0b966cc500cd3ff5ab9f3c7fddaa91d"),  # noqa: E501
    )
    # Source: raw
    # 0x60016001553F00
    addr_0x0000000000000000000000000000000000003f00 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1) + Op.EXTCODEHASH + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x7142d01ed8802179659127719398fa679ac41292"),  # noqa: E501
    )
    # Source: raw
    # 0x600160015560803F00
    addr_0x0000000000000000000000000000000000003f01 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.EXTCODEHASH(address=0x80)
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0xa3d5aecbf6541cd2a0df5ae2e1294abc682180e6"),  # noqa: E501
    )
    # Source: raw
    # 0x60016001554000
    addr_0x0000000000000000000000000000000000004000 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1) + Op.BLOCKHASH + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x6f72794f9c9d8a693ff6c1134d611d353678fcf0"),  # noqa: E501
    )
    # Source: raw
    # 0x600160015560804000
    addr_0x0000000000000000000000000000000000004001 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.BLOCKHASH(block_number=0x80)
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0xb8479583829f24d888a0493a9132845b3d6a5305"),  # noqa: E501
    )
    # Source: raw
    # 0x60016001555000
    addr_0x0000000000000000000000000000000000005000 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1) + Op.POP + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x5f750bad38b37c4ebcc5fee4eed5639283a09a38"),  # noqa: E501
    )
    # Source: raw
    # 0x600160015560805000
    addr_0x0000000000000000000000000000000000005001 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1) + Op.POP(0x80) + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x14ed6c71ebccdf69007d79fe699d368102533929"),  # noqa: E501
    )
    # Source: raw
    # 0x60016001555100
    addr_0x0000000000000000000000000000000000005100 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1) + Op.MLOAD + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x92bfb1aa73e92c1f591d8b6854514df6672bbb90"),  # noqa: E501
    )
    # Source: raw
    # 0x600160015560805100
    addr_0x0000000000000000000000000000000000005101 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1) + Op.MLOAD(offset=0x80) + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0xb2e76a6fdfc66a93a2354748ec2d107a818fe73c"),  # noqa: E501
    )
    # Source: raw
    # 0x600160015560805200
    addr_0x0000000000000000000000000000000000005201 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0xec26e590a6f5da137088aee0c4d6b0f8870eb1ad"),  # noqa: E501
    )
    # Source: raw
    # 0x6001600155608060805200
    addr_0x0000000000000000000000000000000000005202 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.MSTORE(offset=0x80, value=0x80)
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0xac95d1d1c86af90f5a0cf44c104d0da04ab3a467"),  # noqa: E501
    )
    # Source: raw
    # 0x600160015560805300
    addr_0x0000000000000000000000000000000000005301 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80]
        + Op.MSTORE8
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0xa1903db9aa9aa2665ca7da383db9291d93f1d576"),  # noqa: E501
    )
    # Source: raw
    # 0x6001600155608060805300
    addr_0x0000000000000000000000000000000000005302 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.MSTORE8(offset=0x80, value=0x80)
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x891e304c4126f24bf762df079c7683420b16ff57"),  # noqa: E501
    )
    # Source: raw
    # 0x60016001555400
    addr_0x0000000000000000000000000000000000005400 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1) + Op.SLOAD + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x7aedaf23d4e9afb84baa67824cebfec01339afc1"),  # noqa: E501
    )
    # Source: raw
    # 0x600160015560805400
    addr_0x0000000000000000000000000000000000005401 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1) + Op.SLOAD(key=0x80) + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x5096db6b2ea6ace8e2aeb3610faaad183a51ca8d"),  # noqa: E501
    )
    # Source: raw
    # 0x60016001556080A000
    addr_0x000000000000000000000000000000000000a001 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80]
        + Op.LOG0
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x17f25a871ea2ea564cffe99d31dedcf1fcff0a63"),  # noqa: E501
    )
    # Source: raw
    # 0x600160015560806080A000
    addr_0x000000000000000000000000000000000000a002 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.LOG0(offset=0x80, size=0x80)
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0xfb5dbfcd64b16ab0129b99278b9d5ccfb9b605b9"),  # noqa: E501
    )
    # Source: raw
    # 0x600160015560806080A100
    addr_0x000000000000000000000000000000000000a102 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80] * 2
        + Op.LOG1
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0xc70e97b872035f925b07db55b85a3eac04e724d6"),  # noqa: E501
    )
    # Source: raw
    # 0x6001600155608060806080A100
    addr_0x000000000000000000000000000000000000a103 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.LOG1(offset=0x80, size=0x80, topic_1=0x80)
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0xd051afb76160844eb32df55e052044de76250ebc"),  # noqa: E501
    )
    # Source: raw
    # 0x6001600155608060806080A200
    addr_0x000000000000000000000000000000000000a203 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80] * 3
        + Op.LOG2
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0xdac05b6fc9dc9c0b65ecc5032f2313f7a7dd2586"),  # noqa: E501
    )
    # Source: raw
    # 0x60016001556080608060806080A200
    addr_0x000000000000000000000000000000000000a204 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.LOG2(offset=0x80, size=0x80, topic_1=0x80, topic_2=0x80)
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x3fd249e0be1d7bf6386b7dc90d92bf95f9f98bc4"),  # noqa: E501
    )
    # Source: raw
    # 0x60016001556080608060806080A300
    addr_0x000000000000000000000000000000000000a304 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80] * 4
        + Op.LOG3
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0xa7eec8574dbfc883575f2b20a80f14f335a809b6"),  # noqa: E501
    )
    # Source: raw
    # 0x600160015560806080608060806080A300
    addr_0x000000000000000000000000000000000000a305 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.LOG3(
            offset=0x80, size=0x80, topic_1=0x80, topic_2=0x80, topic_3=0x80
        )
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x22d7d32459b46a9b69542c31545cb3a0d887064c"),  # noqa: E501
    )
    # Source: raw
    # 0x600160015560806080608060806080A400
    addr_0x000000000000000000000000000000000000a405 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80] * 5
        + Op.LOG4
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x715f213243cd7baeefd3a52434353015a4fc8de2"),  # noqa: E501
    )
    # Source: raw
    # 0x6001600155608060806080608060806080A400
    addr_0x000000000000000000000000000000000000a406 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.LOG4(
            offset=0x80,
            size=0x80,
            topic_1=0x80,
            topic_2=0x80,
            topic_3=0x80,
            topic_4=0x80,
        )
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x79d8aedd70f8a99a15e3083d3335a028d69af9fa"),  # noqa: E501
    )
    # Source: raw
    # 0x600160015560806080F000
    addr_0x000000000000000000000000000000000000f002 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80] * 2
        + Op.CREATE
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x16a80f6c0bbed421a0d6b392e891a52fca715213"),  # noqa: E501
    )
    # Source: raw
    # 0x6001600155608060806080F000
    addr_0x000000000000000000000000000000000000f003 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.CREATE(value=0x80, offset=0x80, size=0x80)
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x9bd8e7c30198bd73a39e51d6866b72026272773e"),  # noqa: E501
    )
    # Source: raw
    # 0x6001600155608060806080608060806080F100
    addr_0x000000000000000000000000000000000000f106 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80] * 6
        + Op.CALL
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0xf465862e7bf5085fb692e16d3181afaba87550cc"),  # noqa: E501
    )
    # Source: raw
    # 0x60016001556080608060806080608060806080F100
    addr_0x000000000000000000000000000000000000f107 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.CALL(
            gas=0x80,
            address=0x80,
            value=0x80,
            args_offset=0x80,
            args_size=0x80,
            ret_offset=0x80,
            ret_size=0x80,
        )
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x8ce099e0d9e5e5153e578f7cbfa9fd071b714142"),  # noqa: E501
    )
    # Source: raw
    # 0x6001600155608060806080608060806080F200
    addr_0x000000000000000000000000000000000000f206 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80] * 6
        + Op.CALLCODE
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x8e3ab300e3d93ac55727c65510ff8bd96ea76928"),  # noqa: E501
    )
    # Source: raw
    # 0x60016001556080608060806080608060806080F200
    addr_0x000000000000000000000000000000000000f207 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.CALLCODE(
            gas=0x80,
            address=0x80,
            value=0x80,
            args_offset=0x80,
            args_size=0x80,
            ret_offset=0x80,
            ret_size=0x80,
        )
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0xaf6ead2e1a296b787d4b084d30b0733518fd2462"),  # noqa: E501
    )
    # Source: raw
    # 0x60016001556080F300
    addr_0x000000000000000000000000000000000000f301 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80]
        + Op.RETURN
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x84798b4fb35d09db14ecab9d65a4a280e483fe29"),  # noqa: E501
    )
    # Source: raw
    # 0x600160015560806080F300
    addr_0x000000000000000000000000000000000000f302 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.RETURN(offset=0x80, size=0x80)
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x7d002cacbe954f4360fe634fbe23f5b67c686cbf"),  # noqa: E501
    )
    # Source: raw
    # 0x600160015560806080608060806080F400
    addr_0x000000000000000000000000000000000000f405 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80] * 5
        + Op.DELEGATECALL
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x799721e570bcd85be50c0d7a399af369be561fbe"),  # noqa: E501
    )
    # Source: raw
    # 0x6001600155608060806080608060806080F400
    addr_0x000000000000000000000000000000000000f406 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.DELEGATECALL(
            gas=0x80,
            address=0x80,
            args_offset=0x80,
            args_size=0x80,
            ret_offset=0x80,
            ret_size=0x80,
        )
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x9386c3cce8cab9f8c3bc1a89c82a0e55588ced9d"),  # noqa: E501
    )
    # Source: raw
    # 0x6001600155608060806080F500
    addr_0x000000000000000000000000000000000000f503 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80] * 3
        + Op.CREATE2
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x933cb75e0e03a16aa3d3e7114d269a6fe4db46f9"),  # noqa: E501
    )
    # Source: raw
    # 0x60016001556080608060806080F500
    addr_0x000000000000000000000000000000000000f504 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.CREATE2(value=0x80, offset=0x80, size=0x80, salt=0x80)
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0xf1cfc656c8d8e2bcfdfea0e0e9cabcc0b743dd19"),  # noqa: E501
    )
    # Source: raw
    # 0x600160015560806080608060806080FA00
    addr_0x000000000000000000000000000000000000fa05 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80] * 5
        + Op.STATICCALL
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0xee8790666225df6f97ae194e20853f2907bbaebc"),  # noqa: E501
    )
    # Source: raw
    # 0x6001600155608060806080608060806080FA00
    addr_0x000000000000000000000000000000000000fa06 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.STATICCALL(
            gas=0x80,
            address=0x80,
            args_offset=0x80,
            args_size=0x80,
            ret_offset=0x80,
            ret_size=0x80,
        )
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x45952ed2c957691ae4de05032b429a8a0f0ced5b"),  # noqa: E501
    )
    # Source: raw
    # 0x60016001558000
    addr_0x0000000000000000000000000000000000008000 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1) + Op.DUP1 + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x8ceb89e3037b7ac8b58e3765ea3eb65f1a9e4a7c"),  # noqa: E501
    )
    # Source: raw
    # 0x600160015560808000
    addr_0x0000000000000000000000000000000000008001 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80]
        + Op.DUP1
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x5782c86be10d218c82d509f3257e9dfdbf6dead8"),  # noqa: E501
    )
    # Source: raw
    # 0x600160015560808100
    addr_0x0000000000000000000000000000000000008101 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80]
        + Op.DUP2
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0xe6d703c31f83bc617a62f78e3c3a615001d3dd2c"),  # noqa: E501
    )
    # Source: raw
    # 0x6001600155608060808100
    addr_0x0000000000000000000000000000000000008102 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80] * 2
        + Op.DUP2
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x113855e9aa747f6ae6fd74667d7a288b2288caf6"),  # noqa: E501
    )
    # Source: raw
    # 0x6001600155608060808200
    addr_0x0000000000000000000000000000000000008202 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80] * 2
        + Op.DUP3
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x2c2938555e004cbb0ce4481bad8a15857d983d06"),  # noqa: E501
    )
    # Source: raw
    # 0x60016001556080608060808200
    addr_0x0000000000000000000000000000000000008203 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80] * 3
        + Op.DUP3
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x63e21ad1535b95aaeed05e893b5b7947d6b0f15a"),  # noqa: E501
    )
    # Source: raw
    # 0x60016001556080608060808300
    addr_0x0000000000000000000000000000000000008303 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80] * 3
        + Op.DUP4
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x5bce589f39f0eff323bcbeac539dc9fd0f429bd2"),  # noqa: E501
    )
    # Source: raw
    # 0x600160015560806080608060808300
    addr_0x0000000000000000000000000000000000008304 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80] * 4
        + Op.DUP4
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x8030a1eb20b388143f12fb547b5e53a4c164a621"),  # noqa: E501
    )
    # Source: raw
    # 0x600160015560806080608060808400
    addr_0x0000000000000000000000000000000000008404 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80] * 4
        + Op.DUP5
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x5bb0e367bec7d734cb0fc9c27eb85af479b39673"),  # noqa: E501
    )
    # Source: raw
    # 0x6001600155608060806080608060808400
    addr_0x0000000000000000000000000000000000008405 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80] * 5
        + Op.DUP5
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0xe594a68387d42d18bb8e460cef74876f05985e3a"),  # noqa: E501
    )
    # Source: raw
    # 0x6001600155608060806080608060808500
    addr_0x0000000000000000000000000000000000008505 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80] * 5
        + Op.DUP6
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x9a90a463d916b189eee17b331f27a54142b79961"),  # noqa: E501
    )
    # Source: raw
    # 0x60016001556080608060806080608060808500
    addr_0x0000000000000000000000000000000000008506 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80] * 6
        + Op.DUP6
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x029d8125096a81237be857845270ab34afab88ac"),  # noqa: E501
    )
    # Source: raw
    # 0x60016001556080608060806080608060808600
    addr_0x0000000000000000000000000000000000008606 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80] * 6
        + Op.DUP7
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x0d423fa4896aca0a02cba41462e754c3241427f0"),  # noqa: E501
    )
    # Source: raw
    # 0x600160015560806080608060806080608060808600
    addr_0x0000000000000000000000000000000000008607 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80] * 7
        + Op.DUP7
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0xca098deb4ab81002cddbd3c93261d6d1cb5113b5"),  # noqa: E501
    )
    # Source: raw
    # 0x600160015560806080608060806080608060808700
    addr_0x0000000000000000000000000000000000008707 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80] * 7
        + Op.DUP8
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0xfbc09ac707fcca4ae8e348f01457ea18825bd139"),  # noqa: E501
    )
    # Source: raw
    # 0x6001600155608060806080608060806080608060808700
    addr_0x0000000000000000000000000000000000008708 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80] * 8
        + Op.DUP8
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x662d9872215dde44ec296918a0fd96c45c97b332"),  # noqa: E501
    )
    # Source: raw
    # 0x6001600155608060806080608060806080608060808800
    addr_0x0000000000000000000000000000000000008808 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80] * 8
        + Op.DUP9
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0xaeec863f85b9a222ac1ffff774a881d46ec3ad37"),  # noqa: E501
    )
    # Source: raw
    # 0x60016001556080608060806080608060806080608060808800
    addr_0x0000000000000000000000000000000000008809 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80] * 9
        + Op.DUP9
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x5d4fa1456fbf03872b922dc0e8e48ec49f5faf9e"),  # noqa: E501
    )
    # Source: raw
    # 0x60016001556080608060806080608060806080608060808900
    addr_0x0000000000000000000000000000000000008909 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80] * 9
        + Op.DUP10
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x4da0082f56c3cae860eb6fb0fe36bc17cfba2c27"),  # noqa: E501
    )
    # Source: raw
    # 0x600160015560806080608060806080608060806080608060808900
    addr_0x000000000000000000000000000000000000890a = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80] * 10
        + Op.DUP10
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x444a2203a30517f4a8becca90192b193a7b6ecf3"),  # noqa: E501
    )
    # Source: raw
    # 0x600160015560806080608060806080608060806080608060808a00
    addr_0x0000000000000000000000000000000000008a0a = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80] * 10
        + Op.DUP11
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0xd5765c6e58b373df78d7311fe80a67de0ddf987e"),  # noqa: E501
    )
    # Source: raw
    # 0x6001600155608060806080608060806080608060806080608060808a00
    addr_0x0000000000000000000000000000000000008a0b = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80] * 11
        + Op.DUP11
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x742bf896d715c00eb77f340fcaa65bacaee2467c"),  # noqa: E501
    )
    # Source: raw
    # 0x6001600155608060806080608060806080608060806080608060808b00
    addr_0x0000000000000000000000000000000000008b0b = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80] * 11
        + Op.DUP12
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0xc698050f674750bbcafa30c433633dee22b8a9d3"),  # noqa: E501
    )
    # Source: raw
    # 0x60016001556080608060806080608060806080608060806080608060808b00
    addr_0x0000000000000000000000000000000000008b0c = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80] * 12
        + Op.DUP12
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x6ce1b9fedca232f6829f0831ed2c23bd9c2f99a2"),  # noqa: E501
    )
    # Source: raw
    # 0x60016001556080608060806080608060806080608060806080608060808c00
    addr_0x0000000000000000000000000000000000008c0c = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80] * 12
        + Op.DUP13
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x91605658e9533e831c9f855874faa14c363dc795"),  # noqa: E501
    )
    # Source: raw
    # 0x600160015560806080608060806080608060806080608060806080608060808c00
    addr_0x0000000000000000000000000000000000008c0d = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80] * 13
        + Op.DUP13
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0xf2578fadcdd5cd7b55f7046c88a7a77e195a7b17"),  # noqa: E501
    )
    # Source: raw
    # 0x600160015560806080608060806080608060806080608060806080608060808d00
    addr_0x0000000000000000000000000000000000008d0d = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80] * 13
        + Op.DUP14
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x34fb465a898787f7ed08bc2f5de86a896f8bc4da"),  # noqa: E501
    )
    # Source: raw
    # 0x6001600155608060806080608060806080608060806080608060806080608060808d00
    addr_0x0000000000000000000000000000000000008d0e = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80] * 14
        + Op.DUP14
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0xf84f405591be4ab47ca2ca1841dcb57cc43f076f"),  # noqa: E501
    )
    # Source: raw
    # 0x6001600155608060806080608060806080608060806080608060806080608060808e00
    addr_0x0000000000000000000000000000000000008e0e = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80] * 14
        + Op.DUP15
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x2cd79f853ec648b7c3ec3fac7c7ce82d7d83ea1e"),  # noqa: E501
    )
    # Source: raw
    # 0x60016001556080608060806080608060806080608060806080608060806080608060808e00  # noqa: E501
    addr_0x0000000000000000000000000000000000008e0f = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80] * 15
        + Op.DUP15
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x0cd1b3e02e0bc556b0c7d4779c69a9a383c0c7cd"),  # noqa: E501
    )
    # Source: raw
    # 0x60016001556080608060806080608060806080608060806080608060806080608060808f00  # noqa: E501
    addr_0x0000000000000000000000000000000000008f0f = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80] * 15
        + Op.DUP16
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x175de68007e136237a4f26b6983dbce27a87fb5b"),  # noqa: E501
    )
    # Source: raw
    # 0x600160015560806080608060806080608060806080608060806080608060806080608060808f00  # noqa: E501
    addr_0x0000000000000000000000000000000000008f10 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80] * 16
        + Op.DUP16
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x9c8fc002a1dcd0edcf93c20dc9d674031dc5a28d"),  # noqa: E501
    )
    # Source: raw
    # 0x600160015560809000
    addr_0x0000000000000000000000000000000000009001 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80]
        + Op.SWAP1
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x8b62b65db3bd1be727290b490c679c0e84585498"),  # noqa: E501
    )
    # Source: raw
    # 0x6001600155608060809000
    addr_0x0000000000000000000000000000000000009002 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80] * 2
        + Op.SWAP1
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x6c6bc4f9ccde5da559a3e5dddb6b60a8675c0076"),  # noqa: E501
    )
    # Source: raw
    # 0x6001600155608060809100
    addr_0x0000000000000000000000000000000000009102 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80] * 2
        + Op.SWAP2
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0xe98c1ab0ff23d5c5005c639781d1a635b9af887b"),  # noqa: E501
    )
    # Source: raw
    # 0x60016001556080608060809100
    addr_0x0000000000000000000000000000000000009103 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80] * 3
        + Op.SWAP2
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0xacda51eb0d678a0d52bfa44e4354d8f371f43438"),  # noqa: E501
    )
    # Source: raw
    # 0x60016001556080608060809200
    addr_0x0000000000000000000000000000000000009203 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80] * 3
        + Op.SWAP3
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x9768a9bb367830f3331b0c09d7183c131e44a7fc"),  # noqa: E501
    )
    # Source: raw
    # 0x600160015560806080608060809200
    addr_0x0000000000000000000000000000000000009204 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80] * 4
        + Op.SWAP3
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0xd6bb0ea7c7f60c967d3deeeaaba555daafbc52cb"),  # noqa: E501
    )
    # Source: raw
    # 0x600160015560806080608060809300
    addr_0x0000000000000000000000000000000000009304 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80] * 4
        + Op.SWAP4
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x19598106d1cede298b275523e64593c95d5c431c"),  # noqa: E501
    )
    # Source: raw
    # 0x6001600155608060806080608060809300
    addr_0x0000000000000000000000000000000000009305 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80] * 5
        + Op.SWAP4
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0xb44c7350f24bb5482057b53911a1d3c91c263eaf"),  # noqa: E501
    )
    # Source: raw
    # 0x6001600155608060806080608060809400
    addr_0x0000000000000000000000000000000000009405 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80] * 5
        + Op.SWAP5
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x0d0e14670e6e8718377bc2fae6b6814d558d3dee"),  # noqa: E501
    )
    # Source: raw
    # 0x60016001556080608060806080608060809400
    addr_0x0000000000000000000000000000000000009406 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80] * 6
        + Op.SWAP5
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0xa15fe2669809ddc6640e94572907a53411b2aa6e"),  # noqa: E501
    )
    # Source: raw
    # 0x60016001556080608060806080608060809500
    addr_0x0000000000000000000000000000000000009506 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80] * 6
        + Op.SWAP6
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0xd435f13e92f7db306b9b32e1d61db6ecd9c135bd"),  # noqa: E501
    )
    # Source: raw
    # 0x600160015560806080608060806080608060809500
    addr_0x0000000000000000000000000000000000009507 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80] * 7
        + Op.SWAP6
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0xc3fce336558080ef8b1a20a209b173e6d163e548"),  # noqa: E501
    )
    # Source: raw
    # 0x600160015560806080608060806080608060809600
    addr_0x0000000000000000000000000000000000009607 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80] * 7
        + Op.SWAP7
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x620d85c5acc41cbfa47a763bbb9e326054b1819d"),  # noqa: E501
    )
    # Source: raw
    # 0x6001600155608060806080608060806080608060809600
    addr_0x0000000000000000000000000000000000009608 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80] * 8
        + Op.SWAP7
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x9b9d04770c429114574c11780fc9658d3257e80b"),  # noqa: E501
    )
    # Source: raw
    # 0x6001600155608060806080608060806080608060809700
    addr_0x0000000000000000000000000000000000009708 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80] * 8
        + Op.SWAP8
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x44c420a5b1a9071eb7ff6f1027c167c002c7f355"),  # noqa: E501
    )
    # Source: raw
    # 0x60016001556080608060806080608060806080608060809700
    addr_0x0000000000000000000000000000000000009709 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80] * 9
        + Op.SWAP8
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0xdcb6a7c9b64471effdd8bbf72d32d271deeec8c5"),  # noqa: E501
    )
    # Source: raw
    # 0x60016001556080608060806080608060806080608060809800
    addr_0x0000000000000000000000000000000000009809 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80] * 9
        + Op.SWAP9
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x3ad6053af54d703f7e7229bd5bf120c908c8513d"),  # noqa: E501
    )
    # Source: raw
    # 0x600160015560806080608060806080608060806080608060809800
    addr_0x000000000000000000000000000000000000980a = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80] * 10
        + Op.SWAP9
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0xd9292de838cd8839d91b496d8a9d25ac102cd821"),  # noqa: E501
    )
    # Source: raw
    # 0x600160015560806080608060806080608060806080608060809900
    addr_0x000000000000000000000000000000000000990a = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80] * 10
        + Op.SWAP10
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x2ac63027195da2ee9ce4cc1dff225ca97d3c2f0c"),  # noqa: E501
    )
    # Source: raw
    # 0x6001600155608060806080608060806080608060806080608060809900
    addr_0x000000000000000000000000000000000000990b = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80] * 11
        + Op.SWAP10
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x723a69480f074f5df2544cacf63347fb5f0f36d1"),  # noqa: E501
    )
    # Source: raw
    # 0x6001600155608060806080608060806080608060806080608060809a00
    addr_0x0000000000000000000000000000000000009a0b = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80] * 11
        + Op.SWAP11
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x73f7599a216d98d9ff1559788a9771d78895a6a3"),  # noqa: E501
    )
    # Source: raw
    # 0x60016001556080608060806080608060806080608060806080608060809a00
    addr_0x0000000000000000000000000000000000009a0c = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80] * 12
        + Op.SWAP11
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x4289634ebf793179377faa7140610bb80db21b45"),  # noqa: E501
    )
    # Source: raw
    # 0x60016001556080608060806080608060806080608060806080608060809b00
    addr_0x0000000000000000000000000000000000009b0c = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80] * 12
        + Op.SWAP12
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x66a62a0af37886b9b057a1bad714665525e7687f"),  # noqa: E501
    )
    # Source: raw
    # 0x600160015560806080608060806080608060806080608060806080608060809b00
    addr_0x0000000000000000000000000000000000009b0d = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80] * 13
        + Op.SWAP12
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x1bb096578fe2f1be79e03ea88551a8bdd0692bea"),  # noqa: E501
    )
    # Source: raw
    # 0x600160015560806080608060806080608060806080608060806080608060809c00
    addr_0x0000000000000000000000000000000000009c0d = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80] * 13
        + Op.SWAP13
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x745a759f45602915eab7bdc87bc8d1c1675d4e29"),  # noqa: E501
    )
    # Source: raw
    # 0x6001600155608060806080608060806080608060806080608060806080608060809c00
    addr_0x0000000000000000000000000000000000009c0e = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80] * 14
        + Op.SWAP13
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0xbf99ad09fc2f72924cbe6da6020f985e65f78901"),  # noqa: E501
    )
    # Source: raw
    # 0x6001600155608060806080608060806080608060806080608060806080608060809d00
    addr_0x0000000000000000000000000000000000009d0e = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80] * 14
        + Op.SWAP14
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x727fd27941dbe4d8f1e2e9daa0df70288fd73772"),  # noqa: E501
    )
    # Source: raw
    # 0x60016001556080608060806080608060806080608060806080608060806080608060809d00  # noqa: E501
    addr_0x0000000000000000000000000000000000009d0f = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80] * 15
        + Op.SWAP14
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x1eb3790937f47fe31a45f55bd82f50107e7a463a"),  # noqa: E501
    )
    # Source: raw
    # 0x60016001556080608060806080608060806080608060806080608060806080608060809e00  # noqa: E501
    addr_0x0000000000000000000000000000000000009e0f = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80] * 15
        + Op.SWAP15
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0xcd63f547ee166a3feb23a945f488ccc5ee921eef"),  # noqa: E501
    )
    # Source: raw
    # 0x600160015560806080608060806080608060806080608060806080608060806080608060809e00  # noqa: E501
    addr_0x0000000000000000000000000000000000009e10 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80] * 16
        + Op.SWAP15
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x8fd69485a26470a721f6dd7e685da39ee2a3dc1c"),  # noqa: E501
    )
    # Source: raw
    # 0x600160015560806080608060806080608060806080608060806080608060806080608060809f00  # noqa: E501
    addr_0x0000000000000000000000000000000000009f10 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80] * 16
        + Op.SWAP16
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x6f631ae51ead55c8526aff13665fe5dd055e3561"),  # noqa: E501
    )
    # Source: raw
    # 0x6001600155608060806080608060806080608060806080608060806080608060806080608060809f00  # noqa: E501
    addr_0x0000000000000000000000000000000000009f11 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x80] * 17
        + Op.SWAP16
        + Op.STOP,
        storage={1: 24743},
        nonce=0,
        address=Address("0x1debd2afba875db8938ce64218b40fb210e1de0a"),  # noqa: E501
    )
    # Source: lll
    # {
    #     [[0]] 0x60A7
    #     (call (gas) $4 0 0 0 0 0)
    #     [[1]] 0x60A7
    # }
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x60A7)
        + Op.POP(
            Op.CALL(
                gas=Op.GAS,
                address=Op.CALLDATALOAD(offset=0x4),
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.SSTORE(key=0x1, value=0x60A7)
        + Op.STOP,
        nonce=0,
        address=Address("0x4c5f839d523e76fc3837e085a3e1538cd36e288a"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xBA1A9CE0BA1A9CE)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": [0], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000000101: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [1], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000000102: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [2], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000000201: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [3], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000000202: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [4], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000000301: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [5], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000000302: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [6], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000000401: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [7], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000000402: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [8], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000000501: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [9], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000000502: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [10], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000000601: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [11], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000000602: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [12], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000000701: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [13], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000000702: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [14], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000000802: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [15], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000000803: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [16], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000000902: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [17], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000000903: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [18], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000000a01: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [19], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000000a02: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [20], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000000b01: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [21], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000000b02: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [22], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000001001: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [23], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000001002: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [24], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000001101: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [25], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000001102: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [26], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000001201: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [27], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000001202: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [28], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000001301: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [29], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000001302: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [30], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000001401: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [31], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000001402: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [32], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000001500: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [33], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000001501: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [34], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000001601: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [35], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000001602: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [36], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000001701: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [37], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000001702: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [38], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000001801: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [39], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000001802: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [40], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000001900: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [41], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000001901: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [42], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000001a01: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [43], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000001a02: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [44], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000001b01: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [45], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000001b02: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [46], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000001c01: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [47], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000001c02: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [48], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000001d01: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [49], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000001d02: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [50], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000002001: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [51], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000002002: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [52], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000003100: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [53], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000003101: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [54], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000003500: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [55], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000003501: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [56], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000003702: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [57], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000003703: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [58], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000003902: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [59], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000003903: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [60], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000003b00: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [61], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000003b01: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [62], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000003c03: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [63], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000003c04: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [64], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000003f00: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [65], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000003f01: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [66], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000004000: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [67], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000004001: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [68], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000005000: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [69], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000005001: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [70], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000005100: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [71], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000005101: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [72], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000005201: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [73], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000005202: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [74], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000005301: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [75], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000005302: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [76], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000005400: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [77], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000005401: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [78], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x000000000000000000000000000000000000a001: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [79], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x000000000000000000000000000000000000a002: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [80], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x000000000000000000000000000000000000a102: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [81], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x000000000000000000000000000000000000a103: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [82], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x000000000000000000000000000000000000a203: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [83], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x000000000000000000000000000000000000a204: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [84], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x000000000000000000000000000000000000a304: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [85], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x000000000000000000000000000000000000a305: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [86], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x000000000000000000000000000000000000a405: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [87], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x000000000000000000000000000000000000a406: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [88], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x000000000000000000000000000000000000f002: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [89], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x000000000000000000000000000000000000f003: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [90], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x000000000000000000000000000000000000f106: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [91], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x000000000000000000000000000000000000f107: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [92], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x000000000000000000000000000000000000f206: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [93], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x000000000000000000000000000000000000f207: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [94], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x000000000000000000000000000000000000f301: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [95], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x000000000000000000000000000000000000f302: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [96], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x000000000000000000000000000000000000f405: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [97], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x000000000000000000000000000000000000f406: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [98], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x000000000000000000000000000000000000f503: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [99], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x000000000000000000000000000000000000f504: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [100], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x000000000000000000000000000000000000fa05: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [101], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x000000000000000000000000000000000000fa06: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [102], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000008000: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [103], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000008001: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [104], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000008101: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [105], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000008102: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [106], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000008202: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [107], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000008203: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [108], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000008303: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [109], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000008304: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [110], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000008404: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [111], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000008405: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [112], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000008505: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [113], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000008506: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [114], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000008606: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [115], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000008607: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [116], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000008707: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [117], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000008708: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [118], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000008808: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [119], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000008809: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [120], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000008909: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [121], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x000000000000000000000000000000000000890a: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [122], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000008a0a: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [123], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000008a0b: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [124], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000008b0b: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [125], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000008b0c: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [126], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000008c0c: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [127], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000008c0d: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [128], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000008d0d: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [129], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000008d0e: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [130], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000008e0e: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [131], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000008e0f: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [132], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000008f0f: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [133], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000008f10: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [134], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000009001: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [135], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000009002: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [136], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000009102: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [137], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000009103: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [138], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000009203: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [139], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000009204: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [140], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000009304: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [141], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000009305: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [142], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000009405: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [143], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000009406: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [144], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000009506: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [145], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000009507: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [146], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000009607: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [147], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000009608: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [148], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000009708: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [149], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000009709: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [150], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000009809: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [151], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x000000000000000000000000000000000000980a: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [152], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x000000000000000000000000000000000000990a: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [153], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x000000000000000000000000000000000000990b: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [154], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000009a0b: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [155], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000009a0c: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [156], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000009b0c: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [157], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000009b0d: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [158], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000009c0d: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [159], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000009c0e: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [160], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000009d0e: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [161], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000009d0f: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [162], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000009e0f: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [163], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000009e10: Account(
                    storage={1: 1}
                ),
            },
        },
        {
            "indexes": {"data": [164], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000009f10: Account(
                    storage={1: 24743}
                ),
            },
        },
        {
            "indexes": {"data": [165], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 24743, 1: 24743}),
                addr_0x0000000000000000000000000000000000009f11: Account(
                    storage={1: 1}
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=target,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        value=TX_VALUE[v],
        nonce=0,
        gas_price=10,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
