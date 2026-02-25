"""
Ported from:
tests/static/state_tests/stRandom/randomStatetest205Filler.json

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
    caller
    push1 0xb2
    push2 0xedef
    log0
    origin
    push16 0xdc74d570982966277b49cdb30a453fa0
    push13 0x34a7423da44ba2d04341af08c4
    push25 0xb17a57318ab10ab43b3744333b0aa8864ac27b3fd022e38005
    push8 0x35a5fcda3e9fdc25
    push10 0x5972a076884de6d6b6b0
    push14 0xd45416c8110bae3c70576b433a46
    push19 0x777847e81823024ddd1292b929ad28e64a732b
    push21 0xc0ae1941d5936ecd35738e2f279273788f4aaf1990
    push27 0x532a6b0f117c32b6cb967aae8bdfcf86e2d4d64599986abcf65a20
    push22 0x4f5a816c58ed669138f6a0448670b906bbf1eb145ced
    dup10
    push13 0x578de5aa27769006b1a784e84b
    push4 0x16d4e60c
    push17 0x53b0b6550c70a177cb7a3e88d4e83fb189
    push27 0x09c2161ff6cc2679c178292687137854da672e316c66ef03dc9ac3
    ... (42 more instructions)
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
    ["tests/static/state_tests/stRandom/randomStatetest205Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_random_statetest205(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x4f3f701464972e74606d6ea82d4d3080599a0e79")
    sender = Address("0x2e3d0156d2b99a6eacba540c55f423c8f5a33143")
    contract = Address("0xd6c9d572b7645ecae86a7bdb66c7ae1fb04b0321")

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
        Op.CALLER + Op.PUSH1[0xb2] + Op.PUSH2[0xedef] + Op.LOG0 + Op.ORIGIN
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
        + Op.PUSH10[0xae4d38f3df618f5eeb90] + Op.DUP6 + Op.PUSH1[0x1f]
        + Op.PUSH1[0x10] + Op.PUSH1[0x8] + Op.PUSH1[0x16] + Op.PUSH4[0x2c019e2e]
        + Op.PUSH20[0xd6c9d572b7645ecae86a7bdb66c7ae1fb04b0321] + Op.PUSH3[0x6b8a0e]
        + Op.CALL + Op.PUSH26[0xe6b62e86237845e9605d61219d97c1d0145516f5355fe73384e8]
        + Op.PUSH27[0x6a87cc6d2378c81797ac3746bc562e2fd1145e14781307bc4ada39]
        + Op.PUSH20[0x2e9d0e8725fde75c5abc313c11e3238c7cd9b718]
        + Op.PUSH11[0x6a14f8d5c3cad9da533944] + Op.PUSH11[0xd1311ccc67a0691559157a]
        + Op.PUSH8[0x4825358b301ac42d]
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
        + Op.SWAP14 + Op.CALLDATASIZE
    ),
    )

    tx = Transaction(
        secret_key=Hash(
            "0xb1f4cbc3a50042184425a6f9e996d0910f7ba879457ce5dac5c71e498ad3c005"
        ),
        to=contract,
        data=bytes.fromhex(
            "74ac5e422199cb842b1fdcdef502d4142d033387c6d17fe1f03f0fc4a3c05daadf323f3b"
            "b04b7e33dbad9b32f058aa6df6d54c8d7ac95568ba4a6b33a2b0ce8d8c7480ab9e818cf8"
            "998564e6d38b92aa1ecd76aa8aff266dd266c96af419778c16a109cba6976922093e50bd"
            "a96ac1333a946574ad748ad839546ff861257bb6a41cab34045ea7335e1c9667c67424f9"
            "baf8781e79e002a233a622f41f2744c21b6baed43543e0dfb9aa81fd1050326b0ebad84f"
            "da176f3438d3a7f083"
        ),
        gas_limit=7300000,
        gas_price=10,
        nonce=0,
        value=1305713546,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
