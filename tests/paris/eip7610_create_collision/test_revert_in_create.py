"""
Test CREATE/CREATE2 collision scenarios with pre-existing storage per EIP-7610.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    Initcode,
    Op,
    StateTestFiller,
    Transaction,
    compute_create2_address,
)

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-7610.md"
REFERENCE_SPEC_VERSION = "80ef48d0bbb5a4939ade51caaaac57b5df6acd4e"

pytestmark = [
    pytest.mark.valid_from("Paris"),
    # We need to modify the pre-alloc to include the collision
    pytest.mark.pre_alloc_modify,
]


@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/tests/tree/v13.3/src/GeneralStateTestsFiller/stCreate2/RevertInCreateInInitCreate2ParisFiller.json",  # noqa: E501
    ],
    pr=["https://github.com/ethereum/execution-specs/pull/2031"],
)
def test_collision_with_create2_revert_in_initcode(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test that a CREATE transaction collision with pre-existing storage causes
    the transaction to fail, even when the initcode would perform CREATE2 with
    reverting inner initcode.

    The initcode (if it were to run) would:
    1. Execute CREATE2 with inner initcode that reverts with 32 bytes of data
    2. Store RETURNDATASIZE to storage slot 0
    3. Copy returndata to memory and store to slot 1

    Since there's a collision (pre-existing storage), the CREATE TX should fail
    and the pre-existing account should remain unchanged.
    """
    inner_initcode = Op.MSTORE(0, 0x112233) + Op.REVERT(0, 32)

    initcode = (
        Op.MSTORE(0, Op.PUSH32(bytes(inner_initcode).ljust(32, b"\0")))
        + Op.CREATE2(value=0, offset=0, size=len(inner_initcode), salt=0)
        + Op.SSTORE(0, Op.RETURNDATASIZE)
        + Op.RETURNDATACOPY(0, 0, 32)
        + Op.SSTORE(1, Op.MLOAD(0))
        + Op.STOP
    )

    sender = pre.fund_eoa()
    tx = Transaction(
        sender=sender,
        to=None,
        data=initcode,
        gas_limit=10_000_000,
    )

    # Pre-existing account with storage - this causes collision per EIP-7610.
    pre[tx.created_contract] = Account(
        balance=10,
        storage={0x00: 0x01},
    )

    state_test(
        pre=pre,
        post={
            (tx.created_contract): Account(
                balance=10,
                nonce=0,
                storage={0x00: 0x01},
            ),
        },
        tx=tx,
    )


@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/tests/tree/v13.3/src/GeneralStateTestsFiller/stCreate2/create2collisionStorageParisFiller.json",  # noqa: E501
    ],
    pr=["https://github.com/ethereum/execution-specs/pull/2031"],
)
@pytest.mark.parametrize(
    "create2_initcode",
    [
        pytest.param(b"", id="empty-initcode"),
        pytest.param(Op.SSTORE(1, 1), id="sstore-initcode"),
        pytest.param(
            Initcode(deploy_code=Op.SSTORE(1, 1)),
            id="initcode-with-deploy",
        ),
    ],
)
def test_create2_collision_storage(
    state_test: StateTestFiller,
    pre: Alloc,
    create2_initcode: Bytecode,
) -> None:
    """
    Test that CREATE2 fails when targeting an address with pre-existing
    storage.

    A CREATE transaction deploys a contract that executes CREATE2. The CREATE2
    target address has pre-existing storage, which should cause the CREATE2 to
    fail per EIP-7610. The deployer stores the CREATE2 result to slot 0 (0 on
    failure).
    """
    deployer_code = (
        Op.MSTORE(0, Op.PUSH32(bytes(create2_initcode).ljust(32, b"\0")))
        + Op.SSTORE(
            0,
            Op.CREATE2(value=0, offset=0, size=len(create2_initcode), salt=0),
        )
        + Op.STOP
    )

    sender = pre.fund_eoa()
    tx = Transaction(
        sender=sender,
        to=None,
        data=deployer_code,
        value=1,
        gas_limit=400_000,
    )

    deployer_address = tx.created_contract

    create2_address = compute_create2_address(
        address=deployer_address,
        salt=0,
        initcode=create2_initcode,
    )

    pre[create2_address] = Account(
        balance=10,
        storage={0x00: 0x01},
    )

    state_test(
        pre=pre,
        post={
            # CREATE2 target unchanged due to collision
            create2_address: Account(
                balance=10,
                nonce=0,
                storage={0x00: 0x01},
            ),
            # Deployer: nonce=2 (1 for creation + 1 for failed CREATE2 attempt)
            # storage[0]=0 indicates CREATE2 returned 0 (failure)
            deployer_address: Account(
                balance=1,
                nonce=2,
                storage={0x00: 0x00},
            ),
        },
        tx=tx,
    )
