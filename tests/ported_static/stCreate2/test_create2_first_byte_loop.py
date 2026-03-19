"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stCreate2/CREATE2_FirstByte_loopFiller.yml
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
    "1a8451e6000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ef",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000000ef00000000000000000000000000000000000000000000000000000000000000f0",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000000f00000000000000000000000000000000000000000000000000000000000000100",  # noqa: E501
]

TX_GAS = [16777216]

TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    ["tests/static/state_tests/stCreate2/CREATE2_FirstByte_loopFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(0, 0, 0, id="case0"),
        pytest.param(1, 0, 0, id="case1"),
        pytest.param(2, 0, 0, id="case2"),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_create2_first_byte_loop(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xF79127A3004ABDE26A4CBD80C428CB10F829FA11B54D36E7B326F4F4A5927ACF
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=89128960,
    )

    # Source: Yul
    # {
    #   let start := calldataload(4)
    #   let end := calldataload(36)
    #   // initcode: { mstore8(0, 0x00) return(0, 1) }
    #   mstore(0, 0x600060005360016000f300000000000000000000000000000000000000000000)  # noqa: E501
    #   for { let code := start } lt(code, end) { code := add(code, 1) }
    #   {
    #     mstore8(1, code) // change returned byte in initcode
    #     if iszero(create2(0, 0, 10, 0)) { sstore(code, 1) }
    #   }
    #   sstore(256, 1)
    # }
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(
                offset=0x0,
                value=0x600060005360016000F300000000000000000000000000000000000000000000,  # noqa: E501
            )
            + Op.CALLDATALOAD(offset=0x24)
            + Op.CALLDATALOAD(offset=0x4)
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x38, condition=Op.LT(Op.DUP2, Op.DUP2))
            + Op.SSTORE(key=0x100, value=0x1)
            + Op.STOP
            + Op.JUMPDEST
            + Op.DUP1
            + Op.PUSH1[0x1]
            + Op.SWAP2
            + Op.DUP3
            + Op.MSTORE8
            + Op.JUMPI(
                pc=0x4F,
                condition=Op.ISZERO(
                    Op.CREATE2(
                        value=Op.DUP1, offset=Op.DUP2, size=0xA, salt=0x0
                    ),
                ),
            )
            + Op.JUMPDEST
            + Op.ADD
            + Op.JUMP(pc=0x2A)
            + Op.JUMPDEST
            + Op.SSTORE(key=Op.DUP2, value=Op.DUP2)
            + Op.JUMP(pc=0x4A)
        ),
        nonce=0,
        address=Address("0x09fdd11d68be787a4c43f692a0778befc011cd35"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x3B9ACA00)

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                Address("0x013e3ddba3f657af0f05dc30dd5842b055baebf5"): Account(
                    code=bytes.fromhex("02")
                ),
                Address("0x0224b54589bcb13c7cfac521cbef4c5915cc0166"): Account(
                    code=bytes.fromhex("3f")
                ),
                Address("0x02bb7e260960530deb147e3f71e57639ac7cc96b"): Account(
                    code=bytes.fromhex("ec")
                ),
                Address("0x03a7a3e49083d4720b6ce4daa03b9cbc0807baf5"): Account(
                    code=bytes.fromhex("82")
                ),
                Address("0x043b81490ad7333e4990ded04d8a74d5d359a30f"): Account(
                    code=bytes.fromhex("13")
                ),
                Address("0x0690089e309e4998a8a5b05201fcf9d7b230e857"): Account(
                    code=bytes.fromhex("a7")
                ),
                Address("0x0886289bc893311a1c210d60dc6de0aca85ab7e4"): Account(
                    code=bytes.fromhex("44")
                ),
                Address("0x094cf14d701f37438ee7ecb2f46a1ec73593da8c"): Account(
                    code=bytes.fromhex("97")
                ),
                Address("0x0999024c399f7c477d7820473cf4d1012d7391ac"): Account(
                    code=bytes.fromhex("7f")
                ),
                contract: Account(
                    storage={256: 1},
                    code=bytes.fromhex(
                        "7f600060005360016000f3000000000000000000000000000000000000000000006000526024356004355b818110603857600161010055005b8060019182536000600a8180f515604f575b01602a565b818155604a56"  # noqa: E501
                    ),
                ),
                Address("0x0baad227bd545396f0c965bf0bb6983d1ded75eb"): Account(
                    code=bytes.fromhex("28")
                ),
                Address("0x0cbad3bfd342542e2799a3fe5ce4ab681bdbe9cc"): Account(
                    code=bytes.fromhex("c7")
                ),
                Address("0x0d03885ed4f051b06ae83d869cd60f8ebdde37d8"): Account(
                    code=bytes.fromhex("00")
                ),
                Address("0x0d1438f8967a5ba92346e78c1b5c74a7d3bcd6d0"): Account(
                    code=bytes.fromhex("c5")
                ),
                Address("0x0e242b435e86bfa5280e0eb135991b2a7be7d41d"): Account(
                    code=bytes.fromhex("4e")
                ),
                Address("0x0f3f3016c132cd3a93b69678c6bd776650cab189"): Account(
                    code=bytes.fromhex("c3")
                ),
                Address("0x0fa2c4df612f32c40c744602205a02a197442b29"): Account(
                    code=bytes.fromhex("94")
                ),
                Address("0x0fb3bb43a0e31556ca58331eee49b642a1062823"): Account(
                    code=bytes.fromhex("0f")
                ),
                Address("0x1063fb0126ef31ab7d301ad3f8f8ab3dacc9b429"): Account(
                    code=bytes.fromhex("e8")
                ),
                Address("0x10b4e0f0fc8036f85842c3f36d6b3a3bf4a01c0c"): Account(
                    code=bytes.fromhex("2a")
                ),
                Address("0x1184de3efe72af300e9fd9dc46b54b990ffd216a"): Account(
                    code=bytes.fromhex("c9")
                ),
                Address("0x16bcc946d2cce77042c7cd5615eb4ac8bb394128"): Account(
                    code=bytes.fromhex("8b")
                ),
                Address("0x16cadb0677c9f15b6cae111f82db032027701a12"): Account(
                    code=bytes.fromhex("40")
                ),
                Address("0x16ff81957b8445c1962967b2c352a93ebd09a5ac"): Account(
                    code=bytes.fromhex("2d")
                ),
                Address("0x18b8cdcf5d71bca5bef2408eac496ddc9adb3961"): Account(
                    code=bytes.fromhex("90")
                ),
                Address("0x19158da48e5fd23c53beea08ff3588078ff1a673"): Account(
                    code=bytes.fromhex("68")
                ),
                Address("0x1a5d69053e8fdbd0d3eb5369d85fc1f0f59107d3"): Account(
                    code=bytes.fromhex("a0")
                ),
                Address("0x1bd700e26df035a257cbd6ec1477b7a104834f64"): Account(
                    code=bytes.fromhex("15")
                ),
                Address("0x1c017528a05b9a163ae452d8a2f92e9ef0cc15ad"): Account(
                    code=bytes.fromhex("72")
                ),
                Address("0x1d6b687e84941d346b33d7a7808b1bd705ab8d09"): Account(
                    code=bytes.fromhex("5a")
                ),
                Address("0x1d77a28c2c9ee76a12baaf00925e4edd859cc677"): Account(
                    code=bytes.fromhex("8d")
                ),
                Address("0x1f3d2bc2d11e9d6dc1b7f9e7725f7d41c8b7c832"): Account(
                    code=bytes.fromhex("5f")
                ),
                Address("0x1fe9a1e61ee627e28dfec818025a678d2f48854d"): Account(
                    code=bytes.fromhex("eb")
                ),
                Address("0x22b03d21c55e25c59c88e7599b24912f4bdd7e5a"): Account(
                    code=bytes.fromhex("6d")
                ),
                Address("0x243b4c7f1517397d526cbefa354c5c392d1d4844"): Account(
                    code=bytes.fromhex("79")
                ),
                Address("0x24812f69cc656e6b2de3149bebd2a81dbb2b51cc"): Account(
                    code=bytes.fromhex("c0")
                ),
                Address("0x26dd18220015b3f1caa012d35fda436f8880855d"): Account(
                    code=bytes.fromhex("1c")
                ),
                Address("0x29259d452eb70e85288045a19577c2a7faa702dc"): Account(
                    code=bytes.fromhex("88")
                ),
                Address("0x2982c55510e54bf363e8dc3b87c4228e98c9e90b"): Account(
                    code=bytes.fromhex("be")
                ),
                Address("0x309dc8ac7dd6e4dcf51e96e73c45091f1c170387"): Account(
                    code=bytes.fromhex("73")
                ),
                Address("0x30a099a451c962803389feb3181e1d483f9d7310"): Account(
                    code=bytes.fromhex("67")
                ),
                Address("0x3182a06e447b23439a78cf3a6e4fcef4ccc0b778"): Account(
                    code=bytes.fromhex("22")
                ),
                Address("0x3244566d9457d38f7bddb4917303b8e738b2a67b"): Account(
                    code=bytes.fromhex("3c")
                ),
                Address("0x32c13e6ae8e2cf57813bdf6c825df21ef08f959e"): Account(
                    code=bytes.fromhex("de")
                ),
                Address("0x331dbb753caeff09afdb6816c3174162440806d4"): Account(
                    code=bytes.fromhex("2c")
                ),
                Address("0x336257577321373ce4befa4c4aa9c9c539d67e55"): Account(
                    code=bytes.fromhex("a1")
                ),
                Address("0x35eb14e52556459b38d8a4f7eb054f15a58b4ab5"): Account(
                    code=bytes.fromhex("87")
                ),
                Address("0x368fd13e67530b7e30b4d6ba6b04f9aefdb87238"): Account(
                    code=bytes.fromhex("66")
                ),
                Address("0x3736b99027b3ff420c6f5ae2029aa29162b40147"): Account(
                    code=bytes.fromhex("2b")
                ),
                Address("0x3779259fb4452f53cdb0ab391214316b5c963423"): Account(
                    code=bytes.fromhex("cb")
                ),
                Address("0x38e44fdcc9d06ad187ccf981904a1ab52bbdb971"): Account(
                    code=bytes.fromhex("3d")
                ),
                Address("0x3a3bacc1f4963401637d608f5a1581a530e27101"): Account(
                    code=bytes.fromhex("41")
                ),
                Address("0x3b67cc221a6e832c4e3bf7d411bdf33bdebbf9e3"): Account(
                    code=bytes.fromhex("e1")
                ),
                Address("0x3de475e0804cbd1d5fb7df9e71f13057d6bcec33"): Account(
                    code=bytes.fromhex("e4")
                ),
                Address("0x3deb5d72a87f5d97871d6c4a7c53c003b178aea1"): Account(
                    code=bytes.fromhex("0e")
                ),
                Address("0x3e54306e45333000efa8e215a951535b55a6b4e0"): Account(
                    code=bytes.fromhex("95")
                ),
                Address("0x3e6017158de20472a938fda3ff84256b5ae89867"): Account(
                    code=bytes.fromhex("cf")
                ),
                Address("0x4018be476b6c82c3786c7bf154e1444a9453b225"): Account(
                    code=bytes.fromhex("91")
                ),
                Address("0x40336ce4d9455d6270c0c4e1f5971a67db7bfad5"): Account(
                    code=bytes.fromhex("08")
                ),
                Address("0x422bc31c05340e16d1afbc9f4b0f4482216e4ef7"): Account(
                    code=bytes.fromhex("1f")
                ),
                Address("0x483524b7cd0ef87f64f2c66acca745422b9c7cad"): Account(
                    code=bytes.fromhex("6e")
                ),
                Address("0x485a2441041adb043bd510aa8d66c904de65b9dd"): Account(
                    code=bytes.fromhex("92")
                ),
                Address("0x4a9bcaac65525c44054cc89b7da486234abda46a"): Account(
                    code=bytes.fromhex("54")
                ),
                Address("0x4bdfaee3d4a52bbcfd775f047a3ba922a28a9878"): Account(
                    code=bytes.fromhex("3b")
                ),
                Address("0x4c5c1e0f58fe34edaa24db427d6004e3c00d12e3"): Account(
                    code=bytes.fromhex("5b")
                ),
                Address("0x4cf62ccf8679f1a9ec8dd7d13412a02cdd2bf6cc"): Account(
                    code=bytes.fromhex("80")
                ),
                Address("0x4df182ba48c74d495eb6d3ff7b017d0e42f7b2c8"): Account(
                    code=bytes.fromhex("b4")
                ),
                Address("0x4f2a32c3c4eefd21f66770895096fb889c162ab4"): Account(
                    code=bytes.fromhex("a6")
                ),
                Address("0x51baaf13d8cb38d3e8105b4747106fd318435686"): Account(
                    code=bytes.fromhex("ac")
                ),
                Address("0x51d8eca2affad6e77abca9fedc4f3d388feee39d"): Account(
                    code=bytes.fromhex("bb")
                ),
                Address("0x51e15a587c79d847a67fc67b681d22c01b0baf59"): Account(
                    code=bytes.fromhex("03")
                ),
                Address("0x5261518665caac666b102b68a9516b31d409f6a5"): Account(
                    code=bytes.fromhex("ea")
                ),
                Address("0x5531a9f3bd8dc59284aaa148b56003315e079660"): Account(
                    code=bytes.fromhex("db")
                ),
                Address("0x58bd579e6fa34ebec02fd1863b71c63cfd78967c"): Account(
                    code=bytes.fromhex("af")
                ),
                Address("0x59bcbed1b83b852a3f3e1bcb57a54e54a2ff2687"): Account(
                    code=bytes.fromhex("93")
                ),
                Address("0x5aaadb34a96f978117a9a1b44e5554478b1bb64c"): Account(
                    code=bytes.fromhex("e3")
                ),
                Address("0x5b5b16f9255481b182a896d445d5817a0f00da9d"): Account(
                    code=bytes.fromhex("ad")
                ),
                Address("0x5b74a72369a50d7c35b5c80c2b765c79bb2320b1"): Account(
                    code=bytes.fromhex("bc")
                ),
                Address("0x5ca8c07d02a853ffa28be97ff073c0d712c3ed72"): Account(
                    code=bytes.fromhex("bf")
                ),
                Address("0x5d00b86dee0a592ec379469fe5da1d887ea3942f"): Account(
                    code=bytes.fromhex("07")
                ),
                Address("0x5f947d0736feeaebd5444743bea53466e1082736"): Account(
                    code=bytes.fromhex("33")
                ),
                Address("0x606b39e2f69430e73abebfd0132eb90de5b29192"): Account(
                    code=bytes.fromhex("32")
                ),
                Address("0x60eafc0c8b3d6976f2fb94498fb5b04d050477cc"): Account(
                    code=bytes.fromhex("a3")
                ),
                Address("0x61b01ea840a2e1fad7b4c48fc0d2a25b9dd7ba68"): Account(
                    code=bytes.fromhex("83")
                ),
                Address("0x61b8e57ab6fd44a1a22802e68f2322c81a1fd160"): Account(
                    code=bytes.fromhex("42")
                ),
                Address("0x61d667c994d66b12595b017eeda60d34fe0e7436"): Account(
                    code=bytes.fromhex("d7")
                ),
                Address("0x62663b2714f9a33fbf4a2c5da4ea7c5b86f54d7a"): Account(
                    code=bytes.fromhex("da")
                ),
                Address("0x6317561ecf1ecb9ce29dd076e707dc58fd0fd5d4"): Account(
                    code=bytes.fromhex("8c")
                ),
                Address("0x652ba05ebddb57658a948442ade80776cec4ce15"): Account(
                    code=bytes.fromhex("ca")
                ),
                Address("0x67df325ac2d12548956118b35dc39a8266c1565c"): Account(
                    code=bytes.fromhex("8f")
                ),
                Address("0x68670b15312fbf04b740320cd34798855f892193"): Account(
                    code=bytes.fromhex("3e")
                ),
                Address("0x6a093a8494efe94babc770f0a7b9b0d6ec89a523"): Account(
                    code=bytes.fromhex("0b")
                ),
                Address("0x6d053eae87ed83c0be0809e859a361d27d5db2c1"): Account(
                    code=bytes.fromhex("14")
                ),
                Address("0x6d50e2263974029587d595b00808a4ddecf6cfb1"): Account(
                    code=bytes.fromhex("17")
                ),
                Address("0x6e88b27fbe193d61466f92e14f98af521f050400"): Account(
                    code=bytes.fromhex("e7")
                ),
                Address("0x6eb78d64ded78aa304fe2c73a83a562063164b76"): Account(
                    code=bytes.fromhex("7d")
                ),
                Address("0x6ef37fdcaaec0ff0399ee701afb6f62eaa18b5fc"): Account(
                    code=bytes.fromhex("81")
                ),
                Address("0x6f111b56cf8654292ecc2cb0378356e2ae5da6b5"): Account(
                    code=bytes.fromhex("06")
                ),
                Address("0x714d01c385f52867373472476c91a0ae10eb631b"): Account(
                    code=bytes.fromhex("b2")
                ),
                Address("0x734d18813c77791b1e0c5114469d1c61016fcb66"): Account(
                    code=bytes.fromhex("34")
                ),
                Address("0x754e4e2ca49d1731dc306f7eb83132bfe582e7f2"): Account(
                    code=bytes.fromhex("d6")
                ),
                Address("0x75b7967088840cec2f6f65bd7ab5a57a9acf8316"): Account(
                    code=bytes.fromhex("86")
                ),
                Address("0x75dd378b38db6ee28c74becfcec44a78c1a0441a"): Account(
                    code=bytes.fromhex("cc")
                ),
                Address("0x7733cd8b26b83fe38d35c584f0898a71086bc526"): Account(
                    code=bytes.fromhex("75")
                ),
                Address("0x78360ad6903905c12602e9260b006e0708e23b8a"): Account(
                    code=bytes.fromhex("d9")
                ),
                Address("0x7b844a2fc5c4d57e3c85ed73821f361cd00ad30d"): Account(
                    code=bytes.fromhex("46")
                ),
                Address("0x7c1b3ca4d2d114e7051f88e92e5473cf75e7b381"): Account(
                    code=bytes.fromhex("96")
                ),
                Address("0x7dcba477ced3c74bedf83b542f31cae8b2b53a45"): Account(
                    code=bytes.fromhex("d8")
                ),
                Address("0x7f2ddb532124b2e635cc15610196715b0be1c217"): Account(
                    code=bytes.fromhex("59")
                ),
                Address("0x80d670e32d0ee84d4ebeffbada83073ebbba1eeb"): Account(
                    code=bytes.fromhex("52")
                ),
                Address("0x819e0c753d0add87c4b0964348fcd71ee60b5e4f"): Account(
                    code=bytes.fromhex("43")
                ),
                Address("0x82a688e4e2a0e407048032ece2dec2735c150b30"): Account(
                    code=bytes.fromhex("d0")
                ),
                Address("0x8323b623970ecd53b515dbdf7d2257965dc1501a"): Account(
                    code=bytes.fromhex("8a")
                ),
                Address("0x849a6f9eb90c0d1f5b40c0fba7f6ddb2db9f4d96"): Account(
                    code=bytes.fromhex("25")
                ),
                Address("0x851b8ab5c765621b86ab09dd0a72fbdb71de2b26"): Account(
                    code=bytes.fromhex("85")
                ),
                Address("0x864b5484609ec4ab3320bc7aebf489ff45462d9d"): Account(
                    code=bytes.fromhex("d2")
                ),
                Address("0x89df3db713157de983ed0836a8c6990ea8628332"): Account(
                    code=bytes.fromhex("84")
                ),
                Address("0x89eb5b23f979049ddc01459894ee321be6e3d6fe"): Account(
                    code=bytes.fromhex("6f")
                ),
                Address("0x8b2038da858b4789cdeecb77de96caa660f6f919"): Account(
                    code=bytes.fromhex("c1")
                ),
                Address("0x8bf88bff285f142fe61d2542621fd143cf12f4c1"): Account(
                    code=bytes.fromhex("04")
                ),
                Address("0x8e1dbcf64a6a613208eb1ae70604198e91156f96"): Account(
                    code=bytes.fromhex("76")
                ),
                Address("0x8e1e0e3e8f1a03f17be69e3590bd87505af657d2"): Account(
                    code=bytes.fromhex("df")
                ),
                Address("0x8fb3e895f98947de418ea9bdcd1c6ded0ddf9436"): Account(
                    code=bytes.fromhex("ba")
                ),
                Address("0x90c2e9c746d28cffdc6bc6e64eb2d84848da2979"): Account(
                    code=bytes.fromhex("19")
                ),
                Address("0x90e0eadc09d3a68906ea98a2f491a812ec014042"): Account(
                    code=bytes.fromhex("30")
                ),
                Address("0x917f282ccc051b582c75d69de2d2f77558d01b32"): Account(
                    code=bytes.fromhex("64")
                ),
                Address("0x920e69eb2bce3811404bdc4876d9d6d105c099a3"): Account(
                    code=bytes.fromhex("ae")
                ),
                Address("0x9213ce17234c9204bdd6def47c81b6d0b340984c"): Account(
                    code=bytes.fromhex("63")
                ),
                Address("0x923c78dfcc5b02b5e1b6d521a9fba70465eefab5"): Account(
                    code=bytes.fromhex("b1")
                ),
                Address("0x92677d7ddd0bad23935af236f6336d5e9338d2e6"): Account(
                    code=bytes.fromhex("3a")
                ),
                Address("0x9372388c6d9ce24ca0e249aa827f9ff2b641a202"): Account(
                    code=bytes.fromhex("bd")
                ),
                Address("0x942513234c11851bb10e44f4577f5a6cce7fad41"): Account(
                    code=bytes.fromhex("5e")
                ),
                Address("0x9438534827d857f5224200f759b77363d611aa9e"): Account(
                    code=bytes.fromhex("9f")
                ),
                Address("0x944bc6b39f0e791f6c337108ba01e1ec9b2ba55a"): Account(
                    code=bytes.fromhex("56")
                ),
                Address("0x94a388c70e6f6b7f1278b881d57479b74f46be59"): Account(
                    code=bytes.fromhex("c6")
                ),
                Address("0x94b507d001a223d7948119d899358a073fe5e331"): Account(
                    code=bytes.fromhex("ee")
                ),
                Address("0x9887a94dea014df90a0f86df570a0737cf88fdc9"): Account(
                    code=bytes.fromhex("31")
                ),
                Address("0x9a60dc9a38714f2800e2bd9915733b4a5d173cdb"): Account(
                    code=bytes.fromhex("51")
                ),
                Address("0x9aa011f281bbfd8f9dc302221f027316f13f066b"): Account(
                    code=bytes.fromhex("5c")
                ),
                Address("0x9bca700a703b09867dd79e37999b607e47978591"): Account(
                    code=bytes.fromhex("9d")
                ),
                Address("0x9bd09ea8167c09d875ba7f88272012afd239f565"): Account(
                    code=bytes.fromhex("5d")
                ),
                Address("0x9ccc4a50a9c5f9cac81d45d82309203cbd1b7227"): Account(
                    code=bytes.fromhex("09")
                ),
                Address("0x9d0633c9368df76b6b9f29d8066789e4b4153dab"): Account(
                    code=bytes.fromhex("cd")
                ),
                Address("0x9d3da34904461ea9a5091204d4522b1e8a5e5b3e"): Account(
                    code=bytes.fromhex("23")
                ),
                Address("0x9df196006528c7589c5b00ea520b9e7fb726bda2"): Account(
                    code=bytes.fromhex("71")
                ),
                Address("0x9e0ad0d35439a8c8725756b493761db9e2e1c6c2"): Account(
                    code=bytes.fromhex("69")
                ),
                Address("0x9e129ccbd3a730427f5ec8edc6ea9304a2d1d4b8"): Account(
                    code=bytes.fromhex("18")
                ),
                Address("0x9ecbd230fab2f1c3de3d864df05b8ebf746ac26c"): Account(
                    code=bytes.fromhex("aa")
                ),
                Address("0x9f5dbd8c2c9015cff2c99b1a627b30b79852d2ba"): Account(
                    code=bytes.fromhex("27")
                ),
                Address("0xa0194d3beca6170a68427162da4f8abd16f480af"): Account(
                    code=bytes.fromhex("a4")
                ),
                Address("0xa04d0a88a9ae6c46bc745c798c9519e1ba89fce1"): Account(
                    code=bytes.fromhex("9c")
                ),
                Address("0xa0fe04ffd7e70c2bfd5cc77c71edac5787ac80c5"): Account(
                    code=bytes.fromhex("29")
                ),
                Address("0xa121689d6c5fc55f45f0153840354c0b1ab0fb9a"): Account(
                    code=bytes.fromhex("1d")
                ),
                Address("0xa1321ad573c8e819d6cedb91404be76099d52cb3"): Account(
                    code=bytes.fromhex("62")
                ),
                Address("0xa2177f3bb90dd726d0f74b38a17d7650c6bb00db"): Account(
                    code=bytes.fromhex("24")
                ),
                Address("0xa2b32e58f26129b3c7db1b29f9fe1dbd5f06300b"): Account(
                    code=bytes.fromhex("89")
                ),
                Address("0xa36bc5ec80ff9f2e4880fbfe6c0f0564e2fedc61"): Account(
                    code=bytes.fromhex("4b")
                ),
                Address("0xa45f9a24e6824aae43a4d3c651e0633a73791cf1"): Account(
                    code=bytes.fromhex("2e")
                ),
                Address("0xa5a6256f2dc67315571dc941c8bcdfbd689da314"): Account(
                    code=bytes.fromhex("7a")
                ),
                Address("0xa5d6ad838d128ffe7c39156ce3be38070636a844"): Account(
                    code=bytes.fromhex("74")
                ),
                Address("0xa772c31a50f49fdb1c38844acbd1da01058eab8c"): Account(
                    code=bytes.fromhex("55")
                ),
                Address("0xa8f1f5e8946c02aaa9e1ef76345b48b2a1bd2e72"): Account(
                    code=bytes.fromhex("11")
                ),
                Address("0xac93d96a6bf62070ebc7bc5da426aed65e8c0279"): Account(
                    code=bytes.fromhex("26")
                ),
                Address("0xace653909db84c7a21b84fb5e0030900d380620c"): Account(
                    code=bytes.fromhex("49")
                ),
                Address("0xacfb937e08f245b0b925d6494e24f5e3380694f3"): Account(
                    code=bytes.fromhex("1a")
                ),
                Address("0xade6af237ebe91a4a089a7e2d2947ac950929c30"): Account(
                    code=bytes.fromhex("70")
                ),
                Address("0xaed70239fad0cccf38eca9b42c837bc2b7b90081"): Account(
                    code=bytes.fromhex("98")
                ),
                Address("0xaf6e76cea557fe9aea01a5995165dd3acf9fc314"): Account(
                    code=bytes.fromhex("d1")
                ),
                Address("0xb02a384fb112e54cc3cdc2c6ea6b3ab45f70680b"): Account(
                    code=bytes.fromhex("b6")
                ),
                Address("0xb053a8a8b29da0456612fd1bea8097b38d54499f"): Account(
                    code=bytes.fromhex("47")
                ),
                Address("0xb16ff84e2bbe3da2f4264371798af1e36c116c27"): Account(
                    code=bytes.fromhex("21")
                ),
                Address("0xb6260c3f6c760c6c15c2f8d517adb528387ac60f"): Account(
                    code=bytes.fromhex("39")
                ),
                Address("0xb665f20aae80b544107967d6b3457a3cd8aea7e5"): Account(
                    code=bytes.fromhex("0d")
                ),
                Address("0xb6a115e154c4f224c80efe516d56d22864039ad5"): Account(
                    code=bytes.fromhex("0c")
                ),
                Address("0xb7c2524aacd673374e4ab9f59d36c0af7e34841f"): Account(
                    code=bytes.fromhex("12")
                ),
                Address("0xbb91c2530eff3457d9eef4023c3ec9f2dc138450"): Account(
                    code=bytes.fromhex("36")
                ),
                Address("0xbd7a0a7a887168bf69d77a5f6f5327bbeaabdc2b"): Account(
                    code=bytes.fromhex("b8")
                ),
                Address("0xbfd3c45dcbf5d5904e33b81875ddf5b1f15dfc13"): Account(
                    code=bytes.fromhex("01")
                ),
                Address("0xc0b4d0c4cd917296f37c72cf9819924973a7ee1b"): Account(
                    code=bytes.fromhex("45")
                ),
                Address("0xc0cf186c24141d69e1d20ff2cd5bdec9be8ab785"): Account(
                    code=bytes.fromhex("05")
                ),
                Address("0xc17ac54bafe20657752a9640235821205973ca88"): Account(
                    code=bytes.fromhex("b7")
                ),
                Address("0xc27566be015f50cf1d7f24abb68e0d17cad55f2e"): Account(
                    code=bytes.fromhex("b5")
                ),
                Address("0xc27a8cb52c886b43b2d8f6d0e862576a0c3966f8"): Account(
                    code=bytes.fromhex("6a")
                ),
                Address("0xc379e4bc72974bc40de918ba73ea7c1bfc42b7ac"): Account(
                    code=bytes.fromhex("dd")
                ),
                Address("0xc6c80264b29b13efe41cea2845ed7fe56fc5e802"): Account(
                    code=bytes.fromhex("35")
                ),
                Address("0xc75bb53f5bf285d71f966c88f7c0510a1bd44b6e"): Account(
                    code=bytes.fromhex("9b")
                ),
                Address("0xc7b8d44ca2296a34574e2493db17e8bc0ca3bb38"): Account(
                    code=bytes.fromhex("8e")
                ),
                Address("0xc7fcaf2fe80a01788419e97614ca277995d80c99"): Account(
                    code=bytes.fromhex("4a")
                ),
                Address("0xc81538e290b3d1e3a0eeab500ae83f08c1ee6e3c"): Account(
                    code=bytes.fromhex("50")
                ),
                Address("0xc9a6adf4ab3739dc89216c4f63994c3563ceee65"): Account(
                    code=bytes.fromhex("53")
                ),
                Address("0xc9fdb2413eada793de23ed1e406819c5827dde61"): Account(
                    code=bytes.fromhex("9e")
                ),
                Address("0xca34b71c190e0d3317cb980371c9b2cf23496918"): Account(
                    code=bytes.fromhex("b3")
                ),
                Address("0xca52ebc06dc8434a0823bb780f3afbdeb351d525"): Account(
                    code=bytes.fromhex("58")
                ),
                Address("0xcba97325070dd3d8ac77f285809239fee2718051"): Account(
                    code=bytes.fromhex("b0")
                ),
                Address("0xceecdc0231b8e90f9267b51453853781addab55f"): Account(
                    code=bytes.fromhex("38")
                ),
                Address("0xcfbc70e723bf9ad1ae1a959feaf370826f593f9f"): Account(
                    code=bytes.fromhex("16")
                ),
                Address("0xd17a40495ca7d40c158b73b6a73b4f98dc0895a3"): Account(
                    code=bytes.fromhex("d3")
                ),
                Address("0xd521a3471e543de5c50e16d6ae25077e31006995"): Account(
                    code=bytes.fromhex("e6")
                ),
                Address("0xd535c93dbdb259c0c4135968c5188f7f2ae34828"): Account(
                    code=bytes.fromhex("99")
                ),
                Address("0xd5413f13c536e63432af1ad29ec598342f02ebee"): Account(
                    code=bytes.fromhex("1b")
                ),
                Address("0xd5c8c8c0c86672b12a4f6b5210f432006244244c"): Account(
                    code=bytes.fromhex("e2")
                ),
                Address("0xd5ecde5d708f39929647ced5f4376e79edf3dce1"): Account(
                    code=bytes.fromhex("2f")
                ),
                Address("0xd622552f48a3cd38a3237ba8ddfe5d049dfb6771"): Account(
                    code=bytes.fromhex("d5")
                ),
                Address("0xd6a5d5e09ef2483bac0b69966507e0daea39a771"): Account(
                    code=bytes.fromhex("61")
                ),
                Address("0xd6c77ed459f345f56d70b330c171b95367f5828c"): Account(
                    code=bytes.fromhex("c4")
                ),
                Address("0xd71b77b3d09277b1e4b3e5207f6035af3eab2634"): Account(
                    code=bytes.fromhex("1e")
                ),
                Address("0xd95defdf76a2f495975eab8431525805a31642e1"): Account(
                    code=bytes.fromhex("4c")
                ),
                Address("0xde91d10527a84c5765a4e2b3b62ca7ed99275660"): Account(
                    code=bytes.fromhex("b9")
                ),
                Address("0xe09779d14014280acffcbfa797668a17c9b41043"): Account(
                    code=bytes.fromhex("a9")
                ),
                Address("0xe0a4939f1e2258c27df9902f8136139892624905"): Account(
                    code=bytes.fromhex("e0")
                ),
                Address("0xe0b8ebc511d5d5f6f3bce2af3d01b87f920ed990"): Account(
                    code=bytes.fromhex("e5")
                ),
                Address("0xe35df43200469b55b142acff30dec574447559b4"): Account(
                    code=bytes.fromhex("4d")
                ),
                Address("0xe4a48fbec33ebad8ff03bbc6b633214b6a0f99ff"): Account(
                    code=bytes.fromhex("37")
                ),
                Address("0xe68e7090f263d1ad63d53097a0a6ea872ba83488"): Account(
                    code=bytes.fromhex("a5")
                ),
                Address("0xe717767614fc62fac66512f7d14a5b77b912039f"): Account(
                    code=bytes.fromhex("ce")
                ),
                Address("0xe9508ffee2153f95927f0e90a1b091a79d92f4cf"): Account(
                    code=bytes.fromhex("ed")
                ),
                Address("0xea2ee3dd9e46d10a79216446d2605d6f629e36c8"): Account(
                    code=bytes.fromhex("78")
                ),
                Address("0xed224f9db32d20f884b9c8edaa7b730c5f8f41b1"): Account(
                    code=bytes.fromhex("7b")
                ),
                Address("0xef2a648613a66eff36dbb498a5157db95dadf9db"): Account(
                    code=bytes.fromhex("20")
                ),
                Address("0xefa4282d9bb8bd04a0c9d19af9e34f889b8d3db0"): Account(
                    code=bytes.fromhex("48")
                ),
                Address("0xf0a2cf1f39c93e0f6b0fe7a4a48ba459898bb2d9"): Account(
                    code=bytes.fromhex("ab")
                ),
                Address("0xf39f932c52f091b1bf1a80b4966a43400cd42957"): Account(
                    code=bytes.fromhex("6b")
                ),
                Address("0xf56aeba12b2e27b53c918e8a5837629f0266c330"): Account(
                    code=bytes.fromhex("4f")
                ),
                Address("0xf57895c6da5877c0ffb4df7659debcd36f94478a"): Account(
                    code=bytes.fromhex("60")
                ),
                Address("0xf5a10e2b3caf2d2a348ba2a36927c0f178fefc9f"): Account(
                    code=bytes.fromhex("e9")
                ),
                Address("0xf5e5e37d6a7af368ca71edc99db716b4f7e5d160"): Account(
                    code=bytes.fromhex("10")
                ),
                Address("0xf5f6b7cd6b4b660499fc01f44980627a79ad15c6"): Account(
                    code=bytes.fromhex("0a")
                ),
                Address("0xf669d895834c50200348687b6c272eb4bf153505"): Account(
                    code=bytes.fromhex("57")
                ),
                Address("0xf68fc0e4488e0dc0c65715a9ca684c6660eed489"): Account(
                    code=bytes.fromhex("7e")
                ),
                Address("0xf6a755fa694198222d9d51eb257e81c70ac8faa8"): Account(
                    code=bytes.fromhex("a8")
                ),
                Address("0xf7f10c19c48f7d254e9d084575c5c8b145ee1639"): Account(
                    code=bytes.fromhex("c8")
                ),
                Address("0xf82c571bc55a12852fe0de1cb88017daec283dcf"): Account(
                    code=bytes.fromhex("c2")
                ),
                Address("0xf873cc69f48f164be94fa2b96f4bc3e262ad5833"): Account(
                    code=bytes.fromhex("7c")
                ),
                Address("0xf8c799cec07550adbabb4cb6365374bf15b6624c"): Account(
                    code=bytes.fromhex("a2")
                ),
                Address("0xf92ee445f202b95e4254332d07e349437c2dce8f"): Account(
                    code=bytes.fromhex("6c")
                ),
                Address("0xfac8a0ed8609d54d8cfe8f947547e46cd84ec439"): Account(
                    code=bytes.fromhex("9a")
                ),
                Address("0xfde1e9f0558f54e33912dab00eace3787dc72303"): Account(
                    code=bytes.fromhex("dc")
                ),
                Address("0xfe1d94ac52f012bd18120a8e22c1063cccea037b"): Account(
                    code=bytes.fromhex("65")
                ),
                Address("0xfe7e9defcbe3a7e711844f5765bc06eadd6dc116"): Account(
                    code=bytes.fromhex("77")
                ),
                Address("0xffbc38f9a543a24d0c3a0e1d77f64a3c8948e28c"): Account(
                    code=bytes.fromhex("d4")
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={239: 1, 256: 1},
                    code=bytes.fromhex(
                        "7f600060005360016000f3000000000000000000000000000000000000000000006000526024356004355b818110603857600161010055005b8060019182536000600a8180f515604f575b01602a565b818155604a56"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 2, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                Address("0x070db4fa29b5d139bedb29347001bb9c3d75dc3a"): Account(
                    code=bytes.fromhex("ff")
                ),
                Address("0x0921b94546fac76144d92d3c6cd96a3784fb0254"): Account(
                    code=bytes.fromhex("f9")
                ),
                contract: Account(
                    storage={256: 1},
                    code=bytes.fromhex(
                        "7f600060005360016000f3000000000000000000000000000000000000000000006000526024356004355b818110603857600161010055005b8060019182536000600a8180f515604f575b01602a565b818155604a56"  # noqa: E501
                    ),
                ),
                Address("0x0deb678ad394bd015a846c2c8731943c0bb13795"): Account(
                    code=bytes.fromhex("f3")
                ),
                Address("0x2e3f76fff36e20b0cd74ee90abceb94e5215b815"): Account(
                    code=bytes.fromhex("fe")
                ),
                Address("0x65ffaf4d5b8e3efec7168f5fcc75baa24b627d39"): Account(
                    code=bytes.fromhex("f4")
                ),
                Address("0x6812a41ce61f22b4861e457ba383905680d0a3ed"): Account(
                    code=bytes.fromhex("fa")
                ),
                Address("0x8068a55ce40cff0f8ad518429fcea001c94df346"): Account(
                    code=bytes.fromhex("fc")
                ),
                Address("0x820bd67ad14a30f7778e54ddb440aa4acebca5fe"): Account(
                    code=bytes.fromhex("f2")
                ),
                Address("0x896e9dc41224489ed98380921ef0aeac66115d7b"): Account(
                    code=bytes.fromhex("f0")
                ),
                Address("0xa20eb455e7760ed71bec79457e424daff092563c"): Account(
                    code=bytes.fromhex("fb")
                ),
                Address("0xb9867e4b38bdba52f6f5bf999e4fad76a1f240b3"): Account(
                    code=bytes.fromhex("f8")
                ),
                Address("0xc24ed098dac1dd9979547cda3f5ba5aa819e0fe7"): Account(
                    code=bytes.fromhex("f5")
                ),
                Address("0xdb906979390d6688f88c0e5f8152d1b91567669d"): Account(
                    code=bytes.fromhex("fd")
                ),
                Address("0xdfff98a75e634eef4477c7df52ff28a8c7d9c6ed"): Account(
                    code=bytes.fromhex("f7")
                ),
                Address("0xe1dda7a783449dbd9dcef8401bfd074560243337"): Account(
                    code=bytes.fromhex("f6")
                ),
                Address("0xe6aea598fc28c34b486a623adb5d113444522a81"): Account(
                    code=bytes.fromhex("f1")
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(EXPECT_ENTRIES, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=contract,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        value=TX_VALUE[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
