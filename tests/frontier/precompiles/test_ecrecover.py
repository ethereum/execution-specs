"""Tests ecrecover precompiled contract."""

from typing import Any

import pytest
from execution_testing import (
    Account,
    Alloc,
    StateTestFiller,
    Storage,
    Transaction,
    While,
)
from execution_testing.forks.helpers import Fork
from execution_testing.vm import Opcodes as Op

from .spec import EcrecoverInput, Spec


@pytest.mark.ported_from(
    [
        "state_tests/stPreCompiledContracts2/CALLCODEEcrecover0Filler.json",
        "state_tests/stPreCompiledContracts2/CALLCODEEcrecover1Filler.json",
        "state_tests/stPreCompiledContracts2/CALLCODEEcrecover3Filler.json",
        "state_tests/stPreCompiledContracts2/CALLCODEEcrecover80Filler.json",
        "state_tests/stPreCompiledContracts2/CALLCODEEcrecoverH_prefixed0Filler.json",
        "state_tests/stPreCompiledContracts2/CALLCODEEcrecoverR_prefixed0Filler.json",
        "state_tests/stPreCompiledContracts2/CALLCODEEcrecoverS_prefixed0Filler.json",
        "state_tests/stPreCompiledContracts2/CALLCODEEcrecoverV_prefixed0Filler.json",
        "state_tests/stPreCompiledContracts2/CALLCODEEcrecoverV_prefixedf0Filler.json",
        "state_tests/stPreCompiledContracts2/CallEcrecover0Filler.json",
        "state_tests/stPreCompiledContracts2/CallEcrecover1Filler.json",
        "state_tests/stPreCompiledContracts2/CallEcrecover3Filler.json",
        "state_tests/stPreCompiledContracts2/CallEcrecover80Filler.json",
        "state_tests/stPreCompiledContracts2/CallEcrecoverH_prefixed0Filler.json",
        "state_tests/stPreCompiledContracts2/CallEcrecoverInvalidSignatureFiller.json",
        "state_tests/stPreCompiledContracts2/CallEcrecoverR_prefixed0Filler.json",
        "state_tests/stPreCompiledContracts2/CallEcrecoverS_prefixed0Filler.json",
        "state_tests/stPreCompiledContracts2/CallEcrecoverUnrecoverableKeyFiller.json",
        "state_tests/stPreCompiledContracts2/CallEcrecoverV_prefixed0Filler.json",
        "state_tests/stPreCompiledContracts2/CallEcrecover_OverflowFiller.yml",
        "state_tests/stPreCompiledContracts2/ecrecoverWeirdVFiller.yml",
        "state_tests/stStaticCall/static_CallEcrecover0Filler.json",
        "state_tests/stStaticCall/static_CallEcrecover1Filler.json",
        "state_tests/stStaticCall/static_CallEcrecover3Filler.json",
        "state_tests/stStaticCall/static_CallEcrecover80Filler.json",
        "state_tests/stStaticCall/static_CallEcrecoverH_prefixed0Filler.json",
        "state_tests/stStaticCall/static_CallEcrecoverR_prefixed0Filler.json",
        "state_tests/stStaticCall/static_CallEcrecoverS_prefixed0Filler.json",
        "state_tests/stStaticCall/static_CallEcrecoverV_prefixed0Filler.json",
    ],
)
@pytest.mark.with_all_call_opcodes()
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
        pytest.param(
            bytes.fromhex(
                "2f380a2dea7e778d81affc2443403b8fe4644db442ae4862ff5bb3732829cdb9"
            ),
            bytes.fromhex(
                "000000000000000000000000000000000000000000000000000000000000001b"
            ),
            bytes.fromhex(
                "6b65ccb0558806e9b097f27a396d08f964e37b8b7af6ceeb516ff86739fbea0a"
            ),
            bytes.fromhex(
                "37cbc8d883e129a4b1ef9d5f1df53c4f21a3ef147cf2a50a4ede0eb06ce092d4"
            ),
            bytes.fromhex(
                "000000000000000000000000e4319f4b631c6d0fcfc84045dbcb676865fe5e13"
            ),
            id="valid_signature_3",
        ),
        pytest.param(
            bytes.fromhex(
                "00c547e4f7b0f325ad1e56f57e26c745b09a3e503d86e00e5255ff7f715d3d1c"
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
                "000000000000000000000000a0b29af6a56d6cfef6415cb195ccbe540e006d0a"
            ),
            id="msg_hash_high_byte_zeroed",
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
                "00b940b1d03b21e36b0e47e79769f095fe2ab855bd91e3a38756b7d75a9c4549"
            ),
            bytes.fromhex(
                "000000000000000000000000b4950a7fad428434b11c357fa6d4b4bcd3096a5d"
            ),
            id="s_high_byte_zeroed",
        ),
        # Zeroing r's high byte lands on a value that is in range but is
        # not the x-coordinate of any curve point, so recovery has no
        # solution. The next two cases reach the same state differently.
        pytest.param(
            bytes.fromhex(
                "18c547e4f7b0f325ad1e56f57e26c745b09a3e503d86e00e5255ff7f715d3d1c"
            ),
            bytes.fromhex(
                "000000000000000000000000000000000000000000000000000000000000001c"
            ),
            bytes.fromhex(
                "00b1693892219d736caba55bdb67216e485557ea6b6af75f37096c9aa6a5a75f"
            ),
            bytes.fromhex(
                "eeb940b1d03b21e36b0e47e79769f095fe2ab855bd91e3a38756b7d75a9c4549"
            ),
            b"",
            id="r_high_byte_zeroed",
        ),
        pytest.param(
            bytes.fromhex(
                "00c547e4f7b0f325ad1e56f57e26c745b09a3e503d86e00e5255ff7f715d3d1c"
            ),
            bytes.fromhex(
                "000000000000000000000000000000000000000000000000000000000000001c"
            ),
            bytes.fromhex(
                "00b1693892219d736caba55bdb67216e485557ea6b6af75f37096c9aa6a5a75f"
            ),
            bytes.fromhex(
                "00b940b1d03b21e36b0e47e79769f095fe2ab855bd91e3a38756b7d75a9c4549"
            ),
            b"",
            id="all_high_bytes_zeroed",
        ),
        # r and s are ASCII strings, and that r is off the curve too.
        pytest.param(
            bytes.fromhex(
                "a8b53bdf3306a35a7103ab5504a0c9b492295564b6202b1942a84ef300107281"
            ),
            bytes.fromhex(
                "000000000000000000000000000000000000000000000000000000000000001b"
            ),
            bytes.fromhex(
                "3078356531653033663533636531386237373263636230303933666637316633"
            ),
            bytes.fromhex(
                "6635336635633735623734646362333161383561613862383839326234653862"
            ),
            b"",
            id="unrecoverable_key",
        ),
        # z == N (order)
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
            id="z_eq_N",
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
        # v is neither 27 nor 28, so there is no recovery id.
        pytest.param(
            bytes.fromhex(
                "18c547e4f7b0f325ad1e56f57e26c745b09a3e503d86e00e5255ff7f715d3d1c"
            ),
            bytes.fromhex(
                "0000000000000000000000000000000000000000000000000000000000000001"
            ),
            bytes.fromhex(
                "73b1693892219d736caba55bdb67216e485557ea6b6af75f37096c9aa6a5a75f"
            ),
            bytes.fromhex(
                "eeb940b1d03b21e36b0e47e79769f095fe2ab855bd91e3a38756b7d75a9c4549"
            ),
            b"",
            id="v_eq_1",
        ),
        # 128 zero bytes: v is 0, so this fails the same rule as v_eq_1.
        pytest.param(
            bytes.fromhex(
                "0000000000000000000000000000000000000000000000000000000000000000"
            ),
            bytes.fromhex(
                "0000000000000000000000000000000000000000000000000000000000000000"
            ),
            bytes.fromhex(
                "0000000000000000000000000000000000000000000000000000000000000000"
            ),
            bytes.fromhex(
                "0000000000000000000000000000000000000000000000000000000000000000"
            ),
            b"",
            id="zero_input",
        ),
        # r == N (order)
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
            id="r_eq_N",
        ),
        # s == N (order)
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
            id="s_eq_N",
        ),
        # r == 0 and s == N (order)
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
                "fffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364141"
            ),
            b"",
            id="r_zero_and_s_eq_N",
        ),
        # r == N (order) and s == 0
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
                "0000000000000000000000000000000000000000000000000000000000000000"
            ),
            b"",
            id="r_eq_N_and_s_zero",
        ),
        # r == N (order) and s == N (order)
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
                "fffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364141"
            ),
            b"",
            id="r_eq_N_and_s_eq_N",
        ),
        # An in-range r that is not the x-coordinate of any curve point:
        # 5 is the smallest, as 5**3 + 7 is a quadratic non-residue mod p.
        pytest.param(
            bytes.fromhex(
                "18c547e4f7b0f325ad1e56f57e26c745b09a3e503d86e00e5255ff7f715d3d1c"
            ),
            bytes.fromhex(
                "000000000000000000000000000000000000000000000000000000000000001b"
            ),
            bytes.fromhex(
                "0000000000000000000000000000000000000000000000000000000000000005"
            ),
            bytes.fromhex(
                "0000000000000000000000000000000000000000000000000000000000000001"
            ),
            b"",
            id="r_not_on_curve",
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
        # u1 < u2 && R == -G
        pytest.param(
            bytes.fromhex(
                "8641998106234453aa5f9d6a3178f4f7b812e00b817a776265dfdd31b93e29a9"
            ),
            bytes.fromhex(
                "000000000000000000000000000000000000000000000000000000000000001c"
            ),
            bytes.fromhex(
                "79be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798"
            ),
            bytes.fromhex(
                "f37cccfdf3b97758ab40c52b9d0e160e0537f9b65b9c51b2b3e502b62df02f30"
            ),
            bytes.fromhex(
                "00000000000000000000000080c0dbf239224071c59dd8970ab9d542e3414ab2"
            ),
            id="u1_lt_u2_R_eq_neg_G",
        ),
        # u1 == u2 && R == -G, so the recovered point is the point at infinity
        pytest.param(
            bytes.fromhex(
                "0000000000000000000000000000000000000000000000000000000000000001"
            ),
            bytes.fromhex(
                "000000000000000000000000000000000000000000000000000000000000001c"
            ),
            bytes.fromhex(
                "79be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798"
            ),
            bytes.fromhex(
                "fffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364140"
            ),
            b"",
            id="u1_eq_u2_R_eq_neg_G",
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
        # R == 2G, low s
        pytest.param(
            bytes.fromhex(
                "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
            ),
            bytes.fromhex(
                "000000000000000000000000000000000000000000000000000000000000001c"
            ),
            bytes.fromhex(
                "c6047f9441ed7d6d3045406e95c07cd85c778e4b8cef3ca7abac09b95c709ee5"
            ),
            bytes.fromhex(
                "000000000000000000000000000000000000000000000000000000000000000b"
            ),
            bytes.fromhex(
                "000000000000000000000000a77cc0129dba3df2c0e27f2bfe79a18b498f8934"
            ),
            id="R_eq_2G_low_s",
        ),
        # R == 2G, high s
        pytest.param(
            bytes.fromhex(
                "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
            ),
            bytes.fromhex(
                "000000000000000000000000000000000000000000000000000000000000001c"
            ),
            bytes.fromhex(
                "c6047f9441ed7d6d3045406e95c07cd85c778e4b8cef3ca7abac09b95c709ee5"
            ),
            bytes.fromhex(
                "fffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd036413b"
            ),
            bytes.fromhex(
                "000000000000000000000000bbb10a3b5835400b63ca00372c16db781220fb0b"
            ),
            id="R_eq_2G_high_s",
        ),
        # R == 3G, low s
        pytest.param(
            bytes.fromhex(
                "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
            ),
            bytes.fromhex(
                "000000000000000000000000000000000000000000000000000000000000001c"
            ),
            bytes.fromhex(
                "f9308a019258c31049344f85f89d5229b531c845836f99b08601f113bce036f9"
            ),
            bytes.fromhex(
                "0000000000000000000000000000000000000000000000000000000000000010"
            ),
            bytes.fromhex(
                "000000000000000000000000620833dce54ca9329f13a22c3831b102f15df27c"
            ),
            id="R_eq_3G_low_s",
        ),
        # R == 3G, high s
        pytest.param(
            bytes.fromhex(
                "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
            ),
            bytes.fromhex(
                "000000000000000000000000000000000000000000000000000000000000001c"
            ),
            bytes.fromhex(
                "f9308a019258c31049344f85f89d5229b531c845836f99b08601f113bce036f9"
            ),
            bytes.fromhex(
                "fffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd036412a"
            ),
            bytes.fromhex(
                "000000000000000000000000b0e0b5974d71cd6d9142451cc94291dec4191b8b"
            ),
            id="R_eq_3G_high_s",
        ),
        # R == 4G, low s
        pytest.param(
            bytes.fromhex(
                "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
            ),
            bytes.fromhex(
                "000000000000000000000000000000000000000000000000000000000000001c"
            ),
            bytes.fromhex(
                "e493dbf1c10d80f3581e4904930b1404cc6c13900ee0758474fa94abe8c4cd13"
            ),
            bytes.fromhex(
                "0000000000000000000000000000000000000000000000000000000000000020"
            ),
            bytes.fromhex(
                "0000000000000000000000009d39e4bd10915d73b7d6ba205c1aefd814710aaa"
            ),
            id="R_eq_4G_low_s",
        ),
        # R == 4G, high s
        pytest.param(
            bytes.fromhex(
                "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
            ),
            bytes.fromhex(
                "000000000000000000000000000000000000000000000000000000000000001c"
            ),
            bytes.fromhex(
                "e493dbf1c10d80f3581e4904930b1404cc6c13900ee0758474fa94abe8c4cd13"
            ),
            bytes.fromhex(
                "fffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364112"
            ),
            bytes.fromhex(
                "0000000000000000000000000a6fe081a013109d981bad2c5143d7a1fd3bfef7"
            ),
            id="R_eq_4G_high_s",
        ),
        # One step either side of the curve order. N + 1 reduces to 1,
        # a valid x-coordinate; N - 1 is on no curve point, leaving N - 2
        # the largest recoverable r.
        pytest.param(
            bytes.fromhex(
                "18c547e4f7b0f325ad1e56f57e26c745b09a3e503d86e00e5255ff7f715d3d1c"
            ),
            bytes.fromhex(
                "000000000000000000000000000000000000000000000000000000000000001c"
            ),
            bytes.fromhex(
                "fffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364142"
            ),
            bytes.fromhex(
                "efffd310ac743f371de3b9f7f9cb56c0b28ad43601b4ab949f53faa07bd2c804"
            ),
            b"",
            id="r_eq_N_plus_one",
        ),
        pytest.param(
            bytes.fromhex(
                "18c547e4f7b0f325ad1e56f57e26c745b09a3e503d86e00e5255ff7f715d3d1c"
            ),
            bytes.fromhex(
                "000000000000000000000000000000000000000000000000000000000000001c"
            ),
            bytes.fromhex(
                "fffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364140"
            ),
            bytes.fromhex(
                "efffd310ac743f371de3b9f7f9cb56c0b28ad43601b4ab949f53faa07bd2c804"
            ),
            b"",
            id="r_eq_N_minus_one",
        ),
        pytest.param(
            bytes.fromhex(
                "18c547e4f7b0f325ad1e56f57e26c745b09a3e503d86e00e5255ff7f715d3d1c"
            ),
            bytes.fromhex(
                "000000000000000000000000000000000000000000000000000000000000001c"
            ),
            bytes.fromhex(
                "fffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd036413f"
            ),
            bytes.fromhex(
                "efffd310ac743f371de3b9f7f9cb56c0b28ad43601b4ab949f53faa07bd2c804"
            ),
            bytes.fromhex(
                "0000000000000000000000002182da748249a933bf737586b80212df19b8f829"
            ),
            id="r_eq_N_minus_two",
        ),
        pytest.param(
            bytes.fromhex(
                "18c547e4f7b0f325ad1e56f57e26c745b09a3e503d86e00e5255ff7f715d3d1c"
            ),
            bytes.fromhex(
                "000000000000000000000000000000000000000000000000000000000000001c"
            ),
            bytes.fromhex(
                "48b55bfa915ac795c431978d8a6a992b628d557da5ff759b307d495a36649353"
            ),
            bytes.fromhex(
                "fffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364142"
            ),
            b"",
            id="s_eq_N_plus_one",
        ),
        pytest.param(
            bytes.fromhex(
                "18c547e4f7b0f325ad1e56f57e26c745b09a3e503d86e00e5255ff7f715d3d1c"
            ),
            bytes.fromhex(
                "000000000000000000000000000000000000000000000000000000000000001c"
            ),
            bytes.fromhex(
                "48b55bfa915ac795c431978d8a6a992b628d557da5ff759b307d495a36649353"
            ),
            bytes.fromhex(
                "fffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364140"
            ),
            bytes.fromhex(
                "0000000000000000000000001b85ac3c9b09de43659c5d04a2d9c75457d9abf4"
            ),
            id="s_eq_N_minus_one",
        ),
        pytest.param(
            bytes.fromhex(
                "18c547e4f7b0f325ad1e56f57e26c745b09a3e503d86e00e5255ff7f715d3d1c"
            ),
            bytes.fromhex(
                "000000000000000000000000000000000000000000000000000000000000001c"
            ),
            bytes.fromhex(
                "48b55bfa915ac795c431978d8a6a992b628d557da5ff759b307d495a36649353"
            ),
            bytes.fromhex(
                "fffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd036413f"
            ),
            bytes.fromhex(
                "000000000000000000000000d0277c8a3eccd462a313fc60161bac36b16e8699"
            ),
            id="s_eq_N_minus_two",
        ),
        # One key signing three messages, including the smallest hashes.
        pytest.param(
            bytes.fromhex(
                "0000000000000000000000000000000000000000000000000000000000000000"
            ),
            bytes.fromhex(
                "000000000000000000000000000000000000000000000000000000000000001b"
            ),
            bytes.fromhex(
                "ce354e1b07ba96e325aa4851999f07aabcb4471e49f0a0daafed98caab963f03"
            ),
            bytes.fromhex(
                "79d9f3993cdd509f1bfba63dbd23dbdff879fb95203a5049f348a95ce8249f3b"
            ),
            bytes.fromhex(
                "000000000000000000000000b957b0da344f6a17f0081d63be7345a860e5b7a2"
            ),
            id="msg_hash_zero",
        ),
        pytest.param(
            bytes.fromhex(
                "0000000000000000000000000000000000000000000000000000000000000001"
            ),
            bytes.fromhex(
                "000000000000000000000000000000000000000000000000000000000000001c"
            ),
            bytes.fromhex(
                "541c4ce1565a646ddde26e1b483a88a6500ce15bd24622492f05cdd18b97161d"
            ),
            bytes.fromhex(
                "1827e364c15cfa61dab02339904b1e542f3939c6e8d6367d352026e71ffd6af5"
            ),
            bytes.fromhex(
                "000000000000000000000000b957b0da344f6a17f0081d63be7345a860e5b7a2"
            ),
            id="msg_hash_one",
        ),
        pytest.param(
            bytes.fromhex(
                "deaf0dead0600d0f00d00000000000000060a70000000000000f0ad0bad0beef"
            ),
            bytes.fromhex(
                "000000000000000000000000000000000000000000000000000000000000001b"
            ),
            bytes.fromhex(
                "8a41a35dfd03f28615dc64b7754457691c66bd73f630c7423280282fa431a5be"
            ),
            bytes.fromhex(
                "2d40decf11713d564fa2df10dea5eb2adf45455ed309b4c8cc6853e2498323f5"
            ),
            bytes.fromhex(
                "000000000000000000000000b957b0da344f6a17f0081d63be7345a860e5b7a2"
            ),
            id="msg_hash_high_bytes_set",
        ),
        # v values a signature could plausibly carry, none of them 27 or 28.
        pytest.param(
            bytes.fromhex(
                "0000000000000000000000000000000000000000000000000000000000000001"
            ),
            bytes.fromhex(
                "0000000000000000000000000000000000000000000000000000000000000000"
            ),
            bytes.fromhex(
                "541c4ce1565a646ddde26e1b483a88a6500ce15bd24622492f05cdd18b97161d"
            ),
            bytes.fromhex(
                "1827e364c15cfa61dab02339904b1e542f3939c6e8d6367d352026e71ffd6af5"
            ),
            b"",
            id="v_eq_0",
        ),
        # A real chain-id-1 transaction signature, v included.
        pytest.param(
            bytes.fromhex(
                "daf5a779ae972f972197303d7b574746c7ef83eadac0f2791ad23db92e4c8e53"
            ),
            bytes.fromhex(
                "0000000000000000000000000000000000000000000000000000000000000025"
            ),
            bytes.fromhex(
                "28ef61340bd939bc2195fe537567866003e1a15d3c71ff63e1590620aa636276"
            ),
            bytes.fromhex(
                "67cbe9d8997f761aecb703304b3800ccf555c9f3dc64214b297fb1966a3b6d83"
            ),
            b"",
            id="v_eq_37_eip155_chain_id_1",
        ),
        pytest.param(
            bytes.fromhex(
                "0000000000000000000000000000000000000000000000000000000000000000"
            ),
            bytes.fromhex(
                "0000000000000000000000000000000000000000000000000000000000000023"
            ),
            bytes.fromhex(
                "ce354e1b07ba96e325aa4851999f07aabcb4471e49f0a0daafed98caab963f03"
            ),
            bytes.fromhex(
                "79d9f3993cdd509f1bfba63dbd23dbdff879fb95203a5049f348a95ce8249f3b"
            ),
            b"",
            id="v_eq_35_eip155",
        ),
        pytest.param(
            bytes.fromhex(
                "0000000000000000000000000000000000000000000000000000000000000001"
            ),
            bytes.fromhex(
                "0000000000000000000000000000000000000000000000000000000000000026"
            ),
            bytes.fromhex(
                "541c4ce1565a646ddde26e1b483a88a6500ce15bd24622492f05cdd18b97161d"
            ),
            bytes.fromhex(
                "1827e364c15cfa61dab02339904b1e542f3939c6e8d6367d352026e71ffd6af5"
            ),
            b"",
            id="v_eq_38_eip155",
        ),
        pytest.param(
            bytes.fromhex(
                "0000000000000000000000000000000000000000000000000000000000000001"
            ),
            bytes.fromhex(
                "00000000000000000000000000000000000000000000000000000000000000ec"
            ),
            bytes.fromhex(
                "541c4ce1565a646ddde26e1b483a88a6500ce15bd24622492f05cdd18b97161d"
            ),
            bytes.fromhex(
                "1827e364c15cfa61dab02339904b1e542f3939c6e8d6367d352026e71ffd6af5"
            ),
            b"",
            id="v_eq_236_eip155",
        ),
        pytest.param(
            bytes.fromhex(
                "0000000000000000000000000000000000000000000000000000000000000000"
            ),
            bytes.fromhex(
                "00000000000000000000000000000000000000000000000000000000000000ff"
            ),
            bytes.fromhex(
                "ce354e1b07ba96e325aa4851999f07aabcb4471e49f0a0daafed98caab963f03"
            ),
            bytes.fromhex(
                "79d9f3993cdd509f1bfba63dbd23dbdff879fb95203a5049f348a95ce8249f3b"
            ),
            b"",
            id="v_eq_0xff",
        ),
        pytest.param(
            bytes.fromhex(
                "0000000000000000000000000000000000000000000000000000000000000001"
            ),
            bytes.fromhex(
                "0000000000000000000000000000000000000000000000000000000000000100"
            ),
            bytes.fromhex(
                "541c4ce1565a646ddde26e1b483a88a6500ce15bd24622492f05cdd18b97161d"
            ),
            bytes.fromhex(
                "1827e364c15cfa61dab02339904b1e542f3939c6e8d6367d352026e71ffd6af5"
            ),
            b"",
            id="v_eq_0x100",
        ),
        pytest.param(
            bytes.fromhex(
                "0000000000000000000000000000000000000000000000000000000000000001"
            ),
            bytes.fromhex(
                "0000000000000000000000000000000000000000000000000000deadbeef0100"
            ),
            bytes.fromhex(
                "541c4ce1565a646ddde26e1b483a88a6500ce15bd24622492f05cdd18b97161d"
            ),
            bytes.fromhex(
                "1827e364c15cfa61dab02339904b1e542f3939c6e8d6367d352026e71ffd6af5"
            ),
            b"",
            id="v_high_word_low_byte_zero",
        ),
        # Every field set to the same arbitrary value.
        pytest.param(
            bytes.fromhex(
                "0000000000000000000000000000000000000000000000000000000000007e57"
            ),
            bytes.fromhex(
                "0000000000000000000000000000000000000000000000000000000000007e57"
            ),
            bytes.fromhex(
                "0000000000000000000000000000000000000000000000000000000000007e57"
            ),
            bytes.fromhex(
                "0000000000000000000000000000000000000000000000000000000000007e57"
            ),
            b"",
            id="all_fields_0x7e57",
        ),
        # The v of a valid signature, with garbage above its low byte.
        pytest.param(
            bytes.fromhex(
                "18c547e4f7b0f325ad1e56f57e26c745b09a3e503d86e00e5255ff7f715d3d1c"
            ),
            bytes.fromhex(
                "000000000000000000000000000000000000000000000000000000000000f01c"
            ),
            bytes.fromhex(
                "73b1693892219d736caba55bdb67216e485557ea6b6af75f37096c9aa6a5a75f"
            ),
            bytes.fromhex(
                "eeb940b1d03b21e36b0e47e79769f095fe2ab855bd91e3a38756b7d75a9c4549"
            ),
            b"",
            id="v_prefixed_0xf0",
        ),
        pytest.param(
            bytes.fromhex(
                "18c547e4f7b0f325ad1e56f57e26c745b09a3e503d86e00e5255ff7f715d3d1c"
            ),
            bytes.fromhex(
                "00000000000000000000000000000000f000000000000000000000000000001c"
            ),
            bytes.fromhex(
                "73b1693892219d736caba55bdb67216e485557ea6b6af75f37096c9aa6a5a75f"
            ),
            bytes.fromhex(
                "eeb940b1d03b21e36b0e47e79769f095fe2ab855bd91e3a38756b7d75a9c4549"
            ),
            b"",
            id="v_prefixed_high_word",
        ),
    ],
)
@pytest.mark.eels_base_coverage
def test_precompiles(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    call_opcode: Op,
    msg_hash: bytes,
    v: bytes,
    r: bytes,
    s: bytes,
    output: bytes,
) -> None:
    """
    Tests the behavior of `ecrecover` precompiled contract.
    """
    # Memory
    hash_offset = 0
    v_offset = 32
    r_offset = 64
    s_offset = 96
    ret_offset = 128
    # The precompile returns one word, a rejected input none at all, so
    # both seeded words of the wider window must survive.
    ret_size = 2 * 32
    ret_sentinel = b"\xff" * 32

    # Storage
    success_slot = 0
    first_word_slot = 1
    second_word_slot = 2

    # A rejected input is not a failed call: the precompile charges its
    # full price and returns. Forwarding exactly that price makes an
    # implementation that charges more fail the call.
    account = pre.deploy_contract(
        Op.MSTORE(hash_offset, msg_hash)
        + Op.MSTORE(v_offset, v)
        + Op.MSTORE(r_offset, r)
        + Op.MSTORE(s_offset, s)
        + Op.MSTORE(ret_offset, ret_sentinel)
        + Op.MSTORE(ret_offset + 32, ret_sentinel)
        + Op.SSTORE(
            success_slot,
            call_opcode(
                gas=fork.gas_costs().PRECOMPILE_ECRECOVER,
                address="0x01",  # ecrecover precompile address
                args_offset=hash_offset,
                args_size=4 * 32,
                ret_offset=ret_offset,
                ret_size=ret_size,
            ),
        )
        + Op.SSTORE(first_word_slot, Op.MLOAD(ret_offset))
        + Op.SSTORE(second_word_slot, Op.MLOAD(ret_offset + 32))
        + Op.STOP,
        storage=dict.fromkeys(
            (success_slot, first_word_slot, second_word_slot), 0xDEADBEEF
        ),
    )

    tx = Transaction(
        to=account,
        sender=pre.fund_eoa(),
        protected=fork.supports_protected_txs(),
    )

    post = {
        account: Account(
            storage={
                success_slot: 1,
                first_word_slot: output or ret_sentinel,
                second_word_slot: ret_sentinel,
            }
        )
    }

    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    [
        "state_tests/stQuadraticComplexityTest/Call50000_ecrecFiller.json",
        "state_tests/stStaticCall/static_Call50000_ecrecFiller.json",
    ],
    coverage_missed_reason=(
        "The fillers repeat the call until the transaction runs out of gas, "
        "so their whole post-state is the empty one a reverted transaction "
        "leaves behind. The port runs its iterations to completion and "
        "checks the residue instead, keeping the oversized input window but "
        "not the cost of the repetition itself."
    ),
)
@pytest.mark.with_all_call_opcodes
@pytest.mark.valid_from("Frontier")
def test_repeated_underfunded_calls(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    call_opcode: Op,
) -> None:
    """
    Test that repeated underfunded calls to ecrecover all fail, leave the
    return buffer untouched and move no value to the precompile.
    """
    iterations = 10

    # The same signature recovers an address in `test_precompiles`, so the
    # gas is the only reason these calls fail.
    signature = EcrecoverInput(
        msg_hash=(
            0x18C547E4F7B0F325AD1E56F57E26C745B09A3E503D86E00E5255FF7F715D3D1C
        ),
        v=0x1C,
        r=0x73B1693892219D736CABA55BDB67216E485557EA6B6AF75F37096C9AA6A5A75F,
        s=0xEEB940B1D03B21E36B0E47E79769F095FE2AB855BD91E3A38756B7D75A9C4549,
    )

    # A value-bearing call adds the stipend to what the callee receives, so
    # the operand that leaves the precompile one gas short depends on the
    # opcode.
    gas_costs = fork.gas_costs()
    sends_value = "value" in call_opcode.kwargs
    stipend = gas_costs.CALL_STIPEND if sends_value else 0
    forwarded_gas = gas_costs.PRECOMPILE_ECRECOVER - stipend - 1

    # Memory: the input window, then the return buffer, then the loop
    # counter. The window is far wider than the 128 bytes the precompile
    # reads, as in the fillers: a client that copies the whole window
    # before charging for the call pays for it once per iteration.
    args_size = 50_000
    ret_offset = args_size
    counter_offset = ret_offset + 32

    # A failed call returns no bytes, so both seeded values must survive.
    successes_base = 0xC0DE
    ret_sentinel = b"\xff" * 32

    storage = Storage()
    successes_slot = storage.store_next(successes_base, "successes")

    # One wei per iteration, so no call can fail for want of balance.
    caller_balance = iterations
    value_kwarg: dict[str, Any] = {"value": 1} if sends_value else {}
    call = call_opcode(
        gas=forwarded_gas,
        address=Spec.ECRECOVER,
        args_offset=0,
        args_size=args_size,
        ret_offset=ret_offset,
        ret_size=32,
        **value_kwarg,
    )
    body = Op.SSTORE(
        successes_slot, Op.ADD(Op.SLOAD(successes_slot), call)
    ) + Op.MSTORE(counter_offset, Op.ADD(Op.MLOAD(counter_offset), 1))

    caller = pre.deploy_contract(
        Op.CALLDATACOPY(0, 0, len(bytes(signature)))
        + Op.MSTORE(ret_offset, ret_sentinel)
        + While(
            body=body,
            condition=Op.LT(Op.MLOAD(counter_offset), iterations),
        )
        + Op.SSTORE(storage.store_next(iterations), Op.MLOAD(counter_offset))
        + Op.SSTORE(storage.store_next(ret_sentinel), Op.MLOAD(ret_offset))
        + Op.STOP,
        storage={successes_slot: successes_base},
        balance=caller_balance,
    )

    tx = Transaction(
        to=caller,
        data=signature,
        sender=pre.fund_eoa(),
        protected=fork.supports_protected_txs(),
    )

    post = {
        caller: Account(storage=storage, balance=caller_balance),
        Spec.ECRECOVER: Account.NONEXISTENT,
    }

    state_test(pre=pre, post=post, tx=tx)
