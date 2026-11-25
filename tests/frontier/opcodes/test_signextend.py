"""Test the SIGNEXTEND opcode."""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    Fork,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
)


def signextend(byte_index: int, value: int) -> int:
    """Return `value` sign-extended from byte `byte_index` (0 = lowest)."""
    if byte_index >= 31:
        return value
    sign_bit = 8 * byte_index + 7
    low = value & ((1 << (sign_bit + 1)) - 1)
    if value >> sign_bit & 1:
        return low | (2**256 - (1 << (sign_bit + 1)))
    return low


@pytest.mark.valid_from("Frontier")
@pytest.mark.parametrize(
    "value",
    [
        # All bytes distinct and nonzero, so each position extends a
        # different sign byte over different lower bytes.
        pytest.param(int.from_bytes(bytes(range(0x01, 0x21))), id="positive"),
        pytest.param(int.from_bytes(bytes(range(0x81, 0xA1))), id="negative"),
    ],
)
def test_signextend(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    value: int,
) -> None:
    """
    Test SIGNEXTEND from every byte position, including the sign bytes of
    the top 64-bit word, on a value with distinct nonzero bytes.
    """
    storage = Storage()
    code = sum(
        (
            Op.SSTORE(
                storage.store_next(signextend(byte_index, value)),
                Op.SIGNEXTEND(byte_index, value),
            )
            for byte_index in range(32)
        ),
        Bytecode(),
    )
    contract = pre.deploy_contract(code)

    state_test(
        pre=pre,
        post={contract: Account(storage=storage)},
        tx=Transaction(
            sender=pre.fund_eoa(),
            to=contract,
            protected=fork.supports_protected_txs(),
        ),
    )
