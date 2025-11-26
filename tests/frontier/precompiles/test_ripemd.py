"""Tests RIPEMD-160 precompiled contract."""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks.forks.forks import Byzantium
from execution_testing.forks.helpers import Fork
from execution_testing.vm import Opcodes as Op


@pytest.mark.valid_from("Frontier")
@pytest.mark.parametrize(
    "msg, output",
    [
        pytest.param(
            b"abc",
            bytes.fromhex("8eb208f7e05d987a9b044a8e98c6b087f15a0bfc"),
            id="ripemd_abc",
        ),
        pytest.param(
            b"message digest",
            bytes.fromhex("5d0689ef49d2fae572b881b123a85ffa21595f36"),
            id="ripemd_message_digest",
        ),
        pytest.param(
            b"abcdefghijklmnopqrstuvwxyz",
            bytes.fromhex("f71c27109c692c1b56bbdceb5b9d2865b3708dbc"),
            id="ripemd_alphabet",
        ),
        pytest.param(
            b"abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq",
            bytes.fromhex("12a053384a9c0c88e405a06c27dcf49ada62eb2b"),
            id="ripemd_long",
        ),
        pytest.param(
            b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789",
            bytes.fromhex("b0e20b6e3116640286ed3a87a5713079b21f5189"),
            id="ripemd_alnum",
        ),
        pytest.param(
            b"12345678901234567890123456789012345678901234567890123456789012345678901234567890",
            bytes.fromhex("9b752e45573d4b39f4dbd3323cab82bf63326bfb"),
            id="ripemd_numeric",
        ),
        pytest.param(
            b"The quick brown fox jumps over the lazy dog",
            bytes.fromhex("37f332f68db77bd9d7edd4969571ad671cf9dd3b"),
            id="ripemd_quick_brown_fox",
        ),
        pytest.param(
            b"a" * 0,
            bytes.fromhex("9c1185a5c5e9fc54612808977ee8f548b2258d31"),
            id="ripemd_a_0",
        ),
        pytest.param(
            b"a" * 1,
            bytes.fromhex("0bdc9d2d256b3ee9daae347be6f4dc835a467ffe"),
            id="ripemd_a_1",
        ),
        pytest.param(
            b"a" * 54,
            bytes.fromhex("a57fa1577740fd73b6859dd20e090cdac4d2af36"),
            id="ripemd_a_54",
        ),
        pytest.param(
            b"a" * 55,
            bytes.fromhex("0d8a8c9063a48576a7c97e9f95253a6e53ff6765"),
            id="length fits into the first block",
        ),
        pytest.param(
            b"a" * 56,
            bytes.fromhex("e72334b46c83cc70bef979e15453706c95b888be"),
            id="ripemd_a_56",
        ),
        pytest.param(
            b"a" * 57,
            bytes.fromhex("eed82d19d597ab275b550ff3d6e0bc2a75350388"),
            id="ripemd_a_57",
        ),
        pytest.param(
            b"a" * 63,
            bytes.fromhex("e640041293fe663b9bf3f8c21ffecac03819e6b2"),
            id="ripemd_a_63",
        ),
        pytest.param(
            b"a" * 64,
            bytes.fromhex("9dfb7d374ad924f3f88de96291c33e9abed53e32"),
            id="full block",
        ),
        pytest.param(
            b"a" * 65,
            bytes.fromhex("99724bb11811e7166af38f671b6a082d8ab4960b"),
            id="ripemd_a_65",
        ),
        pytest.param(
            b"a" * 119,
            bytes.fromhex("23e398ff2bac815aa1bbb57ca2a669c841872919"),
            id="ripemd_a_119",
        ),
        pytest.param(
            b"a" * 120,
            bytes.fromhex("c476770a6dae31fcee8d25efe6559a05c8024595"),
            id="ripemd_a_120",
        ),
        pytest.param(
            b"a" * 121,
            bytes.fromhex("725c88a6f41605e99477a1478607d3fe25ced606"),
            id="ripemd_a_121",
        ),
        pytest.param(
            b"a" * 127,
            bytes.fromhex("64f2d68b85f394e2e4f49009c4bd50224c2698ed"),
            id="ripemd_a_127",
        ),
        pytest.param(
            b"a" * 128,
            bytes.fromhex("8dfdfb32b2ed5cb41a73478b4fd60cc5b4648b15"),
            id="two blocks",
        ),
        pytest.param(
            b"a" * 129,
            bytes.fromhex("62bb9091f499f294f15aa5b951df4d9744d50cf2"),
            id="ripemd_a_129",
        ),
        pytest.param(
            b"a" * 10_000,
            bytes.fromhex("eb33e86b2400cc0a11707be717a35a9acf074a58"),
            id="ripemd_a_10000",
        ),
    ],
)
def test_precompiles(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    msg: bytes,
    output: bytes,
) -> None:
    """
    Tests the behavior of `RIPEMD-160` precompiled contract.
    """
    env = Environment()

    account = pre.deploy_contract(
        code=Op.CALLDATACOPY(0, 0, len(msg))
        + Op.MLOAD(0)
        + Op.CALL(
            gas=50_000,
            address="0x03",  # RIPEMD-160 precompile address
            args_offset=0,
            args_size=len(msg),
            ret_offset=len(msg),
            ret_size=32,
        )
        + Op.SSTORE(0, Op.MLOAD(len(msg)))
        + Op.STOP,
        storage={0: 0xDEADBEEF},
    )

    tx = Transaction(
        to=account,
        sender=pre.fund_eoa(),
        gas_limit=1_000_0000,
        data=msg,
        protected=fork >= Byzantium,
    )

    post = {account: Account(storage={0: output})}

    state_test(env=env, pre=pre, post=post, tx=tx)
