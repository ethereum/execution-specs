"""
Test_random_statetest636.

Ported from:
state_tests/stRandom2/randomStatetest636Filler.json
"""

import pytest
from execution_testing import (
    Account,
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
    ["state_tests/stRandom2/randomStatetest636Filler.json"],
)
@pytest.mark.valid_from("Cancun")
def test_random_statetest636(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_random_statetest636."""
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    coinbase = pre.deploy_contract(
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
    )
    target = pre.deploy_contract(
        code=Op.LOG1(
            offset=0xAF1C,
            size=0x75,
            topic_1=0x619921C0750AC3268E7A6703CA2BF6C43308E6FC36,
        )
        + Op.PUSH14[0xB843F7A2E05BFC2E46AFC179930B]
        + Op.PUSH27[0x8724A04F9F561BDC65BBA0AD5797DDE0A28D5E8ACA56E1510B724F]
        + Op.PUSH8[0x6A6D33DEE473D746]
        + Op.PUSH5[0x561E49E3D8]
        + Op.PUSH4[0x38C8DCF2]
        + Op.PUSH1[0xF0]
        + Op.PUSH13[0xBFA6283966D2D0F2591F54088E]
        + Op.PUSH16[0x36545C0D90FCDEA10D5629629FFB1B16]
        + Op.PUSH3[0x6C339F]
        + Op.PUSH5[0x90829F1B16]
        + Op.PUSH22[0xF0F2F62B0B7C9D3F070FAFD53F99F90F31E19E81D3DB]
        + Op.PUSH9[0x8929213E34AFFC4111]
        + Op.PUSH15[0x6AE6F54AD5C2062B27A9FBEC78A52F]
        + Op.PUSH27[0x26C6347408631A6C0EFCF33FE576953A4043E846B686471403F38A]
        + Op.PUSH2[0x5A0A]
        + Op.DUP15
        + Op.CALL(
            gas=0x314BC0FE,
            address=Op.ADDRESS,
            value=0x1019A51,
            args_offset=0x14,
            args_size=0xE,
            ret_offset=0xA,
            ret_size=0x1D,
        )
        + Op.PUSH1[0xC]
        + Op.PUSH31[
            0xB69785D3593D3A8552018A4FABA5B591975E8B8056EBC01F5CE5F5F7C04ECA
        ]
        + Op.SWAP1
        + Op.CALLDATALOAD(offset=0xB458A8)
        + Op.SSTORE(key=0x3C4D8F92F8C27517F0ADDD45E050BFCF, value=0x9BE8FBAA90)
        + Op.PUSH26[0x2D8BF87C39D39ED9B1EF6C8C070D8DA4A624CE548B37D03AE810]
        + Op.PUSH29[
            0xA6DA49BE4ADFFC9F5AE896C52B936A18BED4BD9FCBAE531274706E9E9B
        ]
        + Op.SWAP1
        + Op.ADDRESS
        + Op.PUSH2[0x9A40]
        + Op.PUSH18[0x4BB4B22E7BEF8CF7B01551327188EE4BB624]
        + Op.PUSH18[0x18D0E95549A92F7DD9305484CC054E5F206D]
        + Op.PUSH17[0xD008699A85896061427B05AE2A7F16230F]
        + Op.PUSH7[0xAB4DD548E03B09]
        + Op.PUSH19[0x10F5AFFF39A4F9A90E55E91584E86629F3E87]
        + Op.PUSH22[0xF53DA16FCEEDD834103A50DBE72A6634E4DBF374C70E]
        + Op.PUSH12[0xD041628DC8B30DE3C3D7AA0E]
        + Op.PUSH28[0xB48DF927C78ED30B286E249C2CBE79FB55956F492E413E771D0CD63F]
        + Op.PUSH20[0x57AB1E9A38026A4BA9278427812728699A2C7471]
        + Op.DUP10,
    )

    env = Environment(fee_recipient=coinbase, prev_randao=0x20000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(
            "648ae7baf084600e60746edc292e4f932e5d92d41f0bef49fc6b696d03a44c705cb4daaf5160107d58356b0c4e1a7d81fb0b606143c7db58d8147776c02745b7de14b2c388e49568e963334e695b39de93766519c9912b2dccb22bb3bd486cdf043cbc5c0cd3b4a35f6addc01cb4ad9b448c0c60ff6c78c1acc568b086c8181a90b01f613e5e6116e776e8d170f52005efeb96d06594b7477815ea249e6143aaee6798a00d9dbba0552a73cd878ec8872e0e494df0325b92e8c7753a084c6b9763c56059eb608978797530a734a7ced61643b84aece9a39344fab3c6363d62631369ff8d931e17c50dcadb1f72256d2bcfd07e62b68627374ae05b8ff70a238f6b8717aebdaa6cd0696889d903742f20f313a8e4bcb5efae0edcbb74f41e2027dc90b56ee50a7c151872c3f01c0746579073c26c78e58ca65d93cd6c945401024b70fae5f6e17c1bc9636bd85c6c721b77f39c71e417a9bc43cf7288a2888f33b863c22e5e606ef703db601f52cf73b09b88fe1772d6693064e95ea20aa3da12c76fc929d6982f7ae98c71958c5fdd80f52a8d673027f0fa96116b85636464219d046962e9e728f947cc66e8a58061111b752dbc3bbd70bf3fa2e463969371f089c8226cb217fcf86fed7c5c87ada364a13ca107785a1e76d56edd7b1f02caac7915e522478f790322601868ed8a345ba615388b5d77d405d62f0abd72ed81f218f27c6ee6a6cde612b9c528d4107c25f6d842f8d91a37f4f098e3f552a5ce3c14d301fd1a0c7711f831c8c07197a419447c10662351b792bb34eef76c6f5d66414b182911d942896b1bb156c0ba37a9bfe4420bc17ddfe7be8daeabb37222d4ae081dd889cb787c9bf801b07e186f274a70549a04"  # noqa: E501
        ),
        value=0x74FF9009,
    )

    post = {
        target: Account(
            storage={0x3C4D8F92F8C27517F0ADDD45E050BFCF: 0x9BE8FBAA90},
            nonce=1,
        ),
        coinbase: Account(storage={}, nonce=1),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
