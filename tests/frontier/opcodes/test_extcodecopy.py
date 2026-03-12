"""Test `EXTCODECOPY` opcode."""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytes,
    Fork,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
)


@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stExtCodeHash/extCodeCopyBoundsFiller.yml",  # noqa: E501
    ],
    pr=["https://github.com/ethereum/execution-specs/pull/2417"],
)
def test_extcodecopy_bounds(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test EXTCODECOPY with out-of-bounds code offset.

    Perform three EXTCODECOPY operations on a 15-byte target contract:
    1. Huge code offset + large size  -> all zeros (beyond code)
    2. Huge code offset + small size  -> all zeros (beyond code)
    3. Offset 5 + size 12             -> partial code copy + zero padding

    Each result is read via MLOAD(0) and MLOAD(32) and stored. Only the
    third operation produces a non-zero result because the dest_offset=1
    shifts the copied bytes into the MLOAD(0) word.
    """
    storage = Storage()

    target_code = Op.SSTORE(99, 12) + Op.SSTORE(99, 11) + Op.SSTORE(99, 10)
    target = pre.deploy_contract(target_code)

    huge_offset = 0x010000000000000000000000000000000000000000
    large_size = 5000

    code = (
        # 1. Huge code offset, large size -> all zeros
        Op.EXTCODECOPY(target, 1, huge_offset, large_size)
        + Op.SSTORE(storage.store_next(0), Op.MLOAD(0))
        + Op.SSTORE(storage.store_next(0), Op.MLOAD(32))
        + Op.SSTORE(
            storage.store_next(Bytes(b"\0" * large_size).keccak256()),
            Op.SHA3(1, large_size),
        )
        # 2. Huge code offset, size 12 -> all zeros
        + Op.EXTCODECOPY(target, 1, huge_offset, 12)
        + Op.SSTORE(storage.store_next(0), Op.MLOAD(0))
        + Op.SSTORE(storage.store_next(0), Op.MLOAD(32))
        # 3. Offset 5, size 12 -> partial code copy
        + Op.EXTCODECOPY(target, 1, 5, 12)
        + Op.SSTORE(
            storage.store_next(
                b"\x00" + bytes(target_code)[5:15] + b"\x00" * 21
            ),
            Op.MLOAD(0),
        )
        + Op.SSTORE(storage.store_next(0), Op.MLOAD(32))
    )

    code_address = pre.deploy_contract(code, storage=storage.canary())

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=code_address,
        gas_limit=400_000,
        protected=fork.supports_protected_txs(),
    )

    state_test(
        pre=pre,
        post={code_address: Account(storage=storage)},
        tx=tx,
    )
