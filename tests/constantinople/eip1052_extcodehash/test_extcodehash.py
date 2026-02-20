"""
Test EIP-1052 EXTCODEHASH.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
    compute_create2_address,
    compute_create_address,
)

from ethereum.crypto.hash import keccak256

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-1052.md"
REFERENCE_SPEC_VERSION = "2dcbc7ce1563e9624e137e9d447374600af876fa"

pytestmark = [
    pytest.mark.valid_from("ConstantinopleFix"),
]


@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stExtCodeHash/extCodeHashSelfFiller.json",  # noqa: E501
    ],
    pr=["https://github.com/ethereum/execution-specs/pull/2249"],
)
def test_extcodehash_self(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test EXTCODEHASH/EXTCODESIZE of the currently executing account.
    """
    storage = Storage()
    slot_hash = storage.store_next(0)
    slot_size = storage.store_next(0)

    code = Op.SSTORE(slot_hash, Op.EXTCODEHASH(Op.ADDRESS)) + Op.SSTORE(
        slot_size, Op.EXTCODESIZE(Op.ADDRESS)
    )

    storage[slot_hash] = code.keccak256()
    storage[slot_size] = len(code)

    code_address = pre.deploy_contract(code)

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=code_address,
        gas_limit=400_000,
    )

    state_test(
        pre=pre,
        post={code_address: Account(storage=storage)},
        tx=tx,
    )


@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stExtCodeHash/extCodeHashNonExistingAccountFiller.yml",  # noqa: E501
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stExtCodeHash/extCodeHashAccountWithoutCodeFiller.yml",  # noqa: E501
    ],
    pr=["https://github.com/ethereum/execution-specs/pull/2237"],
)
@pytest.mark.parametrize("target_exists", [True, False])
def test_extcodehash_of_empty(
    state_test: StateTestFiller,
    pre: Alloc,
    target_exists: bool,
) -> None:
    """
    Test EXTCODEHASH/EXTCODESIZE for non-existent and empty accounts.
    """
    storage = Storage()
    target_address = pre.empty_account()

    if target_exists:
        pre.fund_address(target_address, 1)

    expected_hash = keccak256(b"") if target_exists else 0
    code = Op.SSTORE(
        storage.store_next(expected_hash),
        Op.EXTCODEHASH(target_address),
    ) + Op.SSTORE(
        storage.store_next(0),
        Op.EXTCODESIZE(target_address),
    )

    code_address = pre.deploy_contract(code)

    tx = Transaction(
        sender=(pre.fund_eoa()),
        to=code_address,
        value=1,
        gas_limit=400_000,
    )

    state_test(
        pre=pre,
        post={
            code_address: Account(storage=storage),
        },
        tx=tx,
    )


@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stExtCodeHash/extcodehashEmpty_ParisFiller.yml",  # noqa: E501
    ],
    pr=["https://github.com/ethereum/execution-specs/pull/2237"],
)
def test_extcodehash_empty_send_value(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test EXTCODEHASH of non-existent account before and after sending value.

    Verify that EXTCODEHASH transitions from 0 to keccak256("") when
    the account receives value within the same transaction.
    """
    storage = Storage()
    target_address = pre.empty_account()

    code = (
        # EXTCODEHASH before sending value: expect 0 (non-existent).
        Op.SSTORE(
            storage.store_next(0),
            Op.EXTCODEHASH(target_address),
        )
        # Send 1 wei to target, creating the account.
        + Op.CALL(gas=Op.GAS, address=target_address, value=1)
        # EXTCODEHASH after sending value: expect keccak256("").
        + Op.SSTORE(
            storage.store_next(keccak256(b"")),
            Op.EXTCODEHASH(target_address),
        )
    )

    code_address = pre.deploy_contract(code, balance=10**18)

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=code_address,
        gas_limit=400_000,
    )

    state_test(
        pre=pre,
        post={
            code_address: Account(storage=storage),
        },
        tx=tx,
    )


@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stExtCodeHash/extcodehashEmpty_ParisFiller.yml",  # noqa: E501
    ],
    pr=["https://github.com/ethereum/execution-specs/pull/2237"],
)
@pytest.mark.pre_alloc_mutable
@pytest.mark.parametrize(
    "account,call_before,expected_hash,expected_size,expected_copy",
    [
        pytest.param(
            Account(nonce=1),
            False,
            keccak256(b""),
            0,
            0,
            id="nonce-only",
        ),
        pytest.param(
            Account(balance=1),
            False,
            keccak256(b""),
            0,
            0,
            id="balance-only",
        ),
        pytest.param(
            Account(
                balance=10,
                storage={0x00: 0x01000000, 0xFFFFFFF: 0xFFFFFFFF},
            ),
            False,
            keccak256(b""),
            0,
            0,
            id="balance-storage",
        ),
        pytest.param(
            Account(code=Op.STOP),
            False,
            keccak256(bytes(Op.STOP)),
            1,
            0,
            id="single-byte-code",
        ),
        pytest.param(
            Account(balance=100, code=Op.PUSH2(0x60A7) + Op.SELFDESTRUCT),
            True,
            keccak256(bytes(Op.PUSH2(0x60A7) + Op.SELFDESTRUCT)),
            4,
            bytes(Op.PUSH2(0x60A7) + Op.SELFDESTRUCT).ljust(32, b"\0"),
            id="selfdestruct",
        ),
    ],
)
def test_extcodehash_empty_account_variants(
    state_test: StateTestFiller,
    pre: Alloc,
    account: Account,
    call_before: bool,
    expected_hash: bytes,
    expected_size: int,
    expected_copy: int | bytes,
) -> None:
    """
    Test EXTCODEHASH/EXTCODESIZE/EXTCODECOPY for empty-account variants.
    """
    storage = Storage()
    target_address = pre.empty_account()
    pre[target_address] = account

    code = Op.JUMPDEST + (
        Op.CALL(gas=Op.GAS, address=target_address, value=0)
        if call_before
        else Op.NOOP
    )

    code += (
        Op.SSTORE(
            storage.store_next(expected_size),
            Op.EXTCODESIZE(target_address),
        )
        + Op.SSTORE(
            storage.store_next(expected_hash),
            Op.EXTCODEHASH(target_address),
        )
        + Op.EXTCODECOPY(target_address, 0, 0, 32)
        + Op.SSTORE(
            storage.store_next(expected_copy),
            Op.MLOAD(0),
        )
    )

    code_address = pre.deploy_contract(code, balance=10**18)

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=code_address,
        value=1,
        gas_limit=400_000,
    )

    state_test(
        pre=pre,
        post={
            code_address: Account(storage=storage),
        },
        tx=tx,
    )


@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stExtCodeHash/extcodehashEmpty_ParisFiller.yml",  # noqa: E501
    ],
    pr=["https://github.com/ethereum/execution-specs/pull/2237"],
)
@pytest.mark.parametrize("opcode", [Op.CREATE, Op.CREATE2])
def test_extcodehash_empty_contract_creation(
    state_test: StateTestFiller,
    pre: Alloc,
    opcode: Op,
) -> None:
    """
    Test EXTCODEHASH/EXTCODESIZE for empty contracts created with
    CREATE/CREATE2.
    """
    storage = Storage()
    initcode = Op.RETURN(0, 0)
    expected_hash = keccak256(b"")

    created_slot = storage.store_next(0)
    hash_slot = storage.store_next(expected_hash)
    size_slot = storage.store_next(0)
    copy_slot = storage.store_next(0)

    create_op = (
        opcode(value=0, offset=0, size=len(initcode), salt=0)
        if opcode == Op.CREATE2
        else opcode(value=0, offset=0, size=len(initcode))
    )

    code = (
        Op.MSTORE(0, Op.PUSH32(bytes(initcode).ljust(32, b"\0")))
        + Op.SSTORE(created_slot, create_op)
        + Op.SSTORE(
            hash_slot,
            Op.EXTCODEHASH(Op.SLOAD(created_slot)),
        )
        + Op.SSTORE(
            size_slot,
            Op.EXTCODESIZE(Op.SLOAD(created_slot)),
        )
        + Op.EXTCODECOPY(Op.SLOAD(created_slot), 0, 0, 32)
        + Op.SSTORE(copy_slot, Op.MLOAD(0))
        + Op.STOP
    )

    code_address = pre.deploy_contract(code)
    created_address = (
        compute_create2_address(
            address=code_address,
            salt=0,
            initcode=initcode,
        )
        if opcode == Op.CREATE2
        else compute_create_address(address=code_address, nonce=1)
    )
    storage[created_slot] = created_address

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=code_address,
        gas_limit=400_000,
    )

    state_test(
        pre=pre,
        post={
            code_address: Account(storage=storage),
            created_address: Account(nonce=1, code=b""),
        },
        tx=tx,
    )
