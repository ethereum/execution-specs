"""
test_random_statetest205

Ported from:
state_tests/stRandom/randomStatetest205Filler.json
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
    ["state_tests/stRandom/randomStatetest205Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_random_statetest205(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_random_statetest205"""
    coinbase = Address("0x4f3f701464972e74606d6ea82d4d3080599a0e79")
    sender = EOA(
        key=0xb1f4cbc3a50042184425a6f9e996d0910f7ba879457ce5dac5c71e498ad3c005
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    # Source: raw
    # 0x3360b261edefa0326fdc74d570982966277b49cdb30a453fa06c34a7423da44ba2d04341af08c478b17a57318ab10ab43b3744333b0aa8864ac27b3fd022e380056735a5fcda3e9fdc25695972a076884de6d6b6b06dd45416c8110bae3c70576b433a4672777847e81823024ddd1292b929ad28e64a732b74c0ae1941d5936ecd35738e2f279273788f4aaf19907a532a6b0f117c32b6cb967aae8bdfcf86e2d4d64599986abcf65a20754f5a816c58ed669138f6a0448670b906bbf1eb145ced896c578de5aa27769006b1a784e84b6316d4e60c7053b0b6550c70a177cb7a3e88d4e83fb1897a09c2161ff6cc2679c178292687137854da672e316c66ef03dc9ac37e8e430b7c64d1939bf67383c4bafeb2f0471fe896b7c0e114bf6f152b266cc769ae4d38f3df618f5eeb9085601f601060086016632c019e2e73<contract:target:0x095e7baea6a6c7c4c2dfeb977efac326af552d87>626b8a0ef179e6b62e86237845e9605d61219d97c1d0145516f5355fe73384e87a6a87cc6d2378c81797ac3746bc562e2fd1145e14781307bc4ada39732e9d0e8725fde75c5abc313c11e3238c7cd9b7186a6a14f8d5c3cad9da5339446ad1311ccc67a0691559157a674825358b301ac42d7bcae31beb8b0849903402175ca3740f3fd690ad66287d6bf67a98c09e6de5717596052d30f4b9bb8046a6b67ef51b1b13c496e97bf9a2e67aeca97fa10a266f8cf22c10cc0375b514b25de466a146576b2cb565754efc80d4b8aa5497aa0fb4cbab90ee57298d322474d276366e04eab856c9f6070c80701fa30596dd0b6ea5bc38ba64e1d16aff1b8c61caa379064465a9308dbb1465294ddcb5fa32833e4ffb049c71761ed93472c7e58f171c6c8b51e2ec704d34897b80466e826b0c1ce2488511cbb1aaad26b075ed5ebf070be6e14eaa6b973423bcb2e0541307d88ff66d1b7e29fffb10218ca75bf3f9957d6ee27a0945278d5f9303b3e3f28a325a7f17905f7467c4afcbb3a43dbbd37e9591e3f5a82841ee9cb8b23f68b4572e8cd96d0f7daacbd3ab3bd5a8f427baf6ea7ae70d98d3948eafb74e2e4a158ac116c5219403c9073a457409c6e464bae32b2c856b15bda1b2176295fd1cecfe7d794ab2692061aa79387004112272204198437fc78d1dbe0e8932ce6f47828a2bf4df47446291b99d92a90de3623954589d36
    target = pre.deploy_contract(
        code=Op.CALLER + Op.LOG0(offset=0xedef, size=0xb2) + Op.ORIGIN
        + Op.PUSH16[0xdc74d570982966277b49cdb30a453fa0]
        + Op.PUSH13[0x34a7423da44ba2d04341af08c4]
        + Op.PUSH25[0xb17a57318ab10ab43b3744333b0aa8864ac27b3fd022e38005]
        + Op.PUSH8[0x35a5fcda3e9fdc25] + Op.PUSH10[0x5972a076884de6d6b6b0]
        + Op.PUSH14[0xd45416c8110bae3c70576b433a46]
        + Op.PUSH19[0x777847e81823024ddd1292b929ad28e64a732b]
        + Op.PUSH21[0xc0ae1941d5936ecd35738e2f279273788f4aaf1990]
        + Op.PUSH27[0x532a6b0f117c32b6cb967aae8bdfcf86e2d4d64599986abcf65a20]
        + Op.PUSH22[0x4f5a816c58ed669138f6a0448670b906bbf1eb145ced] + Op.DUP10
        + Op.PUSH13[0x578de5aa27769006b1a784e84b] + Op.PUSH4[0x16d4e60c]
        + Op.PUSH17[0x53b0b6550c70a177cb7a3e88d4e83fb189]
        + Op.PUSH27[0x9c2161ff6cc2679c178292687137854da672e316c66ef03dc9ac3]
        + Op.PUSH31[0x8e430b7c64d1939bf67383c4bafeb2f0471fe896b7c0e114bf6f152b266cc7]
        + Op.PUSH10[0xae4d38f3df618f5eeb90] + Op.DUP6
        + Op.CALL(gas=0x6b8a0e, address=0xd6c9d572b7645ecae86a7bdb66c7ae1fb04b0321, value=0x2c019e2e, args_offset=0x16, args_size=0x8, ret_offset=0x10, ret_size=0x1f)
        + Op.PUSH26[0xe6b62e86237845e9605d61219d97c1d0145516f5355fe73384e8]
        + Op.PUSH27[0x6a87cc6d2378c81797ac3746bc562e2fd1145e14781307bc4ada39]
        + Op.PUSH20[0x2e9d0e8725fde75c5abc313c11e3238c7cd9b718]
        + Op.PUSH11[0x6a14f8d5c3cad9da533944]
        + Op.PUSH11[0xd1311ccc67a0691559157a] + Op.PUSH8[0x4825358b301ac42d]
        + Op.PUSH28[0xcae31beb8b0849903402175ca3740f3fd690ad66287d6bf67a98c09e]
        + Op.PUSH14[0xe5717596052d30f4b9bb8046a6b6]
        + Op.PUSH31[0xf51b1b13c496e97bf9a2e67aeca97fa10a266f8cf22c10cc0375b514b25de4]
        + Op.PUSH7[0xa146576b2cb565]
        + Op.PUSH22[0x4efc80d4b8aa5497aa0fb4cbab90ee57298d322474d2]
        + Op.PUSH23[0x366e04eab856c9f6070c80701fa30596dd0b6ea5bc38ba]
        + Op.PUSH5[0xe1d16aff1b] + Op.DUP13 + Op.PUSH2[0xcaa3]
        + Op.PUSH26[0x64465a9308dbb1465294ddcb5fa32833e4ffb049c71761ed934]
        + Op.PUSH19[0xc7e58f171c6c8b51e2ec704d34897b80466e82]
        + Op.PUSH12[0xc1ce2488511cbb1aaad26b0]
        + Op.PUSH22[0xed5ebf070be6e14eaa6b973423bcb2e0541307d88ff6]
        + Op.PUSH14[0x1b7e29fffb10218ca75bf3f9957d]
        + Op.PUSH15[0xe27a0945278d5f9303b3e3f28a325a]
        + Op.PUSH32[0x17905f7467c4afcbb3a43dbbd37e9591e3f5a82841ee9cb8b23f68b4572e8cd9]
        + Op.PUSH14[0xf7daacbd3ab3bd5a8f427baf6ea]
        + Op.PUSH27[0xe70d98d3948eafb74e2e4a158ac116c5219403c9073a457409c6e4]
        + Op.PUSH5[0xbae32b2c85] + Op.PUSH12[0x15bda1b2176295fd1cecfe7d]
        + Op.PUSH26[0x4ab2692061aa79387004112272204198437fc78d1dbe0e8932ce]
        + Op.PUSH16[0x47828a2bf4df47446291b99d92a90de3] + Op.PUSH3[0x395458]
        + Op.SWAP14 + Op.CALLDATASIZE,
        nonce=0,
        address=Address("0xd6c9d572b7645ecae86a7bdb66c7ae1fb04b0321"),  # noqa: E501
    )
    # Source: raw
    # 0x6000355415600957005b60203560003555
    coinbase = pre.deploy_contract(
        code=Op.JUMPI(pc=0x9, condition=Op.ISZERO(Op.SLOAD(key=Op.CALLDATALOAD(offset=0x0))))  # noqa: E501
        + Op.STOP + Op.JUMPDEST
        + Op.SSTORE(key=Op.CALLDATALOAD(offset=0x0), value=Op.CALLDATALOAD(offset=0x20)),  # noqa: E501
        balance=46,
        nonce=0,
        address=Address("0x4f3f701464972e74606d6ea82d4d3080599a0e79"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000)


    tx = Transaction(
        sender=sender,
        to=target,
        data=bytes.fromhex("74ac5e422199cb842b1fdcdef502d4142d033387c6d17fe1f03f0fc4a3c05daadf323f3bb04b7e33dbad9b32f058aa6df6d54c8d7ac95568ba4a6b33a2b0ce8d8c7480ab9e818cf8998564e6d38b92aa1ecd76aa8aff266dd266c96af419778c16a109cba6976922093e50bda96ac1333a946574ad748ad839546ff861257bb6a41cab34045ea7335e1c9667c67424f9baf8781e79e002a233a622f41f2744c21b6baed43543e0dfb9aa81fd1050326b0ebad84fda176f3438d3a7f083"),  # noqa: E501
        gas_limit=7300000,
        value=0x4dd39b8a,
        nonce=0,
        gas_price=10,
    )

    post = {
        target: Account(storage={}, nonce=0),
        coinbase: Account(storage={}, nonce=0),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
