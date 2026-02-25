"""
Ported from:
tests/static/state_tests/stRandom2/randomStatetest636Filler.json

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
    push21 0x619921c0750ac3268e7a6703ca2bf6c43308e6fc36
    push1 0x75
    push2 0xaf1c
    log1
    push14 0xb843f7a2e05bfc2e46afc179930b
    push27 0x8724a04f9f561bdc65bba0ad5797dde0a28d5e8aca56e1510b724f
    push8 0x6a6d33dee473d746
    push5 0x561e49e3d8
    push4 0x38c8dcf2
    push1 0xf0
    push13 0xbfa6283966d2d0f2591f54088e
    push16 0x36545c0d90fcdea10d5629629ffb1b16
    push3 0x6c339f
    push5 0x90829f1b16
    push22 0xf0f2f62b0b7c9d3f070fafd53f99f90f31e19e81d3db
    push9 0x8929213e34affc4111
    push15 0x6ae6f54ad5c2062b27a9fbec78a52f
    push27 0x26c6347408631a6c0efcf33fe576953a4043e846b686471403f38a
    push2 0x5a0a
    dup15
    ... (31 more instructions)
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
    ["tests/static/state_tests/stRandom2/randomStatetest636Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.pre_alloc_mutable
def test_random_statetest636(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x4f3f701464972e74606d6ea82d4d3080599a0e79")
    sender = Address("0x2e3d0156d2b99a6eacba540c55f423c8f5a33143")
    contract = Address("0xbdc4b8af0f40b0ec2256166f7145b81cd824a868")

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
        Op.PUSH21[0x619921c0750ac3268e7a6703ca2bf6c43308e6fc36] + Op.PUSH1[0x75]
        + Op.PUSH2[0xaf1c] + Op.LOG1 + Op.PUSH14[0xb843f7a2e05bfc2e46afc179930b]
        + Op.PUSH27[0x8724a04f9f561bdc65bba0ad5797dde0a28d5e8aca56e1510b724f]
        + Op.PUSH8[0x6a6d33dee473d746] + Op.PUSH5[0x561e49e3d8] + Op.PUSH4[0x38c8dcf2]
        + Op.PUSH1[0xf0] + Op.PUSH13[0xbfa6283966d2d0f2591f54088e]
        + Op.PUSH16[0x36545c0d90fcdea10d5629629ffb1b16] + Op.PUSH3[0x6c339f]
        + Op.PUSH5[0x90829f1b16]
        + Op.PUSH22[0xf0f2f62b0b7c9d3f070fafd53f99f90f31e19e81d3db]
        + Op.PUSH9[0x8929213e34affc4111] + Op.PUSH15[0x6ae6f54ad5c2062b27a9fbec78a52f]
        + Op.PUSH27[0x26c6347408631a6c0efcf33fe576953a4043e846b686471403f38a]
        + Op.PUSH2[0x5a0a] + Op.DUP15 + Op.PUSH1[0x1d] + Op.PUSH1[0xa] + Op.PUSH1[0xe]
        + Op.PUSH1[0x14] + Op.PUSH4[0x1019a51]
        + Op.PUSH20[0xbdc4b8af0f40b0ec2256166f7145b81cd824a868] + Op.PUSH4[0x314bc0fe]
        + Op.CALL + Op.PUSH1[0xc]
        + Op.PUSH31[0xb69785d3593d3a8552018a4faba5b591975e8b8056ebc01f5ce5f5f7c04eca]
        + Op.SWAP1 + Op.PUSH3[0xb458a8] + Op.CALLDATALOAD + Op.PUSH5[0x9be8fbaa90]
        + Op.PUSH16[0x3c4d8f92f8c27517f0addd45e050bfcf] + Op.SSTORE
        + Op.PUSH26[0x2d8bf87c39d39ed9b1ef6c8c070d8da4a624ce548b37d03ae810]
        + Op.PUSH29[0xa6da49be4adffc9f5ae896c52b936a18bed4bd9fcbae531274706e9e9b]
        + Op.SWAP1 + Op.ADDRESS + Op.PUSH2[0x9a40]
        + Op.PUSH18[0x4bb4b22e7bef8cf7b01551327188ee4bb624]
        + Op.PUSH18[0x18d0e95549a92f7dd9305484cc054e5f206d]
        + Op.PUSH17[0xd008699a85896061427b05ae2a7f16230f] + Op.PUSH7[0xab4dd548e03b09]
        + Op.PUSH19[0x10f5afff39a4f9a90e55e91584e86629f3e87]
        + Op.PUSH22[0xf53da16fceedd834103a50dbe72a6634e4dbf374c70e]
        + Op.PUSH12[0xd041628dc8b30de3c3d7aa0e]
        + Op.PUSH28[0xb48df927c78ed30b286e249c2cbe79fb55956f492e413e771d0cd63f]
        + Op.PUSH20[0x57ab1e9a38026a4ba9278427812728699a2c7471] + Op.DUP10
    ),
    )

    tx = Transaction(
        secret_key=Hash(
            "0xb1f4cbc3a50042184425a6f9e996d0910f7ba879457ce5dac5c71e498ad3c005"
        ),
        to=contract,
        data=bytes.fromhex(
            "648ae7baf084600e60746edc292e4f932e5d92d41f0bef49fc6b696d03a44c705cb4daaf"
            "5160107d58356b0c4e1a7d81fb0b606143c7db58d8147776c02745b7de14b2c388e49568"
            "e963334e695b39de93766519c9912b2dccb22bb3bd486cdf043cbc5c0cd3b4a35f6addc0"
            "1cb4ad9b448c0c60ff6c78c1acc568b086c8181a90b01f613e5e6116e776e8d170f52005"
            "efeb96d06594b7477815ea249e6143aaee6798a00d9dbba0552a73cd878ec8872e0e494d"
            "f0325b92e8c7753a084c6b9763c56059eb608978797530a734a7ced61643b84aece9a393"
            "44fab3c6363d62631369ff8d931e17c50dcadb1f72256d2bcfd07e62b68627374ae05b8f"
            "f70a238f6b8717aebdaa6cd0696889d903742f20f313a8e4bcb5efae0edcbb74f41e2027"
            "dc90b56ee50a7c151872c3f01c0746579073c26c78e58ca65d93cd6c945401024b70fae5"
            "f6e17c1bc9636bd85c6c721b77f39c71e417a9bc43cf7288a2888f33b863c22e5e606ef7"
            "03db601f52cf73b09b88fe1772d6693064e95ea20aa3da12c76fc929d6982f7ae98c7195"
            "8c5fdd80f52a8d673027f0fa96116b85636464219d046962e9e728f947cc66e8a5806111"
            "1b752dbc3bbd70bf3fa2e463969371f089c8226cb217fcf86fed7c5c87ada364a13ca107"
            "785a1e76d56edd7b1f02caac7915e522478f790322601868ed8a345ba615388b5d77d405"
            "d62f0abd72ed81f218f27c6ee6a6cde612b9c528d4107c25f6d842f8d91a37f4f098e3f5"
            "52a5ce3c14d301fd1a0c7711f831c8c07197a419447c10662351b792bb34eef76c6f5d66"
            "414b182911d942896b1bb156c0ba37a9bfe4420bc17ddfe7be8daeabb37222d4ae081dd8"
            "89cb787c9bf801b07e186f274a70549a04"
        ),
        gas_limit=1635935265,
        gas_price=10,
        nonce=0,
        value=1962905609,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
