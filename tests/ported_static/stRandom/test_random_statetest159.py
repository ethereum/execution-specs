"""
Test_random_statetest159.

Ported from:
state_tests/stRandom/randomStatetest159Filler.json
"""

import pytest
from execution_testing import (
    EOA,
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
    ["state_tests/stRandom/randomStatetest159Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.pre_alloc_mutable
def test_random_statetest159(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_random_statetest159."""
    coinbase = Address(0x4F3F701464972E74606D6EA82D4D3080599A0E79)
    sender = EOA(
        key=0xB1F4CBC3A50042184425A6F9E996D0910F7BA879457CE5DAC5C71E498AD3C005
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    # Source: raw
    # 0x324260e172acf6051580ff4e3ba75da449e7ab2b705cf75873b252caf4b51def86cf4988747e4b77d541c09d316acfebf3871d3a1944a5b975670f11d63a7d9c9b49750a0734d7313f746ba5fba6f3ff04148f4f39e4a28cc271e1ae0b89f2ad1413af2317c6a9628006d4157cdf7a3f30103f20611fe88431b16a79be995278aec271b56bc32543196c650621b66f1bfc718c0d9360cfb17a079aeca76a0b08cb4f0e5789426a6a26c3bef3710be80e4d646135f26076a178e17952f1667fa85f3b72ffa4c95bda9db87e2b8409a9b1c9e27346e5b9a49fd3689f943925eb4618577675acf6bf7b1b665940c32ef9086a95914496bc8bb76245fa2dc9cd3e29618e568966b2893ecd2e84766a8cf184a772e70b3e042b9584601e600b600760136304b1e2f273<contract:target:0x095e7baea6a6c7c4c2dfeb977efac326af552d87>6339570738f16df327f570c11aa84a7a5480b98c5175cbd00120239df2d03db2fdd9c233df848ead9d3c84d4556f6030a17e0f41dfce8be36a92b0d5e0d67a71c146187edefc7923a8aad22ca228ecee824c2d7c237ace7e52fd62bd649662a4fe5f78a0b34d84a28c14c9fea0f18d1d55870173546b3b99e17cae467e2f1667b7c9445b11382bf9d7ff632d1ccdc973ba913d9ebbb219ac7aa0f3b579caa81065e433d2b8cf8cbfb998ec52fe1eaea6d87bc7728315cc653ccf904948918741  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.ORIGIN
        + Op.TIMESTAMP
        + Op.PUSH1[0xE1]
        + Op.PUSH19[0xACF6051580FF4E3BA75DA449E7AB2B705CF758]
        + Op.PUSH20[0xB252CAF4B51DEF86CF4988747E4B77D541C09D31]
        + Op.PUSH11[0xCFEBF3871D3A1944A5B975]
        + Op.PUSH8[0xF11D63A7D9C9B49]
        + Op.PUSH22[0xA0734D7313F746BA5FBA6F3FF04148F4F39E4A28CC2]
        + Op.PUSH18[0xE1AE0B89F2AD1413AF2317C6A9628006D415]
        + Op.PUSH29[
            0xDF7A3F30103F20611FE88431B16A79BE995278AEC271B56BC32543196C
        ]
        + Op.PUSH6[0x621B66F1BFC]
        + Op.PUSH18[0x8C0D9360CFB17A079AECA76A0B08CB4F0E57]
        + Op.DUP10
        + Op.TIMESTAMP
        + Op.LOG1(offset=0x76, size=0x35F2, topic_1=0x6A26C3BEF3710BE80E4D64)
        + Op.PUSH25[0xE17952F1667FA85F3B72FFA4C95BDA9DB87E2B8409A9B1C9E2]
        + Op.PUSH20[0x46E5B9A49FD3689F943925EB4618577675ACF6BF]
        + Op.PUSH28[0x1B665940C32EF9086A95914496BC8BB76245FA2DC9CD3E29618E5689]
        + Op.PUSH7[0xB2893ECD2E8476]
        + Op.PUSH11[0x8CF184A772E70B3E042B95]
        + Op.DUP5
        + Op.CALL(
            gas=0x39570738,
            address=0xBADAB8EC78E07CDBB4B25F913769FEA51E5A9C2A,
            value=0x4B1E2F2,
            args_offset=0x13,
            args_size=0x7,
            ret_offset=0xB,
            ret_size=0x1E,
        )
        + Op.SSTORE(
            key=0xCBD00120239DF2D03DB2FDD9C233DF848EAD9D3C84D4,
            value=0xF327F570C11AA84A7A5480B98C51,
        )
        + Op.PUSH16[0x6030A17E0F41DFCE8BE36A92B0D5E0D6]
        + Op.PUSH27[0x71C146187EDEFC7923A8AAD22CA228ECEE824C2D7C237ACE7E52FD]
        + Op.PUSH3[0xBD6496]
        + Op.PUSH3[0xA4FE5F]
        + Op.PUSH25[0xA0B34D84A28C14C9FEA0F18D1D55870173546B3B99E17CAE46]
        + Op.PUSH31[
            0x2F1667B7C9445B11382BF9D7FF632D1CCDC973BA913D9EBBB219AC7AA0F3B5
        ]
        + Op.PUSH26[0xCAA81065E433D2B8CF8CBFB998EC52FE1EAEA6D87BC7728315CC]
        + Op.PUSH6[0x3CCF90494891]
        + Op.DUP8
        + Op.COINBASE,
        nonce=0,
        address=Address(0xBADAB8EC78E07CDBB4B25F913769FEA51E5A9C2A),  # noqa: E501
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
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(
            "712b835f3d9d2bd711b82bc3789135c9552a3962223b777f55a33e73998ad2f06a4ed6f25fc8856c8a525749b27c6ad568ed749589e17633797a16e71f79b4ef7d8aaf5252de3ab771d75b7888230935e2229a77019eb0de19bf8ce156f43713d4e7fc7c8e4a05eb7055bfcc74d63886a235d3195ec4ffb5b8d0e2981d360ab96470716c3480ed32bf1d810d463fee63f646c5d23572f2e778741514e9d2ddcda7c7311236f8fc564c6459f2044db767566340f115b2161c6c58dca4273276ab7dba59a8f7837bf38e2015040e0729abbead0f19b1cdc778a8e61745a96c3e4f4597566f4597629c6bfddff7c6b18ba01f163a6b65a66bbfa71fb76accc5decebf659df24d36b38e70fe2db90ba399950f4d2d3d08f96436f19563b113bc79206663747a4f9f4bbf7319ef422e02dc9d5b8a0aa64e2e5b106c5417559c69c67bd576141c2a77da9a695bc048023ce2e47da6a3a27314e6991ebcc4fa88351f556caea7aeacbe4b858d7c11d1ff9c90ce3ee7a294a8413e8a5b2b1ccc42328418739d2df3584249817040e86e243c89afb2608b9b32380916ca3d656a1d839af675f3768808b0d0c6811c472a67e9be5dfbee8a030e5bbcf28c327338b6bd2dd7e091d3d38d9de8e3bddab3afa5f2137180693f02159392a9ed8ce9213f4ee0908279692e61162f1e9695507c8f6aa90dc83ee13fbd09ed79dc7b1c7d54d52e4a0c4e4bf10760f3c845556086393fa12177a43230b0fc7994cdf997c343261e41c8a45ae19aa4ece5f45bc15dcb82c2bc436a9619e2eb92ae524b6df5ad7cc65340247d3475a2201d93c64bfb9a1e40d5610f512588865e49183ff9617d21896e1be033b42b4f21d5ecb6fea5f9fbed7d1554d470c21e1608c1a10ab043396c4076460fb57a54e9f9f708b5ee060c65e9c9ebed92d33960cf6bfa527276b5263aa69f84387464e0318ce3bd82632ca685ac74e4f0b09a9f8e6d7b40bfb9d53bddefd5bad10f40b972dd05b8617f4e892ef5a7f911a891213690d15f69429e9601dae799c9fd8a6c4c562cd8adfed3855eb4e661a663d96255a76b91d63a23edfc368d558c89287d0b88c712797e6fb21f4a84c6407a61a713c1ba9d957622fe80be46092751640e498de7687a828b2ff6b864fb279ea72f1e53c3b5848c1fd8b9533fc2772829b26881802082d00eb7ca786f7446a0f860299c628bc20e5deefd8b8360897931a41e6ff3d9f9554552fa142eb6c03a1683933c3f0cdcd9b7dc73410aee35eecfe12e2ae69036a27ae906232544439d735b8a404c30cae29e5fa56924e7b036f8b66b8e9970dd8113a8188b654f1cb648d8300f20b08869b0625d10dbb1d8db409d64e141c19b2f83"  # noqa: E501
        ),
        gas_limit=1661465041,
        value=0x24A7152F,
    )

    post = {
        target: Account(
            storage={
                0xCBD00120239DF2D03DB2FDD9C233DF848EAD9D3C84D4: 0xF327F570C11AA84A7A5480B98C51,  # noqa: E501
            },
            nonce=0,
        ),
        coinbase: Account(storage={}, nonce=0),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
