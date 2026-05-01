"""
Tests for [EIP-7997: Deterministic Factory Predeploy](https://eips.ethereum.org/EIPS/eip-7997).

The factory at `0x12` interprets calldata as `salt (32) || initcode` and
invokes `CREATE2` with the call value forwarded. It returns the created
address (left-padded to 32 bytes) on success, reverts with the creation-frame
return data on `CREATE2` failure, and reverts with empty data when calldata
is shorter than 32 bytes.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Hash,
    Initcode,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
    compute_create2_address,
)

from .spec import Spec, ref_spec_7997

REFERENCE_SPEC_GIT_PATH = ref_spec_7997.git_path
REFERENCE_SPEC_VERSION = ref_spec_7997.version

pytestmark = pytest.mark.valid_from("Amsterdam")

FACTORY = Spec.FACTORY_ADDRESS


def test_factory_predeploy_account(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """The factory bytecode is present at `0x12` with nonce 1."""
    caller = pre.deploy_contract(
        Op.SSTORE(0, Op.EXTCODESIZE(FACTORY)) + Op.STOP,
    )
    state_test(
        pre=pre,
        tx=Transaction(
            sender=pre.fund_eoa(),
            to=caller,
            gas_limit=200_000,
        ),
        post={
            FACTORY: Account(
                nonce=1,
                code=Spec.FACTORY_BYTECODE,
            ),
            caller: Account(
                storage={0: len(Spec.FACTORY_BYTECODE)},
            ),
        },
    )


def test_factory_deploys_contract(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Calling the factory with `salt || initcode` deploys a contract at the
    expected `CREATE2` address and returns that address.
    """
    salt = 0x42
    runtime_code = Op.PUSH1(0x01) + Op.PUSH1(0x00) + Op.RETURN
    initcode = Initcode(deploy_code=runtime_code)
    expected_address = compute_create2_address(FACTORY, salt, initcode)

    storage = Storage()
    caller = pre.deploy_contract(
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        + Op.SSTORE(
            storage.store_next(1, "factory_call_success"),
            Op.CALL(
                gas=Op.GAS,
                address=FACTORY,
                value=0,
                args_offset=0,
                args_size=Op.CALLDATASIZE,
                ret_offset=0,
                ret_size=32,
            ),
        )
        + Op.SSTORE(
            storage.store_next(expected_address, "returned_address"),
            Op.MLOAD(0),
        )
        + Op.STOP,
    )

    state_test(
        pre=pre,
        tx=Transaction(
            sender=pre.fund_eoa(),
            to=caller,
            data=Hash(salt) + bytes(initcode),
            gas_limit=500_000,
        ),
        post={
            caller: Account(storage=storage),
            expected_address: Account(
                nonce=1,
                code=bytes(runtime_code),
            ),
        },
    )


def test_factory_forwards_value(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """`CALLVALUE` is forwarded from the factory to the created contract."""
    salt = 0x1234
    runtime_code = Op.STOP
    initcode = Initcode(deploy_code=runtime_code)
    expected_address = compute_create2_address(FACTORY, salt, initcode)
    forwarded_value = 0xBA1

    storage = Storage()
    caller = pre.deploy_contract(
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        + Op.SSTORE(
            storage.store_next(1, "factory_call_success"),
            Op.CALL(
                gas=Op.GAS,
                address=FACTORY,
                value=forwarded_value,
                args_offset=0,
                args_size=Op.CALLDATASIZE,
                ret_offset=0,
                ret_size=32,
            ),
        )
        + Op.STOP,
        balance=forwarded_value,
    )

    state_test(
        pre=pre,
        tx=Transaction(
            sender=pre.fund_eoa(),
            to=caller,
            data=Hash(salt) + bytes(initcode),
            gas_limit=500_000,
        ),
        post={
            caller: Account(storage=storage, balance=0),
            expected_address: Account(
                nonce=1,
                balance=forwarded_value,
                code=bytes(runtime_code),
            ),
        },
    )


@pytest.mark.parametrize(
    "calldata",
    [
        pytest.param(b"", id="empty"),
        pytest.param(b"\x00", id="one_byte"),
        pytest.param(b"\xff" * 31, id="thirty_one_bytes"),
    ],
)
def test_factory_reverts_short_calldata(
    state_test: StateTestFiller,
    pre: Alloc,
    calldata: bytes,
) -> None:
    """
    Calldata shorter than 32 bytes makes the factory revert with empty
    return data and no contract is deployed.
    """
    storage = Storage()
    caller = pre.deploy_contract(
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        + Op.SSTORE(
            storage.store_next(0, "call_failed"),
            Op.CALL(
                gas=Op.GAS,
                address=FACTORY,
                value=0,
                args_offset=0,
                args_size=Op.CALLDATASIZE,
                ret_offset=0,
                ret_size=32,
            ),
        )
        + Op.SSTORE(
            storage.store_next(0, "returndatasize"),
            Op.RETURNDATASIZE,
        )
        + Op.STOP,
    )

    state_test(
        pre=pre,
        tx=Transaction(
            sender=pre.fund_eoa(),
            to=caller,
            data=calldata,
            gas_limit=200_000,
        ),
        post={caller: Account(storage=storage)},
    )


def test_factory_propagates_initcode_revert(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    When the initcode reverts with data, the factory reverts with the same
    return data, and no contract is deployed.
    """
    salt = 0x99
    revert_data = bytes.fromhex("deadbeef") + b"\x00" * 28
    initcode = Op.MSTORE(0, int.from_bytes(revert_data, "big")) + Op.REVERT(
        offset=0, size=32
    )
    expected_address = compute_create2_address(FACTORY, salt, initcode)

    storage = Storage()
    caller = pre.deploy_contract(
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        + Op.SSTORE(
            storage.store_next(0, "factory_call_failed"),
            Op.CALL(
                gas=Op.GAS,
                address=FACTORY,
                value=0,
                args_offset=0,
                args_size=Op.CALLDATASIZE,
                ret_offset=0,
                ret_size=32,
            ),
        )
        + Op.SSTORE(
            storage.store_next(32, "returndatasize"),
            Op.RETURNDATASIZE,
        )
        + Op.RETURNDATACOPY(0, 0, Op.RETURNDATASIZE)
        + Op.SSTORE(
            storage.store_next(
                int.from_bytes(revert_data, "big"), "revert_payload"
            ),
            Op.MLOAD(0),
        )
        + Op.STOP,
    )

    state_test(
        pre=pre,
        tx=Transaction(
            sender=pre.fund_eoa(),
            to=caller,
            data=Hash(salt) + bytes(initcode),
            gas_limit=500_000,
        ),
        post={
            caller: Account(storage=storage),
            expected_address: Account.NONEXISTENT,
        },
    )


def test_factory_address_collision_reverts(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    A second deployment to the same `CREATE2` target reverts. `CREATE2`
    fails when the destination already has code, returns 0, and the factory
    reverts with the (empty) creation-frame return data.
    """
    salt = 0x77
    runtime_code = Op.STOP
    initcode = Initcode(deploy_code=runtime_code)
    target = compute_create2_address(FACTORY, salt, initcode)

    storage = Storage()
    caller = pre.deploy_contract(
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        + Op.SSTORE(
            storage.store_next(1, "first_call_success"),
            Op.CALL(
                gas=Op.GAS,
                address=FACTORY,
                value=0,
                args_offset=0,
                args_size=Op.CALLDATASIZE,
                ret_offset=0x100,
                ret_size=32,
            ),
        )
        + Op.SSTORE(
            storage.store_next(0, "second_call_failed"),
            Op.CALL(
                gas=Op.GAS,
                address=FACTORY,
                value=0,
                args_offset=0,
                args_size=Op.CALLDATASIZE,
                ret_offset=0x100,
                ret_size=32,
            ),
        )
        + Op.STOP,
    )

    state_test(
        pre=pre,
        tx=Transaction(
            sender=pre.fund_eoa(),
            to=caller,
            data=Hash(salt) + bytes(initcode),
            gas_limit=1_000_000,
        ),
        post={
            caller: Account(storage=storage),
            target: Account(nonce=1, code=bytes(runtime_code)),
        },
    )
