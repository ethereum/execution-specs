"""
THROWAWAY MEASUREMENT INSTRUMENT -- its failures are the measurement.

Probes what a bare `STATICCALL` observes at addresses that are precompiles on
some forks and plain empty accounts on others, and what modexp charges for a
given input *shape*. Each param packs its three observables into one word

    packed = success << 64 | returndatasize << 32 | frame_gas_delta

and asserts a deliberately wrong sentinel, so the KeyValueMismatchError
prints the real value. Only the FIRST mismatching slot is reported per test,
which is why everything is packed into slot 0.

Run (from tests/deployed_idioms/):
  python3 tools/locked_fill.py \
    /abs/path/expansion/tests/tools/test_precompile_address_probe.py \
    --from Berlin --until Amsterdam --output /tmp/pp -q -p no:cacheprovider
decode: packed >> 64, (packed >> 32) & M32, packed & M32
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytecode,
    Op,
    StateTestFiller,
    Transaction,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

SENTINEL = 0xDEAD
FORWARD = 50_000

ADDRESSES = {
    "a_0x05_modexp": 0x05,
    "b_0x0a_point_evaluation": 0x0A,
    "c_0x0b_bls_g1add": 0x0B,
    "d_0x100_p256verify": 0x100,
    "e_0x12_never_assigned": 0x12,
    "f_0x200_never_assigned": 0x200,
}


def _pack(g_before_mem: int, success_mem: int) -> Bytecode:
    """success << 64 | RETURNDATASIZE << 32 | (g_before - GAS)."""
    return Op.SSTORE(
        0,
        Op.ADD(
            Op.ADD(
                Op.SHL(64, Op.MLOAD(success_mem)),
                Op.SHL(32, Op.RETURNDATASIZE),
            ),
            Op.SUB(Op.MLOAD(g_before_mem), Op.GAS),
        ),
    )


@pytest.mark.parametrize(
    "addr", [pytest.param(v, id=k) for k, v in ADDRESSES.items()]
)
@pytest.mark.valid_from("Berlin")
def test_probe_bare_call(
    state_test: StateTestFiller, pre: Alloc, addr: int
) -> None:
    """Record success / returndatasize / frame gas delta for a bare call."""
    probe = pre.deploy_contract(
        Op.MSTORE(0x80, Op.GAS)
        + Op.MSTORE(
            0xA0,
            Op.STATICCALL(
                gas=FORWARD,
                address=Address(addr),
                args_offset=0,
                args_size=0,
                ret_offset=0,
                ret_size=0,
            ),
        )
        + _pack(0x80, 0xA0)
        + Op.STOP
    )
    tx = Transaction(to=probe, state_gas_reservoir=0, sender=pre.fund_eoa())
    state_test(
        pre=pre,
        post={probe: Account(storage={0: SENTINEL})},
        tx=tx,
    )


# ---------------------------------------------------------------- modexp cost

# (base_length, exp_length, modulus_length, first exponent byte)
MODEXP_SHAPES = {
    "rsa2048_e65537": (256, 3, 256, 0x01),
    "rsa1024_e65537": (128, 3, 128, 0x01),
    "base32_mod32_e65537": (32, 3, 32, 0x01),
    "base1024_mod1_exp0": (1024, 0, 1, 0x00),
    "base1025_mod1_exp0": (1025, 0, 1, 0x00),
    "base1_mod1024_exp0": (1, 0, 1024, 0x00),
    "base1_mod1025_exp0": (1, 0, 1025, 0x00),
    "base1_mod1_exp1024": (1, 1024, 1, 0x00),
    "base1_mod1_exp1025": (1, 1025, 1, 0x00),
}


def _modexp_input(bl: int, el: int, ml: int, head: int) -> Bytecode:
    """
    Build a modexp input in memory: three 32-byte lengths then zero payload.

    Memory is zero-filled, so base = exp = modulus = 0 unless `head` is set.
    A zero modulus makes the precompile return `modulus_length` zero bytes,
    keeping the arithmetic trivial while the *lengths* -- the only thing
    EIP-7823 and EIP-7883 look at -- stay exactly as declared.
    """
    code = Op.MSTORE(0, bl) + Op.MSTORE(32, el) + Op.MSTORE(64, ml)
    if head and el:
        code += Op.MSTORE8(96 + bl, head)
    return code


@pytest.mark.parametrize(
    "bl,el,ml,head",
    [pytest.param(*v, id=k) for k, v in MODEXP_SHAPES.items()],
)
@pytest.mark.valid_from("Berlin")
def test_probe_modexp_shape(
    state_test: StateTestFiller,
    pre: Alloc,
    bl: int,
    el: int,
    ml: int,
    head: int,
) -> None:
    """Record modexp success and the gas the frame spends on it."""
    total = 96 + bl + el + ml
    probe = pre.deploy_contract(
        _modexp_input(bl, el, ml, head)
        + Op.MSTORE(0x2000, Op.GAS)
        + Op.MSTORE(
            0x2020,
            Op.STATICCALL(
                gas=2_000_000,
                address=Address(0x05),
                args_offset=0,
                args_size=total,
                ret_offset=0x3000,
                ret_size=0,
            ),
        )
        + _pack(0x2000, 0x2020)
        + Op.STOP
    )
    tx = Transaction(
        to=probe,
        gas_limit=10_000_000,
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
    )
    state_test(
        pre=pre,
        post={probe: Account(storage={0: SENTINEL})},
        tx=tx,
    )
