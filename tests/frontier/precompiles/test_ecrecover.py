"""Tests ecrecover precompiled contract."""

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
    "msg_hash, v, r, s, output",
    [
        pytest.param(
            bytes.fromhex(
                "18c547e4f7b0f325ad1e56f57e26c745b09a3e503d86e00e5255ff7f715d3d1c"
            ),
            bytes.fromhex(
                "000000000000000000000000000000000000000000000000000000000000001c"
            ),
            bytes.fromhex(
                "73b1693892219d736caba55bdb67216e485557ea6b6af75f37096c9aa6a5a75f"
            ),
            bytes.fromhex(
                "eeb940b1d03b21e36b0e47e79769f095fe2ab855bd91e3a38756b7d75a9c4549"
            ),
            bytes.fromhex(
                "000000000000000000000000a94f5374fce5edbc8e2a8697c15331677e6ebf0b"
            ),
            id="valid_signature_1",
        ),
        pytest.param(
            bytes.fromhex(
                "18c547e4f7b0f325ad1e56f57e26c745b09a3e503d86e00e5255ff7f715d3d1c"
            ),
            bytes.fromhex(
                "000000000000000000000000000000000000000000000000000000000000001b"
            ),
            bytes.fromhex(
                "7af9e73057870458f03c143483bc5fcb6f39d01c9b26d28ed9f3fe23714f6628"
            ),
            bytes.fromhex(
                "3134a4ba8fafe11b351a720538398a5635e235c0b3258dce19942000731079ec"
            ),
            bytes.fromhex(
                "0000000000000000000000009a04aede774152f135315670f562c19c5726df2c"
            ),
            id="valid_signature_2",
        ),
        # z >= Order
        pytest.param(
            bytes.fromhex(
                "fffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364141"
            ),
            bytes.fromhex(
                "000000000000000000000000000000000000000000000000000000000000001b"
            ),
            bytes.fromhex(
                "7af9e73057870458f03c143483bc5fcb6f39d01c9b26d28ed9f3fe23714f6628"
            ),
            bytes.fromhex(
                "3134a4ba8fafe11b351a720538398a5635e235c0b3258dce19942000731079ec"
            ),
            bytes.fromhex(
                "000000000000000000000000b32cf3c8616537a28583fc00d29a3e8c9614cd61"
            ),
            id="z_gte_order",
        ),
        pytest.param(
            bytes.fromhex(
                "6b8d2c81b11b2d699528dde488dbdf2f94293d0d33c32e347f255fa4a6c1f0a9"
            ),
            bytes.fromhex(
                "000000000000000000000000000000000000000000000000000000000000001b"
            ),
            bytes.fromhex(
                "79be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798"
            ),
            bytes.fromhex(
                "6b8d2c81b11b2d699528dde488dbdf2f94293d0d33c32e347f255fa4a6c1f0a9"
            ),
            b"",
            id="invalid_signature_1",
        ),
        pytest.param(
            bytes.fromhex(
                "18c547e4f7b0f325ad1e56f57e26c745b09a3e503d86e00e5255ff7f715d3d1c"
            ),
            bytes.fromhex(
                "000000000000000000000000000000000000000000000000000000000000001c"
            ),
            bytes.fromhex(
                "0000000000000000000000000000000000000000000000000000000000000000"
            ),
            bytes.fromhex(
                "eeb940b1d03b21e36b0e47e79769f095fe2ab855bd91e3a38756b7d75a9c4549"
            ),
            b"",
            id="invalid_signature_2",
        ),
        pytest.param(
            bytes.fromhex(
                "18c547e4f7b0f325ad1e56f57e26c745b09a3e503d86e00e5255ff7f715d3d1c"
            ),
            bytes.fromhex(
                "000000000000000000000000000000000000000000000000000000000000001c"
            ),
            bytes.fromhex(
                "73b1693892219d736caba55bdb67216e485557ea6b6af75f37096c9aa6a5a75f"
            ),
            bytes.fromhex(
                "0000000000000000000000000000000000000000000000000000000000000000"
            ),
            b"",
            id="invalid_signature_3",
        ),
        # r >= Order
        pytest.param(
            bytes.fromhex(
                "18c547e4f7b0f325ad1e56f57e26c745b09a3e503d86e00e5255ff7f715d3d1c"
            ),
            bytes.fromhex(
                "000000000000000000000000000000000000000000000000000000000000001c"
            ),
            bytes.fromhex(
                "fffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364141"
            ),
            bytes.fromhex(
                "eeb940b1d03b21e36b0e47e79769f095fe2ab855bd91e3a38756b7d75a9c4549"
            ),
            b"",
            id="invalid_signature_3",
        ),
        # s >= Order
        pytest.param(
            bytes.fromhex(
                "18c547e4f7b0f325ad1e56f57e26c745b09a3e503d86e00e5255ff7f715d3d1c"
            ),
            bytes.fromhex(
                "000000000000000000000000000000000000000000000000000000000000001c"
            ),
            bytes.fromhex(
                "73b1693892219d736caba55bdb67216e485557ea6b6af75f37096c9aa6a5a75f"
            ),
            bytes.fromhex(
                "fffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364141"
            ),
            b"",
            id="s_gte_order",
        ),
        # u1 == u2 && R == G
        pytest.param(
            bytes.fromhex(
                "c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470"
            ),
            bytes.fromhex(
                "000000000000000000000000000000000000000000000000000000000000001b"
            ),
            bytes.fromhex(
                "79be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798"
            ),
            bytes.fromhex(
                "3a2db9fe7908dcc36d81824d2338fc3dd5ae2692e4c6790043d7868872b09cd1"
            ),
            bytes.fromhex(
                "0000000000000000000000002e4db28b1f03ec8acfc2865e0c08308730e7ddf2"
            ),
            id="u1_eq_u2_R_eq_G",
        ),
        # u1 == -u2 && R == -G
        pytest.param(
            bytes.fromhex(
                "c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470"
            ),
            bytes.fromhex(
                "000000000000000000000000000000000000000000000000000000000000001c"
            ),
            bytes.fromhex(
                "79be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798"
            ),
            bytes.fromhex(
                "c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470"
            ),
            bytes.fromhex(
                "0000000000000000000000002e4db28b1f03ec8acfc2865e0c08308730e7ddf2"
            ),
            id="u1_eq_neg_u2_R_eq_neg_G",
        ),
        # 13u1 == u2 && R == -13G
        pytest.param(
            bytes.fromhex(
                "c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470"
            ),
            bytes.fromhex(
                "000000000000000000000000000000000000000000000000000000000000001b"
            ),
            bytes.fromhex(
                "f28773c2d975288bc7d1d205c3748651b075fbc6610e58cddeeddf8f19405aa8"
            ),
            bytes.fromhex(
                "533e9827446324ac92450a05ef04622bc0081f8d5b394e4d7b514ed35c946ee9"
            ),
            b"",
            id="13u1_eq_u2_R_eq_neg_13G",
        ),
        # 13u1 == u2 && R == 13G
        pytest.param(
            bytes.fromhex(
                "c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470"
            ),
            bytes.fromhex(
                "000000000000000000000000000000000000000000000000000000000000001c"
            ),
            bytes.fromhex(
                "f28773c2d975288bc7d1d205c3748651b075fbc6610e58cddeeddf8f19405aa8"
            ),
            bytes.fromhex(
                "533e9827446324ac92450a05ef04622bc0081f8d5b394e4d7b514ed35c946ee9"
            ),
            bytes.fromhex(
                "000000000000000000000000fc4b7e97f115ac81f9a6997254892b45e8159d46"
            ),
            id="13u1_eq_u2_R_eq_13G",
        ),
    ],
)
def test_precompiles(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    msg_hash: bytes,
    v: bytes,
    r: bytes,
    s: bytes,
    output: bytes,
) -> None:
    """
    Tests the behavior of `ecrecover` precompiled contract.
    """
    env = Environment()

    # Memory
    hash_offset = 0
    v_offset = 32
    r_offset = 64
    s_offset = 96
    ret_offset = 128

    account = pre.deploy_contract(
        Op.MSTORE(hash_offset, msg_hash)
        + Op.MSTORE(v_offset, v)
        + Op.MSTORE(r_offset, r)
        + Op.MSTORE(s_offset, s)
        + Op.CALL(
            gas=50_000,
            address="0x01",  # ecrecover precompile address
            args_offset=hash_offset,
            args_size=4 * 32,
            ret_offset=ret_offset,
            ret_size=32,
        )
        + Op.SSTORE(0, Op.MLOAD(ret_offset))
        + Op.STOP,
        storage={0: 0xDEADBEEF},
    )

    tx = Transaction(
        to=account,
        sender=pre.fund_eoa(),
        gas_limit=1_000_000,
        protected=fork >= Byzantium,
    )

    post = {account: Account(storage={0: output})}

    state_test(env=env, pre=pre, post=post, tx=tx)
