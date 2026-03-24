"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stRandom/randomStatetest205Filler.json
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

    pre[sender] = Account(balance=0xDE0B6B3A7640000)
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.JUMPI(
                pc=0x9,
                condition=Op.ISZERO(Op.SLOAD(key=Op.CALLDATALOAD(offset=0x0))),
            )
            + Op.STOP
            + Op.JUMPDEST
            + Op.SSTORE(
                key=Op.CALLDATALOAD(offset=0x0),
                value=Op.CALLDATALOAD(offset=0x20),
            )
        ),
        balance=46,
        nonce=0,
        address=coinbase,  # noqa: E501
    )
    # Source: raw bytecode
    contract = pre.deploy_contract(
        code=(
            Op.CALLER
            + Op.LOG0(offset=0xEDEF, size=0xB2)
            + Op.ORIGIN
            + Op.PUSH16[0xDC74D570982966277B49CDB30A453FA0]
            + Op.PUSH13[0x34A7423DA44BA2D04341AF08C4]
            + Op.PUSH25[0xB17A57318AB10AB43B3744333B0AA8864AC27B3FD022E38005]
            + Op.PUSH8[0x35A5FCDA3E9FDC25]
            + Op.PUSH10[0x5972A076884DE6D6B6B0]
            + Op.PUSH14[0xD45416C8110BAE3C70576B433A46]
            + Op.PUSH19[0x777847E81823024DDD1292B929AD28E64A732B]
            + Op.PUSH21[0xC0AE1941D5936ECD35738E2F279273788F4AAF1990]
            + Op.PUSH27[
                0x532A6B0F117C32B6CB967AAE8BDFCF86E2D4D64599986ABCF65A20
            ]
            + Op.PUSH22[0x4F5A816C58ED669138F6A0448670B906BBF1EB145CED]
            + Op.DUP10
            + Op.PUSH13[0x578DE5AA27769006B1A784E84B]
            + Op.PUSH4[0x16D4E60C]
            + Op.PUSH17[0x53B0B6550C70A177CB7A3E88D4E83FB189]
            + Op.PUSH27[
                0x9C2161FF6CC2679C178292687137854DA672E316C66EF03DC9AC3
            ]
            + Op.PUSH31[
                0x8E430B7C64D1939BF67383C4BAFEB2F0471FE896B7C0E114BF6F152B266CC7  # noqa: E501
            ]
            + Op.PUSH10[0xAE4D38F3DF618F5EEB90]
            + Op.DUP6
            + Op.CALL(
                gas=0x6B8A0E,
                address=0xD6C9D572B7645ECAE86A7BDB66C7AE1FB04B0321,
                value=0x2C019E2E,
                args_offset=0x16,
                args_size=0x8,
                ret_offset=0x10,
                ret_size=0x1F,
            )
            + Op.PUSH26[0xE6B62E86237845E9605D61219D97C1D0145516F5355FE73384E8]
            + Op.PUSH27[
                0x6A87CC6D2378C81797AC3746BC562E2FD1145E14781307BC4ADA39
            ]
            + Op.PUSH20[0x2E9D0E8725FDE75C5ABC313C11E3238C7CD9B718]
            + Op.PUSH11[0x6A14F8D5C3CAD9DA533944]
            + Op.PUSH11[0xD1311CCC67A0691559157A]
            + Op.PUSH8[0x4825358B301AC42D]
            + Op.PUSH28[
                0xCAE31BEB8B0849903402175CA3740F3FD690AD66287D6BF67A98C09E
            ]
            + Op.PUSH14[0xE5717596052D30F4B9BB8046A6B6]
            + Op.PUSH31[
                0xF51B1B13C496E97BF9A2E67AECA97FA10A266F8CF22C10CC0375B514B25DE4  # noqa: E501
            ]
            + Op.PUSH7[0xA146576B2CB565]
            + Op.PUSH22[0x4EFC80D4B8AA5497AA0FB4CBAB90EE57298D322474D2]
            + Op.PUSH23[0x366E04EAB856C9F6070C80701FA30596DD0B6EA5BC38BA]
            + Op.PUSH5[0xE1D16AFF1B]
            + Op.DUP13
            + Op.PUSH2[0xCAA3]
            + Op.PUSH26[0x64465A9308DBB1465294DDCB5FA32833E4FFB049C71761ED934]
            + Op.PUSH19[0xC7E58F171C6C8B51E2EC704D34897B80466E82]
            + Op.PUSH12[0xC1CE2488511CBB1AAAD26B0]
            + Op.PUSH22[0xED5EBF070BE6E14EAA6B973423BCB2E0541307D88FF6]
            + Op.PUSH14[0x1B7E29FFFB10218CA75BF3F9957D]
            + Op.PUSH15[0xE27A0945278D5F9303B3E3F28A325A]
            + Op.PUSH32[
                0x17905F7467C4AFCBB3A43DBBD37E9591E3F5A82841EE9CB8B23F68B4572E8CD9  # noqa: E501
            ]
            + Op.PUSH14[0xF7DAACBD3AB3BD5A8F427BAF6EA]
            + Op.PUSH27[
                0xE70D98D3948EAFB74E2E4A158AC116C5219403C9073A457409C6E4
            ]
            + Op.PUSH5[0xBAE32B2C85]
            + Op.PUSH12[0x15BDA1B2176295FD1CECFE7D]
            + Op.PUSH26[0x4AB2692061AA79387004112272204198437FC78D1DBE0E8932CE]
            + Op.PUSH16[0x47828A2BF4DF47446291B99D92A90DE3]
            + Op.PUSH3[0x395458]
            + Op.SWAP14
            + Op.CALLDATASIZE
        ),
        nonce=0,
        address=Address("0xd6c9d572b7645ecae86a7bdb66c7ae1fb04b0321"),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex(
            "74ac5e422199cb842b1fdcdef502d4142d033387c6d17fe1f03f0fc4a3c05daadf323f3b"  # noqa: E501
            "b04b7e33dbad9b32f058aa6df6d54c8d7ac95568ba4a6b33a2b0ce8d8c7480ab9e818cf8"  # noqa: E501
            "998564e6d38b92aa1ecd76aa8aff266dd266c96af419778c16a109cba6976922093e50bd"  # noqa: E501
            "a96ac1333a946574ad748ad839546ff861257bb6a41cab34045ea7335e1c9667c67424f9"  # noqa: E501
            "baf8781e79e002a233a622f41f2744c21b6baed43543e0dfb9aa81fd1050326b0ebad84f"  # noqa: E501
            "da176f3438d3a7f083"
        ),
        gas_limit=7300000,
        value=1305713546,
    )

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
