"""
A random test that had failed in Python ethereum implementation

Ported from:
tests/static/state_tests/stRevertTest/PythonRevertTestTue201814-1430Filler.json

callee code:
    push27 0xbee2a270429abbd3ff3b9945f72f58dcf4f8b344417a87dfa1ebd7
    push1 0x1f
    mstore
    origin
    push1 0x9b
    push2 0x03ee
    push2 0x027b
    push2 0x0132
    push4 0x42a46f50
    push20 0x69859649e8a52de717592b881508371f8a8ed6b9
    push4 0x2c1e2816
    callcode
    push2 0x0172
    push2 0x01ec
    push2 0x0131
    push2 0x0124
    push20 0x843e0b83d4d70dede90d9a4d93fa3f10bb5011c7
    push4 0x2318d76f
    staticcall
    push19 0x01a0ff381bb40bb828d7781d2ef7c0fd8695f7
    ... (102 more instructions)

contract code:
    push2 0x02fa
    push1 0xff
    push1 0xf5
    push2 0x0148
    push20 0xf7b2e80637a148b5e46945e29388928dafd5aa25
    push4 0x0277795a
    staticcall
    push9 0x9497edb6a665eae52f
    returndatasize
    push3 0x524975
    push2 0x03a5
    mstore
    push1 0xa8
    push1 0xfb
    push1 0xcb
    returndatacopy
    push2 0x02dd
    push2 0x03e0
    revert
    push16 0x568a159c0cae9044d258c55b10f4d100
    ... (116 more instructions)

callee_1 code:
    push1 0x13
    push2 0x019f
    push2 0x0101
    returndatacopy
    push16 0x338db2b1165b4918f178852663192a95
    push14 0x79a68b50eefdc639ca0b62ab4d52
    push24 0x1db054ccc801c0666b34b3c6242bbfc5e98f20c14fb95e01
    push8 0x18be9ad033d50e21
    push8 0x5ff59297861847ea
    push11 0x911a6a9d135e2f826dc603
    push30 0x850e0db21d105b8732a34b873c7d943050b8659794f0bd3e841d35a2231e
    push6 0xf697f8cde117
    push8 0x28fa2051e87933cf
    push7 0x858e4e5e91baa7
    push23 0x4fc1e9ffe4c7b15ba600e88f095989dc68f47ed704be2b
    swap10
    push1 0x17
    push2 0x0215
    push4 0x200fbd63
    create
    ... (59 more instructions)
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
    ["tests/static/state_tests/stRevertTest/PythonRevertTestTue201814-1430Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_python_revert_test_tue201814_1430(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """A random test that had failed in Python ethereum implementation."""
    coinbase = Address("0xf7b2e80637a148b5e46945e29388928dafd5aa25")
    sender = Address("0x80fb51c1799682acdc5353bd0f344a74c81209b9")
    contract = Address("0x843e0b83d4d70dede90d9a4d93fa3f10bb5011c7")
    callee = Address("0x69859649e8a52de717592b881508371f8a8ed6b9")
    callee_1 = Address("0xe7e620c9cf6045209edcad4d6ef43413bedf0949")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=5805800386153628,
    )

    pre[callee] = Account(
        balance=0x882fd85bc18c9f00,
        nonce=29,
        code=(
        Op.PUSH27[0xbee2a270429abbd3ff3b9945f72f58dcf4f8b344417a87dfa1ebd7]
        + Op.PUSH1[0x1f] + Op.MSTORE + Op.ORIGIN + Op.PUSH1[0x9b] + Op.PUSH2[0x3ee]
        + Op.PUSH2[0x27b] + Op.PUSH2[0x132] + Op.PUSH4[0x42a46f50]
        + Op.PUSH20[0x69859649e8a52de717592b881508371f8a8ed6b9] + Op.PUSH4[0x2c1e2816]
        + Op.CALLCODE + Op.PUSH2[0x172] + Op.PUSH2[0x1ec] + Op.PUSH2[0x131]
        + Op.PUSH2[0x124] + Op.PUSH20[0x843e0b83d4d70dede90d9a4d93fa3f10bb5011c7]
        + Op.PUSH4[0x2318d76f] + Op.STATICCALL
        + Op.PUSH19[0x1a0ff381bb40bb828d7781d2ef7c0fd8695f7]
        + Op.PUSH29[0x5465fbadf99fdffef2afd94b0e76531b6ea0d23d2332d13c20368a072]
        + Op.PUSH5[0x4e41bc1130]
        + Op.PUSH26[0xa6b1ebc3464527e34c26a4379f9dfe4f8e57981a9fc08558c90d]
        + Op.MSTORE8 + Op.PUSH22[0x38079f1921b60fe6fa448171fec55c4c63e811712211]
        + Op.PUSH5[0xcf72f489a4] + Op.JUMPI
        + Op.PUSH22[0xe83a2f5427eab647b075a910929de0a6554fc1426b49] + Op.SLOAD
        + Op.PUSH27[0xcd8e2c770339616ce9c501fb746715dd4a20219229d0673ac05599]
        + Op.PUSH31[0x3bd089a6663f6dff488574195b848fbb357eb7be1fff076e997770d03b7028]
        + Op.MSTORE8 + Op.PUSH2[0x3b3] + Op.PUSH2[0x284] + Op.PUSH2[0x305]
        + Op.PUSH2[0x2db] + Op.PUSH20[0x69859649e8a52de717592b881508371f8a8ed6b9]
        + Op.PUSH4[0x47cfe65d] + Op.DELEGATECALL + Op.TIMESTAMP + Op.GASPRICE
        + Op.PUSH12[0x8679871dc28aa5a1399b21c8] + Op.PUSH2[0x2e4] + Op.PUSH1[0x47]
        + Op.PUSH2[0x1f3] + Op.PUSH1[0x5b]
        + Op.PUSH20[0xffffffffffffffffffffffffffffffffffffffff] + Op.PUSH4[0x11ecd01b]
        + Op.STATICCALL + Op.PUSH23[0xafa8155ecd75dd05f9d7eb42fa3e79c6a2109dff2a1e53]
        + Op.PUSH2[0x30a] + Op.PUSH2[0x1b2] + Op.REVERT + Op.PUSH2[0x263]
        + Op.PUSH1[0x58] + Op.PUSH2[0x117] + Op.PUSH2[0x27f] + Op.PUSH4[0x459d135b]
        + Op.PUSH20[0x5] + Op.PUSH4[0x42ce224d] + Op.CALLCODE
        + Op.PUSH21[0xe612fbe000bed18eec8345f005f537c72820d8b973] + Op.PUSH1[0xe3]
        + Op.MSTORE + Op.PUSH12[0x50ae523a8f7467ae14a8bd9a]
        + Op.PUSH11[0xaee55862b685e32476cc67] + Op.PUSH3[0xae2c40]
        + Op.PUSH9[0xcf55729540d111f44c] + Op.SWAP3 + Op.PUSH1[0xe7] + Op.PUSH2[0x1bc]
        + Op.PUSH2[0x3f3] + Op.RETURNDATACOPY + Op.PUSH9[0x639458dae7ad2a9b38]
        + Op.PUSH3[0x9ed3bb] + Op.LT + Op.PUSH1[0xd8] + Op.PUSH2[0x36a] + Op.REVERT
        + Op.PUSH2[0x123] + Op.PUSH2[0x359] + Op.PUSH4[0x6db4b55b] + Op.CREATE
        + Op.PUSH3[0x602169] + Op.PUSH2[0x177] + Op.MSTORE + Op.PUSH4[0xea8a7b3a]
        + Op.PUSH5[0x1bcf921919] + Op.BYTE + Op.PUSH2[0x3be] + Op.PUSH2[0x371]
        + Op.PUSH2[0x1f7] + Op.RETURNDATACOPY
        + Op.PUSH21[0xc0413cb5d609ca9a51645238e4f1f8268f973c3a01]
        + Op.PUSH10[0xa0b67479a345d1e70065] + Op.MSTORE8 + Op.PUSH1[0x16]
        + Op.PUSH2[0x173] + Op.PUSH2[0x2f2] + Op.PUSH2[0x214] + Op.PUSH4[0x3ff89b31]
        + Op.PUSH20[0x6] + Op.PUSH4[0x35adeabd] + Op.CALL + Op.RETURNDATASIZE
        + Op.PUSH31[0xe6d218af54c3d8045447d06c726801695cfa26fdfaa6460a8685cd662855a5]
        + Op.SLOAD
        + Op.PUSH32[0x5716140ae0b1e25aeaf04ae7cf54e8aa7a22206da5a6e52bdd3ef82ad40a4681]
        + Op.MLOAD + Op.PUSH24[0xd25811167b0a3f66a727652592924dc1291a6085d537c5da]
        + Op.PUSH2[0x1b1] + Op.PUSH1[0x1d] + Op.PUSH2[0x3a3] + Op.RETURNDATACOPY
        + Op.PUSH22[0x2d6272a54f882460bc76407d6361c40cc56bc88a8bc9] + Op.PUSH1[0x72]
        + Op.PUSH2[0x3ec] + Op.PUSH2[0x2c1] + Op.PUSH2[0x1f3]
        + Op.PUSH20[0xe7e620c9cf6045209edcad4d6ef43413bedf0949] + Op.PUSH4[0x5f449586]
        + Op.DELEGATECALL
    ),
    )
    pre[sender] = Account(balance=0xab56295c9d120548, nonce=0)
    pre[contract] = Account(
        balance=0x845252b8509dc215,
        nonce=29,
        code=(
        Op.PUSH2[0x2fa] + Op.PUSH1[0xff] + Op.PUSH1[0xf5] + Op.PUSH2[0x148]
        + Op.PUSH20[0xf7b2e80637a148b5e46945e29388928dafd5aa25] + Op.PUSH4[0x277795a]
        + Op.STATICCALL + Op.PUSH9[0x9497edb6a665eae52f] + Op.RETURNDATASIZE
        + Op.PUSH3[0x524975] + Op.PUSH2[0x3a5] + Op.MSTORE + Op.PUSH1[0xa8]
        + Op.PUSH1[0xfb] + Op.PUSH1[0xcb] + Op.RETURNDATACOPY + Op.PUSH2[0x2dd]
        + Op.PUSH2[0x3e0] + Op.REVERT + Op.PUSH16[0x568a159c0cae9044d258c55b10f4d100]
        + Op.PUSH3[0x8d29ab]
        + Op.PUSH25[0x1df7fcebb789e2a8cdbaa9c67c42cd1ebe81716ead0e94c721]
        + Op.PUSH14[0x279dd3a0b3de311596d547292878]
        + Op.PUSH20[0x449ccce511e6991b3dc636a178159a3d9a062274] + Op.PUSH3[0xcd9a67]
        + Op.PUSH9[0xccba17c2cb06de468e] + Op.SWAP6
        + Op.PUSH20[0xbf78e55af17e19973f2c3f5d4c21c169890b9a9]
        + Op.PUSH8[0x2491f91aa1e71426] + Op.PUSH8[0x60d385ed594e21b]
        + Op.PUSH14[0x2b23a6c4c50e7ab6a3ef66f83a2] + Op.SWAP3
        + Op.PUSH32[0x9845b4ba85c4fdfbd0054a0123ad93eff4b525b0f4b08d285f36f3bcac6a985b]
        + Op.PUSH7[0x906c348472b7cb] + Op.DIV
        + Op.PUSH28[0xc5a02e618666f0c50eecdc11f20fc1dc41c2fd957752e55ede4e56f4]
        + Op.PUSH10[0xf536a04d436ad418a1ca]
        + Op.PUSH27[0x44c0173c10f1806ba284f9c9c7c13670005de594dec538cd56c274]
        + Op.PUSH12[0x3bfdfa7683ae0df68bbcb534]
        + Op.PUSH30[0x61be606ef617322e6448e3e4124dbe061257a8f486529de397f08ce92502]
        + Op.LOG3
        + Op.PUSH28[0x957f855818082b5b5b49e36de5a83e8a270663088571bf2fdf8f5f29]
        + Op.PUSH2[0x314] + Op.MSTORE + Op.ORIGIN
        + Op.PUSH16[0xb9499741e3859928a237f5e5df84c13c] + Op.PUSH1[0x43] + Op.SSTORE
        + Op.PUSH12[0x1e82328f9093e64defbdd07d]
        + Op.PUSH24[0x74d84835800999791abc41260472d96f604d07198e859adc]
        + Op.SIGNEXTEND + Op.PUSH17[0x806beae7200cf116d2b55e89ddd564abc3]
        + Op.PUSH14[0x900e69a68b0f0e9e4f1299872881] + Op.MSTORE8 + Op.PUSH1[0x5d]
        + Op.PUSH30[0x1c42f3b109ed2bd72a6cf13500241c2a5e5c4e17ea9ed9b05ba9b57d70d]
        + Op.PUSH4[0xd270ece7]
        + Op.PUSH32[0x6ecf21d3a41ad554f79584dcab761d4c8437774cad4bb13b2bece140358df93e]
        + Op.PUSH23[0xc0f49abe102cd44e474ab71c0237247865fa2add74c8b2] + Op.LOG3
        + Op.RETURNDATASIZE + Op.PUSH16[0x7041c5718a2554a72662720296dff5b3]
        + Op.PUSH24[0xb559df4558b8a5b2c9e7d15eb3947a70064f935c8fdf0a4e]
        + Op.PUSH19[0x6f644aa31b42c10280e50ea92a366c3d060c12]
        + Op.PUSH17[0xc6a16a75522fbeb3d7cca702807f521781]
        + Op.PUSH15[0xab9cceb9e237ee8fde4ed3a23d3ec8]
        + Op.PUSH27[0xdb334ac1caa7e06523b0132dd615cf3fc16140d34c191617823c3a]
        + Op.PUSH28[0xf47c42bc36b69cb4385463595c7f6f9ea451e05303603e0cd401e13d]
        + Op.PUSH16[0xf744e2a673824d943941551704ff14df]
        + Op.PUSH32[0xa8646efbb2d8abc4ac6e258e9924924b8001f8f0650d66b37411d484b18f41e7]
        + Op.PUSH29[0x792bd1c169fa52bbfc8af4a45f20acb0ef95db2ecbc0d4eadbbbf6732f]
        + Op.PUSH5[0x8bd33b3633] + Op.PUSH14[0xc0faf0cf1970bcd38093a50a44fd]
        + Op.PUSH12[0x253b0e74f2706239c499217b] + Op.DUP13 + Op.ORIGIN
        + Op.PUSH4[0xdae332e2] + Op.SLOAD
        + Op.PUSH18[0x1d5d5e7e795c998cceed14cf46977e7d3cbb] + Op.CALLDATALOAD
        + Op.PUSH25[0x3c79ef0530c3a8ac3fd8d49f10bb0ae919fa149adead67dae0]
        + Op.CALLDATALOAD + Op.PUSH3[0x7de430] + Op.PUSH3[0x2813ac]
        + Op.PUSH3[0x71b518] + Op.PUSH20[0x69859649e8a52de717592b881508371f8a8ed6b9]
        + Op.EXTCODECOPY
        + Op.PUSH32[0xb9ba628e056e0e87e029b8e5f42821d775338e6774301ecb428b3938236ee22b]
        + Op.PUSH30[0xb5edf2ad6997869f427ba0672a7168614233e85f61dae5ed4283a53f605]
        + Op.PUSH17[0x116dad586dce62833a62ca8c914c641f86] + Op.PUSH1[0x52]
        + Op.PUSH2[0x1d7] + Op.PUSH2[0x107] + Op.PUSH2[0x31c]
        + Op.PUSH20[0xf7b2e80637a148b5e46945e29388928dafd5aa25] + Op.PUSH4[0x33d3d55f]
        + Op.DELEGATECALL + Op.PUSH2[0x1a5b] + Op.PUSH4[0x1c4ea729] + Op.DUP2
        + Op.PUSH2[0x256] + Op.PUSH2[0x3ce] + Op.PUSH2[0x1c1] + Op.PUSH2[0x14a]
        + Op.PUSH20[0x6] + Op.PUSH4[0x202b2ea8] + Op.DELEGATECALL + Op.PUSH2[0x221]
        + Op.PUSH2[0x106] + Op.PUSH1[0x2e] + Op.RETURNDATACOPY
        + Op.PUSH5[0x8a95029ecb] + Op.PUSH19[0x849fe0943cb9d854c7d50ad04cfdfe648e2868]
        + Op.PUSH23[0xb8f2b53e55fe01a152c8496cbcc6997447062b734cebde] + Op.DIV
        + Op.PUSH26[0x6c6452e9efc4aba5bf071cbff56208a525a8ef5f52399b4f3369]
        + Op.PUSH28[0xd988884f58166d734881774eff46d77bb189c89c55b1c6591f178d2d]
        + Op.PUSH29[0x21bf2b023adf9bc5b8621235e3346d98d56047a3f71241fd5a24abbb0c]
        + Op.PUSH20[0xfc463fb8a5e67e32055696fe51258dd07526ebd8]
        + Op.PUSH31[0x439bcebb514ae26dc12d653a5c1263705109097ec5dcdb3918ab114985f709]
        + Op.PUSH32[0xd3003b50e58fba91007825a6b800f644eaa306051808460fc3b2d8e276b2187c]
        + Op.PUSH28[0x583ff29ee0b0c34f9ee57bac9ebb996402e3300ddf06c760fc5f531f]
        + Op.PUSH21[0x6b1e2beda7a15c07f90f92422822e8d33c5d2409ea]
        + Op.PUSH20[0x75197f7cd6d61770eddb078206cfc7c5006cd0e9]
        + Op.PUSH30[0xa9ec65fa4fc683da22cfaf6dfc995feb5f8386a052851fc502f32e7ef934]
        + Op.PUSH15[0x3d4633def4c0a4b9be12f2cd7c6460] + Op.PUSH3[0xe14ca3]
        + Op.PUSH29[0xfb977524f677714c3d994ea05f1997a2462fc0ab20ed2a5958f3712602]
        + Op.SWAP12 + Op.PUSH2[0x205] + Op.PUSH2[0x2c9] + Op.PUSH1[0x5d]
        + Op.PUSH2[0x3a1] + Op.PUSH20[0x69859649e8a52de717592b881508371f8a8ed6b9]
        + Op.PUSH4[0x2e83dbe] + Op.DELEGATECALL
    ),
    )
    pre[callee_1] = Account(
        balance=0x5b1936a53e6e440f,
        nonce=21,
        code=(
        Op.PUSH1[0x13] + Op.PUSH2[0x19f] + Op.PUSH2[0x101] + Op.RETURNDATACOPY
        + Op.PUSH16[0x338db2b1165b4918f178852663192a95]
        + Op.PUSH14[0x79a68b50eefdc639ca0b62ab4d52]
        + Op.PUSH24[0x1db054ccc801c0666b34b3c6242bbfc5e98f20c14fb95e01]
        + Op.PUSH8[0x18be9ad033d50e21] + Op.PUSH8[0x5ff59297861847ea]
        + Op.PUSH11[0x911a6a9d135e2f826dc603]
        + Op.PUSH30[0x850e0db21d105b8732a34b873c7d943050b8659794f0bd3e841d35a2231e]
        + Op.PUSH6[0xf697f8cde117] + Op.PUSH8[0x28fa2051e87933cf]
        + Op.PUSH7[0x858e4e5e91baa7]
        + Op.PUSH23[0x4fc1e9ffe4c7b15ba600e88f095989dc68f47ed704be2b] + Op.SWAP10
        + Op.PUSH1[0x17] + Op.PUSH2[0x215] + Op.PUSH4[0x200fbd63] + Op.CREATE
        + Op.PUSH31[0x41c7f86732f4d5419b41e6887cca98e0943f141a5c66df98bd0c6d6c4cec65]
        + Op.PUSH25[0x93afaa8ce1769c96cd0751aa76a98c8196fa8c92e70d7bda17]
        + Op.PUSH3[0x99c91c] + Op.RETURNDATACOPY
        + Op.PUSH27[0x7f05de3181109b8194387746f9ec15a6e0233f759e43360bd4e0a0]
        + Op.PUSH15[0x4e9f395117afcd072774ce12d13dc7] + Op.PUSH2[0x161] + Op.MSTORE
        + Op.ADDRESS + Op.GASPRICE + Op.PUSH9[0x3305858002a92140b6]
        + Op.PUSH25[0x508e3a3be377d4825dbf618a393c7c061e75a8a496a33afe0f]
        + Op.PUSH19[0x17f2e33549e321838b083d48893f23dced459]
        + Op.PUSH31[0x2e9ea08fe3f80970d6334b6c6f1fde8bcc81d03a7ccc244231cb6606dba6d0]
        + Op.PUSH15[0xc1c5158ef0db6994192acbd4cac6ab]
        + Op.PUSH11[0xc8449d80fc2c32471946e0]
        + Op.PUSH18[0xd9606bd390266d7f712766f4765076283ad6]
        + Op.PUSH9[0x7450d7ab4df6f3f6ee] + Op.SWAP7 + Op.PUSH2[0x14a]
        + Op.PUSH17[0xb802ec9d7ed96dc0b9ce7bd14b193dc1f0] + Op.MSTORE8
        + Op.PUSH23[0xd11ce19283c7f651d4d2e7c180715ff7fcbc995ea8b276]
        + Op.PUSH3[0x13cc51]
        + Op.PUSH30[0x6dad16d17f29a93220ce0ddb0a65d3d474dbc39cba5bcb3d4fcf9fef1910]
        + Op.PUSH1[0x7d] + Op.PUSH5[0xc04511df27]
        + Op.PUSH32[0x522ab2475fbb2ba0720711a903dbecfa0429bf11e6e90cbb0f13d4ee050c52c8]
        + Op.PUSH20[0x65e0216b4096186fc604fb563fa59f1263ee91d5]
        + Op.PUSH10[0x5e407fdffe82ca1558f7] + Op.DUP8
        + Op.PUSH11[0x93f3a218dd9ba6901fdea9] + Op.RETURNDATASIZE
        + Op.PUSH12[0xe498f0b0e1874331115e31aa]
        + Op.PUSH16[0xad4d87227362a9ec3e1c1be11cdb2309]
        + Op.PUSH10[0x7bbc0c692eeadfa91616] + Op.PUSH10[0xb8aec24564487dc74f8e]
        + Op.PUSH30[0x17e6a133b5dbe576838697de73f856197203ef1a3a54f7edb0dbd60f9d52]
        + Op.PUSH21[0xdb6b5c1477169b77f0d817ed731a20db4b9e5b83d2]
        + Op.PUSH25[0x6bffefab084a31c4afda168156612f281da0be688e5bdb1f31]
        + Op.PUSH23[0xed78bc62343a7665abad6573482449e68b3acfe820993d]
        + Op.PUSH24[0xdf5785384d51aaa0612dab5ddbf2a9bf550736ad42293387] + Op.DUP9
        + Op.PUSH2[0x119] + Op.PUSH2[0x23f] + Op.REVERT + Op.PUSH1[0x8f]
        + Op.PUSH2[0x22d] + Op.PUSH2[0x216] + Op.PUSH2[0x36e] + Op.PUSH4[0x5af7465b]
        + Op.PUSH20[0xffffffffffffffffffffffffffffffffffffffff] + Op.PUSH4[0x792c6916]
        + Op.CALL + Op.PUSH15[0xd70693587df6ccfae5218d01559bac] + Op.PUSH1[0x15]
        + Op.PUSH2[0x200] + Op.PUSH2[0x1ad] + Op.REVERT
    ),
    )
    pre[coinbase] = Account(
        balance=0x54c814f188394c8,
        nonce=29,
        code=bytes.fromhex(
        "610326610100f379c940b5f2046740058558468f238b85db7f6bbe3f3d51e92a3e3268b7"
        "f7c4147541c695f376705288410b81b217e80726fb9e4c5c7b4c49eca0c1b6b97e117c16"
        "c26c9816459f38396ffc36da48d65defdc7d055cbc846c07e81cfab0fb607c6cbc968774"
        "d4de7df8e3236f581e688cc2081a96b1cad9e0609b70f4fddda49ae97714e7d325ceab23"
        "acd5f46ba15b5210474116121921a04f68f3f933b9ad91b735bf71bfe41da706499c5d47"
        "b6de1fe398cb91fdf66481cbb8661d71d457cf3cef75dabf5ea496d7012f4c56b9fe70e6"
        "c4204720e3ce66874cead08499d57a547b97d37744ce205e051f296fb116fc9e5f3c2809"
        "19aff3c93c5d5cefff9a6102d86103ca6364b68c8ef07d"
    ),
    )

    tx = Transaction(
        secret_key=Hash(
            "0x3e297df41e49c542f54718bbee92d449778686880729c852f6d2c3c40d135341"
        ),
        to=contract,
        data=bytes.fromhex(
            "66a9b45d44c78cfe774333fe0c49418dd61f183d41132f5340e48ababb825a26eb0a75c0"
            "ca693a8b465121200fd21a7b4c365a65a3255278f672705e5ca0f6146fccd36a6e5b9dec"
            "fb6e5096887651e829313a2cc9d5b518e25861c31ba04ed3f5a3310bd966993aa534b007"
            "85778d9545342410ce8c156d780a8cb4a65efed30aa9d6bd63c4778a134c9cb0c677ecda"
            "48aacef0c191de37e3cfdae69153747c2406995ea81bbae6a201663b9b37a6a9f597ae4f"
            "40e44e74ea92616bc2956328ced0d77412c265c2925470320e5f285d15a08a263b0a4445"
            "16817c266bd51fe726677144df3c080d07dd47c4eb9e44a87541ddc5a697163260a06921"
            "033eb3542b375cd0d073dfb48f6acde07152794b5539563efff1afed3b0a6b1516652617"
            "5e7184b83cc2de68df61ec5d65d1eee66ea376fcb84f2c73335db9fba49e3d40638cd7f4"
            "62f1d3b315f17b8dc1f692a68b2431b166ee71a4ba159dd322b9fa5f3237dfb85d259405"
            "6102f261025b61021d6101d3631fe4bdc373ffffffffffffffffffffffffffffffffffff"
            "ffff631ea09dc6f263edd580947c8177bd72d2244f7652371e3428d28bc6356c553b18d0"
            "0e6b3cf60206c273abbd7763059f61940b0d19fde33f7b5a96080d25791e9ae89c718dd4"
            "1c3f57b0c304fbb83978de28d23499bdd19c0472301ff527ccc9f7ed74a8dbd906b468d4"
            "48fba77f38f193e3047b02e40beb08b4f11707681ef103ec1b00585a85f27227a179f15e"
            "7e97a359268b06ff34bcee23a869974fbca6e201cb16179743ac0f8c9f8603d570e26a5a"
            "ad5217ebfff3140716923723efaa79b6cd87fbc9fd408d4ac5a048e43fb4e7a2b94053bf"
            "1fb7257562977725cde415738a99e1a7690cbe409744b737367dedc82e3063516c5bc57e"
            "35fcb2038306d9a3a6e46103515279ddcb9d30879e470f5dd81e1148184f62bd61ae9708"
            "ff61cee25c63694a73437a42be5043b1fde117ba383682ba0d91e0db8b29c882a044d0c8"
            "bb49056a25a66d8480df1b1ccc2564791df94f43d5802aa8f44bf70a6817ed784e5725bd"
            "c7718a54d6a567234286085240ba847d575dac25d7fc32c59999a9d38fee0d25e7c23986"
            "009c5bb022f7d28a2cab6e01a4bb37dd42ea42d5141d55f5730c7bd82bf08bff3928aea7"
            "7e7153bcc4a3a53996be367ec98cb6fe85797e771d020284d4d302c8b4ebe6b28a9c64a9"
            "ae2ad6894716732f6b245e7fdc5243f79a0ae9b8d874900caa1c5796a2854ceddb00a82b"
            "4ec01b513ed61c72ce89400a06fe90a109bad6d5e028143e7552937a0136347eb71a49db"
            "0072c87bd437b9cd7b2f7e6e9f3a85875c9ede6036650f9d06d4c2e8692caf2e87043c0b"
            "f5a2359c66431acbb35dcbfc6a7b86074b99c9e6f959d8417784e5e40c854c280218c0cd"
            "4e98dc3bc44f7d651d7191ead455"
        ),
        gas_limit=2643883,
        gas_price=10,
        nonce=0,
        value=625999040,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
