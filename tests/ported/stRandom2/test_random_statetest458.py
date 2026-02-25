"""
Ported from:
tests/static/state_tests/stRandom2/randomStatetest458Filler.json

contract code:
    push23 0x89747fb3520231748bbe5eb9617666e630019e3e84ce71
    push26 0xc5d83b7e36050e5c05623956e599f54eb56213e4f96f69f402cd
    push20 0xe13c366095a3fe56bdd6a815d9ba23f3a9729bc4
    push3 0x385c69
    push31 0xd9f24192c949e33ff7ed256c84979d70148b8fd8a62438ca053de264227145
    push14 0xde46ce78cf7c6d1d2cc48eee658a
    push20 0xad9f9ca1e550720490e2d0769e0a429773e42fc9
    push6 0xea1030f6c078
    push28 0x4e7bc4915150a99fc758d3373561d8917c4c7d605f0cd8d2203f4d69
    push1 0x61
    swap9
    number
    push21 0x29e2f2d2bf742b28760a9c0ab51203d0c5d5b9e16d
    push21 0xce0428945aaff2d0f99240a901d3233bd04e366c36
    push27 0xb93ecea0c206fbf01084254636df9c1f308c7d6875d5d5d37f3ce2
    push26 0x89e39048f175f0d2dc49eaa86530def7ab70553f5d3904c843b5
    push20 0x6025e321e7e2ab92af570e5b3bef4014c54e6531
    push12 0xb546eb8906f155f7b9405326
    push21 0x0104d8f5d98dc97ac374ad0c58f4385e086891b9b2
    push6 0x7e982eb15a36
    ... (63 more instructions)

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
    ["tests/static/state_tests/stRandom2/randomStatetest458Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.pre_alloc_mutable
def test_random_statetest458(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x4f3f701464972e74606d6ea82d4d3080599a0e79")
    sender = Address("0x2e3d0156d2b99a6eacba540c55f423c8f5a33143")
    contract = Address("0x4f391713bdca6e610dea121df82ff743d96d33b6")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH23[0x89747fb3520231748bbe5eb9617666e630019e3e84ce71]
        + Op.PUSH26[0xc5d83b7e36050e5c05623956e599f54eb56213e4f96f69f402cd]
        + Op.PUSH20[0xe13c366095a3fe56bdd6a815d9ba23f3a9729bc4] + Op.PUSH3[0x385c69]
        + Op.PUSH31[0xd9f24192c949e33ff7ed256c84979d70148b8fd8a62438ca053de264227145]
        + Op.PUSH14[0xde46ce78cf7c6d1d2cc48eee658a]
        + Op.PUSH20[0xad9f9ca1e550720490e2d0769e0a429773e42fc9]
        + Op.PUSH6[0xea1030f6c078]
        + Op.PUSH28[0x4e7bc4915150a99fc758d3373561d8917c4c7d605f0cd8d2203f4d69]
        + Op.PUSH1[0x61] + Op.SWAP9 + Op.NUMBER
        + Op.PUSH21[0x29e2f2d2bf742b28760a9c0ab51203d0c5d5b9e16d]
        + Op.PUSH21[0xce0428945aaff2d0f99240a901d3233bd04e366c36]
        + Op.PUSH27[0xb93ecea0c206fbf01084254636df9c1f308c7d6875d5d5d37f3ce2]
        + Op.PUSH26[0x89e39048f175f0d2dc49eaa86530def7ab70553f5d3904c843b5]
        + Op.PUSH20[0x6025e321e7e2ab92af570e5b3bef4014c54e6531]
        + Op.PUSH12[0xb546eb8906f155f7b9405326]
        + Op.PUSH21[0x104d8f5d98dc97ac374ad0c58f4385e086891b9b2]
        + Op.PUSH6[0x7e982eb15a36]
        + Op.PUSH31[0xab6683b51ea9f219abae5ca39f669a1a88a82e14efd4192a3edbe04a12d356]
        + Op.PUSH26[0xcf6338130d67f37c324464d16cc866be846b0304ef9fd3c6611e]
        + Op.PUSH13[0xdf1277d65f6b2a58ffb61ba979]
        + Op.PUSH21[0xb8df72816602071e979e6029c9307d718ffdc70f3]
        + Op.PUSH31[0xa0019353c06b0fb56d8e3738dfdb18418e952092e8625b51749f276cc6ae41]
        + Op.PUSH11[0x85bd070c61e65240d8c271] + Op.SWAP13
        + Op.PUSH23[0xb0420f84ece41c9be0f93d4f30581c28f6976839516393]
        + Op.PUSH32[0x95b86da30fa76b6937870245d9250e06b6e07dffea8f849a37647378dd59ac83]
        + Op.PUSH6[0xa37dd908eea2] + Op.PUSH12[0xe2f53375e1dbee32ecaa7e95]
        + Op.PUSH31[0xace8c6f0883e4ef830485bd43b2b7851a0b11497f752d3ee4560e312a7a91b]
        + Op.PUSH28[0x2a88c109737c92feb7807d481ac3fd823f038c4ba82df40a60982a7c]
        + Op.PUSH27[0x6f6ba2cb95233c257b30e1c9d3c84aa37b6f4268fec34fb9eef1f8]
        + Op.PUSH1[0x2e] + Op.PUSH11[0x7bf1ebfa162680b57af09f]
        + Op.PUSH27[0x7fc584055ff32d68a92e59ddaf20bcaaaa70d5970fd71c04cdbab4]
        + Op.PUSH13[0xf86e566e870664b6df2c686134]
        + Op.PUSH28[0x2a3886788bbebbd03cbb51ed29357f699c8b974c61528a0423f67a83]
        + Op.PUSH28[0xfab83afa78a0bff70a653ea0f398f73632d5e3bea0a31115d65486fb]
        + Op.PUSH14[0x667110448e0208264a3f76f35972] + Op.PUSH7[0x6e7aa7339f23b0]
        + Op.DUP15 + Op.PUSH1[0x28] + Op.PUSH2[0x6337] + Op.LOG0 + Op.CALLDATASIZE
        + Op.PUSH1[0x16] + Op.PUSH1[0x1d] + Op.PUSH1[0x14] + Op.PUSH1[0xb]
        + Op.PUSH4[0xe6db38e] + Op.PUSH20[0x4f391713bdca6e610dea121df82ff743d96d33b6]
        + Op.PUSH4[0x5706352b] + Op.CALL + Op.PUSH10[0x5bb9e53d5ad3ba1191ea]
        + Op.PUSH6[0xae1880d46c68]
        + Op.PUSH23[0x5148e427a09d40172dbdd5fc72fffb1443080a39a0ee7]
        + Op.PUSH32[0xeed9ddc9050affce41d68c34ad97c484f204a987bcfaf46b9fa4a9ed2dad3738]
        + Op.PUSH24[0x1a3cf86b43f303a8db8cde3ed8a40ae35574b9084f4cab88]
        + Op.PUSH17[0x1d150e628d9b2a33e71c8f9fb0ce9e7286] + Op.PUSH3[0x576917]
        + Op.PUSH23[0xf999b7ddf64f22532351bd34743e08facd1acc94b0d6b5]
        + Op.PUSH12[0xf97491d5ed9d726af684d1a4]
        + Op.PUSH27[0xbcb243b7c29d12a315e939f70af8d2617df63567c3bc56c16609a2]
        + Op.PUSH25[0x71af77631fe1ccaa0d15f8da9bd9a712a544abb92b925b1d75]
        + Op.PUSH2[0xfced] + Op.PUSH1[0xb0] + Op.SWAP12
        + Op.PUSH12[0x22f2121b105a65a209e151b7]
        + Op.PUSH12[0x31be481d57353d10a1d968ca]
        + Op.PUSH27[0x185495a8a2935571a0d17443a327bf11cb421baca9064bc4e4497c]
        + Op.PUSH30[0x4c486c40082cc2d01b3f6023b726de95ac2ad53ae0b731d741676338181e]
        + Op.PUSH7[0xc8ac8daf0d5477] + Op.PUSH9[0x27987e79d9f617c51f]
        + Op.PUSH16[0x4b87cf8fee734c99e5e3fc2e37f17e62]
        + Op.PUSH13[0xbfd1195157215d10fa39b4b094]
        + Op.PUSH29[0x3339139b280c0b042da7ec93a24416d5c52e0ba21ec9d39d6fbcd3d742]
        + Op.PUSH7[0x580eef6ca9bb9d]
        + Op.PUSH23[0xbb4dc441f3d6d0cf38307b505251deea82ab39f9ccd17a]
        + Op.PUSH6[0x7bf16b38640] + Op.PUSH8[0x9c22f2134e8258f7] + Op.SWAP12
    ),
    )
    pre[coinbase] = Account(
        balance=46,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.SLOAD + Op.ISZERO + Op.PUSH1[0x9]
        + Op.JUMPI + Op.STOP + Op.JUMPDEST + Op.PUSH1[0x20] + Op.CALLDATALOAD
        + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.SSTORE
    ),
    )

    tx = Transaction(
        secret_key=Hash(
            "0xb1f4cbc3a50042184425a6f9e996d0910f7ba879457ce5dac5c71e498ad3c005"
        ),
        to=contract,
        data=bytes.fromhex(
            "6cff89fd2305930f9a427748410969e86bfeabd7748df8c60e9075e32f95abb7b73e260f"
            "c345efb09ac919b22eb90402ff6b737a79722d83372adc70ef947e3a28e6dda50601f52f"
            "ea5b45a7294d90ea73bb64de313534dce604ebc4a22c7519bd1a15bc91aca303759ffdfc"
            "849b53ca82e03b1df66d1ede5b09b519084802396f8849817328c82f591c11d4b40c0653"
            "e1ec91398ca9a1a6b872165aac3c0567020253bc3f5221edb93cbbd87c7486136d4f5649"
            "a5f1ad8808013f373cbffc6c40c8707f2e0449a9ce33beba84b4974ed62803f8dd900ba3"
            "b47d3cc55ba503f903701f1188"
        ),
        gas_limit=1630523086,
        gas_price=10,
        nonce=0,
        value=2131886598,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
