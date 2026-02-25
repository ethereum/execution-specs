"""
Ported from:
tests/static/state_tests/stRandom/randomStatetest159Filler.json

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
    origin
    timestamp
    push1 0xe1
    push19 0xacf6051580ff4e3ba75da449e7ab2b705cf758
    push20 0xb252caf4b51def86cf4988747e4b77d541c09d31
    push11 0xcfebf3871d3a1944a5b975
    push8 0x0f11d63a7d9c9b49
    push22 0x0a0734d7313f746ba5fba6f3ff04148f4f39e4a28cc2
    push18 0xe1ae0b89f2ad1413af2317c6a9628006d415
    push29 0xdf7a3f30103f20611fe88431b16a79be995278aec271b56bc32543196c
    push6 0x0621b66f1bfc
    push18 0x8c0d9360cfb17a079aeca76a0b08cb4f0e57
    dup10
    timestamp
    push11 0x6a26c3bef3710be80e4d64
    push2 0x35f2
    push1 0x76
    log1
    push25 0xe17952f1667fa85f3b72ffa4c95bda9db87e2b8409a9b1c9e2
    push20 0x46e5b9a49fd3689f943925eb4618577675acf6bf
    ... (25 more instructions)
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
    ["tests/static/state_tests/stRandom/randomStatetest159Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.pre_alloc_mutable
def test_random_statetest159(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x4f3f701464972e74606d6ea82d4d3080599a0e79")
    sender = Address("0x2e3d0156d2b99a6eacba540c55f423c8f5a33143")
    contract = Address("0xbadab8ec78e07cdbb4b25f913769fea51e5a9c2a")

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
        Op.ORIGIN + Op.TIMESTAMP + Op.PUSH1[0xe1]
        + Op.PUSH19[0xacf6051580ff4e3ba75da449e7ab2b705cf758]
        + Op.PUSH20[0xb252caf4b51def86cf4988747e4b77d541c09d31]
        + Op.PUSH11[0xcfebf3871d3a1944a5b975] + Op.PUSH8[0xf11d63a7d9c9b49]
        + Op.PUSH22[0xa0734d7313f746ba5fba6f3ff04148f4f39e4a28cc2]
        + Op.PUSH18[0xe1ae0b89f2ad1413af2317c6a9628006d415]
        + Op.PUSH29[0xdf7a3f30103f20611fe88431b16a79be995278aec271b56bc32543196c]
        + Op.PUSH6[0x621b66f1bfc] + Op.PUSH18[0x8c0d9360cfb17a079aeca76a0b08cb4f0e57]
        + Op.DUP10 + Op.TIMESTAMP + Op.PUSH11[0x6a26c3bef3710be80e4d64]
        + Op.PUSH2[0x35f2] + Op.PUSH1[0x76] + Op.LOG1
        + Op.PUSH25[0xe17952f1667fa85f3b72ffa4c95bda9db87e2b8409a9b1c9e2]
        + Op.PUSH20[0x46e5b9a49fd3689f943925eb4618577675acf6bf]
        + Op.PUSH28[0x1b665940c32ef9086a95914496bc8bb76245fa2dc9cd3e29618e5689]
        + Op.PUSH7[0xb2893ecd2e8476] + Op.PUSH11[0x8cf184a772e70b3e042b95] + Op.DUP5
        + Op.PUSH1[0x1e] + Op.PUSH1[0xb] + Op.PUSH1[0x7] + Op.PUSH1[0x13]
        + Op.PUSH4[0x4b1e2f2] + Op.PUSH20[0xbadab8ec78e07cdbb4b25f913769fea51e5a9c2a]
        + Op.PUSH4[0x39570738] + Op.CALL + Op.PUSH14[0xf327f570c11aa84a7a5480b98c51]
        + Op.PUSH22[0xcbd00120239df2d03db2fdd9c233df848ead9d3c84d4] + Op.SSTORE
        + Op.PUSH16[0x6030a17e0f41dfce8be36a92b0d5e0d6]
        + Op.PUSH27[0x71c146187edefc7923a8aad22ca228ecee824c2d7c237ace7e52fd]
        + Op.PUSH3[0xbd6496] + Op.PUSH3[0xa4fe5f]
        + Op.PUSH25[0xa0b34d84a28c14c9fea0f18d1d55870173546b3b99e17cae46]
        + Op.PUSH31[0x2f1667b7c9445b11382bf9d7ff632d1ccdc973ba913d9ebbb219ac7aa0f3b5]
        + Op.PUSH26[0xcaa81065e433d2b8cf8cbfb998ec52fe1eaea6d87bc7728315cc]
        + Op.PUSH6[0x3ccf90494891] + Op.DUP8 + Op.COINBASE
    ),
    )

    tx = Transaction(
        secret_key=Hash(
            "0xb1f4cbc3a50042184425a6f9e996d0910f7ba879457ce5dac5c71e498ad3c005"
        ),
        to=contract,
        data=bytes.fromhex(
            "712b835f3d9d2bd711b82bc3789135c9552a3962223b777f55a33e73998ad2f06a4ed6f2"
            "5fc8856c8a525749b27c6ad568ed749589e17633797a16e71f79b4ef7d8aaf5252de3ab7"
            "71d75b7888230935e2229a77019eb0de19bf8ce156f43713d4e7fc7c8e4a05eb7055bfcc"
            "74d63886a235d3195ec4ffb5b8d0e2981d360ab96470716c3480ed32bf1d810d463fee63"
            "f646c5d23572f2e778741514e9d2ddcda7c7311236f8fc564c6459f2044db767566340f1"
            "15b2161c6c58dca4273276ab7dba59a8f7837bf38e2015040e0729abbead0f19b1cdc778"
            "a8e61745a96c3e4f4597566f4597629c6bfddff7c6b18ba01f163a6b65a66bbfa71fb76a"
            "ccc5decebf659df24d36b38e70fe2db90ba399950f4d2d3d08f96436f19563b113bc7920"
            "6663747a4f9f4bbf7319ef422e02dc9d5b8a0aa64e2e5b106c5417559c69c67bd576141c"
            "2a77da9a695bc048023ce2e47da6a3a27314e6991ebcc4fa88351f556caea7aeacbe4b85"
            "8d7c11d1ff9c90ce3ee7a294a8413e8a5b2b1ccc42328418739d2df3584249817040e86e"
            "243c89afb2608b9b32380916ca3d656a1d839af675f3768808b0d0c6811c472a67e9be5d"
            "fbee8a030e5bbcf28c327338b6bd2dd7e091d3d38d9de8e3bddab3afa5f2137180693f02"
            "159392a9ed8ce9213f4ee0908279692e61162f1e9695507c8f6aa90dc83ee13fbd09ed79"
            "dc7b1c7d54d52e4a0c4e4bf10760f3c845556086393fa12177a43230b0fc7994cdf997c3"
            "43261e41c8a45ae19aa4ece5f45bc15dcb82c2bc436a9619e2eb92ae524b6df5ad7cc653"
            "40247d3475a2201d93c64bfb9a1e40d5610f512588865e49183ff9617d21896e1be033b4"
            "2b4f21d5ecb6fea5f9fbed7d1554d470c21e1608c1a10ab043396c4076460fb57a54e9f9"
            "f708b5ee060c65e9c9ebed92d33960cf6bfa527276b5263aa69f84387464e0318ce3bd82"
            "632ca685ac74e4f0b09a9f8e6d7b40bfb9d53bddefd5bad10f40b972dd05b8617f4e892e"
            "f5a7f911a891213690d15f69429e9601dae799c9fd8a6c4c562cd8adfed3855eb4e661a6"
            "63d96255a76b91d63a23edfc368d558c89287d0b88c712797e6fb21f4a84c6407a61a713"
            "c1ba9d957622fe80be46092751640e498de7687a828b2ff6b864fb279ea72f1e53c3b584"
            "8c1fd8b9533fc2772829b26881802082d00eb7ca786f7446a0f860299c628bc20e5deefd"
            "8b8360897931a41e6ff3d9f9554552fa142eb6c03a1683933c3f0cdcd9b7dc73410aee35"
            "eecfe12e2ae69036a27ae906232544439d735b8a404c30cae29e5fa56924e7b036f8b66b"
            "8e9970dd8113a8188b654f1cb648d8300f20b08869b0625d10dbb1d8db409d64e141c19b"
            "2f83"
        ),
        gas_limit=1661465041,
        gas_price=10,
        nonce=0,
        value=614929711,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
