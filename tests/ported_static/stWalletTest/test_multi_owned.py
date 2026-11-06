"""
Call the owner management functions of the `multiOwned` contract.

Ported from:
state_tests/stWalletTest/multiOwnedAddOwnerFiller.json
state_tests/stWalletTest/multiOwnedAddOwnerAddMyselfFiller.json
state_tests/stWalletTest/multiOwnedChangeOwnerFiller.json
state_tests/stWalletTest/multiOwnedChangeOwner_fromNotOwnerFiller.json
state_tests/stWalletTest/multiOwnedChangeOwnerNoArgumentFiller.json
state_tests/stWalletTest/multiOwnedChangeOwner_toIsOwnerFiller.json
state_tests/stWalletTest/multiOwnedChangeRequirementTo0Filler.json
state_tests/stWalletTest/multiOwnedChangeRequirementTo1Filler.json
state_tests/stWalletTest/multiOwnedChangeRequirementTo2Filler.json
state_tests/stWalletTest/multiOwnedIsOwnerFalseFiller.json
state_tests/stWalletTest/multiOwnedIsOwnerTrueFiller.json
state_tests/stWalletTest/multiOwnedRemoveOwnerFiller.json
state_tests/stWalletTest/multiOwnedRemoveOwnerByNonOwnerFiller.json
state_tests/stWalletTest/multiOwnedRemoveOwner_mySelfFiller.json
state_tests/stWalletTest/multiOwnedRemoveOwner_ownerIsNotOwnerFiller.json
state_tests/stWalletTest/multiOwnedRevokeNothingFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytes,
    Hash,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

from tests.ported_static.stWalletTest.wallet_contracts import (
    MULTI_OWNED_CODE,
    MULTI_OWNED_V2_CODE,
    OWNER_INDEX_MAP,
    PENDING_INDEX_SLOT,
    mapping_slot,
    owners_storage,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

ADD_OWNER = Bytes("7065cb48")
CHANGE_OWNER = Bytes("f00d4b5d")
CHANGE_REQUIREMENT = Bytes("ba51a6df")
IS_OWNER = Bytes("2f54bf6e")
REMOVE_OWNER = Bytes("173825d9")
REVOKE = Bytes("b75c7dc6")

RETURN_SENTINEL = 0x5E47


def word(value: int | Address) -> Hash:
    """Return `value` as an ABI-encoded word."""
    return Hash(value, left_padding=True)


@pytest.mark.ported_from(
    [
        "state_tests/stWalletTest/multiOwnedAddOwnerFiller.json",
        "state_tests/stWalletTest/multiOwnedAddOwnerAddMyselfFiller.json",
        "state_tests/stWalletTest/multiOwnedChangeOwnerFiller.json",
        "state_tests/stWalletTest/multiOwnedChangeOwner_fromNotOwnerFiller.json",  # noqa: E501
        "state_tests/stWalletTest/multiOwnedChangeOwnerNoArgumentFiller.json",
        "state_tests/stWalletTest/multiOwnedChangeOwner_toIsOwnerFiller.json",
        "state_tests/stWalletTest/multiOwnedChangeRequirementTo0Filler.json",
        "state_tests/stWalletTest/multiOwnedChangeRequirementTo1Filler.json",
        "state_tests/stWalletTest/multiOwnedChangeRequirementTo2Filler.json",
        "state_tests/stWalletTest/multiOwnedIsOwnerFalseFiller.json",
        "state_tests/stWalletTest/multiOwnedIsOwnerTrueFiller.json",
        "state_tests/stWalletTest/multiOwnedRemoveOwnerFiller.json",
        "state_tests/stWalletTest/multiOwnedRemoveOwnerByNonOwnerFiller.json",
        "state_tests/stWalletTest/multiOwnedRemoveOwner_mySelfFiller.json",
        "state_tests/stWalletTest/multiOwnedRemoveOwner_ownerIsNotOwnerFiller.json",  # noqa: E501
        "state_tests/stWalletTest/multiOwnedRevokeNothingFiller.json",
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "scenario",
    [
        "add_owner",
        "add_owner_add_myself",
        "change_owner",
        "change_owner_from_not_owner",
        "change_owner_no_argument",
        "change_owner_to_is_owner",
        "change_requirement_to0",
        "change_requirement_to1",
        "change_requirement_to2",
        "is_owner_false",
        "is_owner_true",
        "remove_owner",
        "remove_owner_by_non_owner",
        "remove_owner_my_self",
        "remove_owner_owner_is_not_owner",
        "revoke_nothing",
    ],
)
def test_multi_owned(
    state_test: StateTestFiller,
    pre: Alloc,
    scenario: str,
) -> None:
    """Call one `multiOwned` function from the sender."""
    sender = pre.fund_eoa()
    other_owner = pre.nonexistent_account()
    stranger = pre.nonexistent_account()

    code = MULTI_OWNED_CODE
    owners: list[Address] = [sender]
    unchanged = owners_storage(1, owners)
    pending = unchanged | {PENDING_INDEX_SLOT: 1}
    caller_storage: dict | None = None
    data: bytes

    if scenario == "add_owner":
        data = ADD_OWNER + word(other_owner)
        post_storage = owners_storage(1, [sender, other_owner])
    elif scenario == "add_owner_add_myself":
        data = ADD_OWNER + word(sender)
        post_storage = pending
    elif scenario == "change_owner":
        data = CHANGE_OWNER + word(sender) + word(other_owner)
        post_storage = owners_storage(1, [other_owner])
    elif scenario == "change_owner_from_not_owner":
        data = CHANGE_OWNER + word(stranger) + word(other_owner)
        post_storage = pending
    elif scenario == "change_owner_no_argument":
        data = CHANGE_OWNER
        post_storage = pending
    elif scenario == "change_owner_to_is_owner":
        data = CHANGE_OWNER + word(sender) + word(sender)
        post_storage = pending
    elif scenario == "change_requirement_to0":
        data = CHANGE_REQUIREMENT + word(0)
        post_storage = owners_storage(0, owners)
    elif scenario == "change_requirement_to1":
        data = CHANGE_REQUIREMENT + word(1)
        post_storage = unchanged
    elif scenario == "change_requirement_to2":
        data = CHANGE_REQUIREMENT + word(2)
        post_storage = pending
    elif scenario == "is_owner_false":
        data = IS_OWNER + word(stranger)
        post_storage = unchanged
        caller_storage = {0: 0, 1: 0x20}
    elif scenario == "is_owner_true":
        data = IS_OWNER + word(sender)
        post_storage = unchanged
        caller_storage = {0: 1, 1: 0x20}
    elif scenario == "remove_owner":
        code = MULTI_OWNED_V2_CODE
        owners = [sender, other_owner]
        data = REMOVE_OWNER + word(sender)
        post_storage = owners_storage(1, [other_owner])
    elif scenario == "remove_owner_by_non_owner":
        owners = [other_owner]
        data = REMOVE_OWNER + word(other_owner)
        post_storage = owners_storage(1, owners)
    elif scenario == "remove_owner_my_self":
        data = REMOVE_OWNER + word(sender)
        post_storage = pending
    elif scenario == "remove_owner_owner_is_not_owner":
        data = REMOVE_OWNER + word(stranger)
        post_storage = pending
    elif scenario == "revoke_nothing":
        data = REVOKE + word(mapping_slot(sender, OWNER_INDEX_MAP))
        post_storage = unchanged
    else:
        raise ValueError(f"Unknown scenario: {scenario}")

    wallet = pre.deploy_contract(code=code, storage=owners_storage(1, owners))
    post = {wallet: Account(storage=post_storage)}

    to = wallet
    if caller_storage is not None:
        to = pre.deploy_contract(
            code=Op.CALLDATACOPY(0x20, 0, Op.CALLDATASIZE)
            + Op.MSTORE(0, RETURN_SENTINEL)
            + Op.POP(
                Op.CALL(
                    address=wallet,
                    args_offset=0x20,
                    args_size=Op.CALLDATASIZE,
                    ret_offset=0,
                    ret_size=0x20,
                )
            )
            + Op.SSTORE(0, Op.MLOAD(0))
            + Op.SSTORE(1, Op.RETURNDATASIZE),
        )
        post[to] = Account(storage=caller_storage)

    tx = Transaction(sender=sender, to=to, data=data)
    state_test(pre=pre, post=post, tx=tx)
