"""
THROWAWAY MEASUREMENT INSTRUMENT -- its failures are the measurement.

For each precompile shape, forwards a LADDER of frozen gas budgets and packs
the six success bits into one word (`bit i` set iff `budgets[i]` sufficed),
then asserts a wrong sentinel so the mismatch prints the bitmask. A bitmask
of 0b111000 means "the top three budgets suffice, the bottom three do not",
which locates the price between `budgets[2]` and `budgets[3]`.

Run (from tests/deployed_idioms/):
  python3 tools/locked_fill.py /abs/.../test_precompile_price_probe.py \
     --from Berlin --until Amsterdam --output <unique> -q -p no:cacheprovider
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

# secp256r1 (P-256) field prime, and p-2: the exponent both deployed
# `primemod(value, p)` wrappers pass to modexp for a modular inverse by
# Fermat's little theorem.
P256_P = 0xFFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFF
P256_P_MINUS_2 = P256_P - 2

# name -> (address, setup bytecode, input length, six ascending budgets)
SHAPES = {
    # 128 zero bytes = infinity + infinity. EIP-1108 cut ECADD 500 -> 150.
    "ecadd_infinity": (0x06, Bytecode(), 128, [148, 149, 150, 151, 499, 500]),
    # 96 zero bytes = infinity * 0. EIP-1108 cut ECMUL 40,000 -> 6,000.
    # 6,000 and 8,000 are deployed literals (see README).
    "ecmul_infinity": (
        0x07,
        Bytecode(),
        96,
        [5_999, 6_000, 6_001, 8_000, 39_999, 40_000],
    ),
    # 0 bytes = zero pairs: charges ECPAIRING_BASE alone.
    "ecpairing_0pt": (
        0x08,
        Bytecode(),
        0,
        [44_999, 45_000, 45_001, 60_000, 99_999, 100_000],
    ),
    # 192 zero bytes = one pair of infinities: BASE + 1 x PER_POINT.
    "ecpairing_1pt": (
        0x08,
        Bytecode(),
        192,
        [78_999, 79_000, 79_001, 100_000, 179_999, 180_000],
    ),
    # 32/32/32 modexp with exponent p-2: exactly what a deployed account-abstraction stack's
    # a passkey validation module and the a sibling fallback handler pass, under
    # frozen literals of 1,500 and 14,000 respectively.
    "modexp_p256_inverse": (
        0x05,
        Op.MSTORE(0, 32)
        + Op.MSTORE(32, 32)
        + Op.MSTORE(64, 32)
        + Op.MSTORE(96, 1)
        + Op.MSTORE(128, P256_P_MINUS_2)
        + Op.MSTORE(160, P256_P),
        192,
        [1_359, 1_360, 1_500, 4_079, 4_080, 14_000],
    ),
}


@pytest.mark.parametrize(
    "addr,setup,in_len,budgets",
    [pytest.param(*v, id=k) for k, v in SHAPES.items()],
)
@pytest.mark.valid_from("Berlin")
def test_probe_price_ladder(
    state_test: StateTestFiller,
    pre: Alloc,
    addr: int,
    setup: Bytecode,
    in_len: int,
    budgets: list,
) -> None:
    """Pack `success(budgets[i]) << i` for six ascending budgets."""
    code = setup
    for i, b in enumerate(budgets):
        code += Op.MSTORE(
            0x1000 + 32 * i,
            Op.STATICCALL(
                gas=b,
                address=Address(addr),
                args_offset=0,
                args_size=in_len,
                ret_offset=0x2000,
                ret_size=0,
            ),
        )
    total: Bytecode | None = None
    for i in range(len(budgets)):
        term = Op.SHL(i, Op.MLOAD(0x1000 + 32 * i))
        total = term if total is None else Op.ADD(total, term)
    code += Op.SSTORE(0, total) + Op.STOP

    probe = pre.deploy_contract(code)
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
