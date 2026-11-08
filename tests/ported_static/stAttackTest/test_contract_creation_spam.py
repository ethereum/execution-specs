"""
Test_contract_creation_spam.

Ported from:
state_tests/stAttackTest/ContractCreationSpamFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytes,
    StateTestFiller,
    Storage,
    Transaction,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stAttackTest/ContractCreationSpamFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.slow
def test_contract_creation_spam(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Test_contract_creation_spam."""
    sender = pre.fund_eoa(amount=0xC9F2C9CD04674EDEA40000000)

    # Source: hex
    # 0x7f6004600c60003960046000f3600035ff00000000000000000000000000000000600052602060006000f0600054805b6001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1505a616000106200002f57600055  # noqa: E501
    contract_0 = pre.deploy_contract(
        code=Op.MSTORE(
            offset=0x0,
            value=0x6004600C60003960046000F3600035FF00000000000000000000000000000000,  # noqa: E501
        )
        + Op.CREATE(value=0x0, offset=0x0, size=0x20)
        + Op.SLOAD(key=0x0)
        + Op.DUP1
        + Op.JUMPDEST
        + Op.PUSH1[0x1]
        + Op.ADD
        + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(
            Op.CALL(
                gas=0x6,
                address=Op.DUP8,
                value=Op.DUP1,
                args_offset=Op.DUP2,
                args_size=0x20,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
        )
        + Op.PUSH1[0x1]
        + Op.ADD
        + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(
            Op.CALL(
                gas=0x6,
                address=Op.DUP8,
                value=Op.DUP1,
                args_offset=Op.DUP2,
                args_size=0x20,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
        )
        + Op.PUSH1[0x1]
        + Op.ADD
        + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(
            Op.CALL(
                gas=0x6,
                address=Op.DUP8,
                value=Op.DUP1,
                args_offset=Op.DUP2,
                args_size=0x20,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
        )
        + Op.PUSH1[0x1]
        + Op.ADD
        + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(
            Op.CALL(
                gas=0x6,
                address=Op.DUP8,
                value=Op.DUP1,
                args_offset=Op.DUP2,
                args_size=0x20,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
        )
        + Op.PUSH1[0x1]
        + Op.ADD
        + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(
            Op.CALL(
                gas=0x6,
                address=Op.DUP8,
                value=Op.DUP1,
                args_offset=Op.DUP2,
                args_size=0x20,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
        )
        + Op.PUSH1[0x1]
        + Op.ADD
        + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(
            Op.CALL(
                gas=0x6,
                address=Op.DUP8,
                value=Op.DUP1,
                args_offset=Op.DUP2,
                args_size=0x20,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
        )
        + Op.PUSH1[0x1]
        + Op.ADD
        + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(
            Op.CALL(
                gas=0x6,
                address=Op.DUP8,
                value=Op.DUP1,
                args_offset=Op.DUP2,
                args_size=0x20,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
        )
        + Op.PUSH1[0x1]
        + Op.ADD
        + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(
            Op.CALL(
                gas=0x6,
                address=Op.DUP8,
                value=Op.DUP1,
                args_offset=Op.DUP2,
                args_size=0x20,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
        )
        + Op.PUSH1[0x1]
        + Op.ADD
        + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(
            Op.CALL(
                gas=0x6,
                address=Op.DUP8,
                value=Op.DUP1,
                args_offset=Op.DUP2,
                args_size=0x20,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
        )
        + Op.PUSH1[0x1]
        + Op.ADD
        + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(
            Op.CALL(
                gas=0x6,
                address=Op.DUP8,
                value=Op.DUP1,
                args_offset=Op.DUP2,
                args_size=0x20,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
        )
        + Op.PUSH1[0x1]
        + Op.ADD
        + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(
            Op.CALL(
                gas=0x6,
                address=Op.DUP8,
                value=Op.DUP1,
                args_offset=Op.DUP2,
                args_size=0x20,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
        )
        + Op.PUSH1[0x1]
        + Op.ADD
        + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(
            Op.CALL(
                gas=0x6,
                address=Op.DUP8,
                value=Op.DUP1,
                args_offset=Op.DUP2,
                args_size=0x20,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
        )
        + Op.PUSH1[0x1]
        + Op.ADD
        + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(
            Op.CALL(
                gas=0x6,
                address=Op.DUP8,
                value=Op.DUP1,
                args_offset=Op.DUP2,
                args_size=0x20,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
        )
        + Op.PUSH1[0x1]
        + Op.ADD
        + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(
            Op.CALL(
                gas=0x6,
                address=Op.DUP8,
                value=Op.DUP1,
                args_offset=Op.DUP2,
                args_size=0x20,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
        )
        + Op.PUSH1[0x1]
        + Op.ADD
        + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(
            Op.CALL(
                gas=0x6,
                address=Op.DUP8,
                value=Op.DUP1,
                args_offset=Op.DUP2,
                args_size=0x20,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
        )
        + Op.PUSH1[0x1]
        + Op.ADD
        + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(
            Op.CALL(
                gas=0x6,
                address=Op.DUP8,
                value=Op.DUP1,
                args_offset=Op.DUP2,
                args_size=0x20,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
        )
        + Op.PUSH1[0x1]
        + Op.ADD
        + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(
            Op.CALL(
                gas=0x6,
                address=Op.DUP8,
                value=Op.DUP1,
                args_offset=Op.DUP2,
                args_size=0x20,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
        )
        + Op.PUSH1[0x1]
        + Op.ADD
        + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(
            Op.CALL(
                gas=0x6,
                address=Op.DUP8,
                value=Op.DUP1,
                args_offset=Op.DUP2,
                args_size=0x20,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
        )
        + Op.PUSH1[0x1]
        + Op.ADD
        + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(
            Op.CALL(
                gas=0x6,
                address=Op.DUP8,
                value=Op.DUP1,
                args_offset=Op.DUP2,
                args_size=0x20,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
        )
        + Op.PUSH1[0x1]
        + Op.ADD
        + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(
            Op.CALL(
                gas=0x6,
                address=Op.DUP8,
                value=Op.DUP1,
                args_offset=Op.DUP2,
                args_size=0x20,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
        )
        + Op.PUSH1[0x1]
        + Op.ADD
        + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(
            Op.CALL(
                gas=0x6,
                address=Op.DUP8,
                value=Op.DUP1,
                args_offset=Op.DUP2,
                args_size=0x20,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
        )
        + Op.PUSH1[0x1]
        + Op.ADD
        + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(
            Op.CALL(
                gas=0x6,
                address=Op.DUP8,
                value=Op.DUP1,
                args_offset=Op.DUP2,
                args_size=0x20,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
        )
        + Op.PUSH1[0x1]
        + Op.ADD
        + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(
            Op.CALL(
                gas=0x6,
                address=Op.DUP8,
                value=Op.DUP1,
                args_offset=Op.DUP2,
                args_size=0x20,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
        )
        + Op.PUSH1[0x1]
        + Op.ADD
        + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(
            Op.CALL(
                gas=0x6,
                address=Op.DUP8,
                value=Op.DUP1,
                args_offset=Op.DUP2,
                args_size=0x20,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
        )
        + Op.PUSH1[0x1]
        + Op.ADD
        + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(
            Op.CALL(
                gas=0x6,
                address=Op.DUP8,
                value=Op.DUP1,
                args_offset=Op.DUP2,
                args_size=0x20,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
        )
        + Op.PUSH1[0x1]
        + Op.ADD
        + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(
            Op.CALL(
                gas=0x6,
                address=Op.DUP8,
                value=Op.DUP1,
                args_offset=Op.DUP2,
                args_size=0x20,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
        )
        + Op.PUSH1[0x1]
        + Op.ADD
        + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(
            Op.CALL(
                gas=0x6,
                address=Op.DUP8,
                value=Op.DUP1,
                args_offset=Op.DUP2,
                args_size=0x20,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
        )
        + Op.PUSH1[0x1]
        + Op.ADD
        + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(
            Op.CALL(
                gas=0x6,
                address=Op.DUP8,
                value=Op.DUP1,
                args_offset=Op.DUP2,
                args_size=0x20,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
        )
        + Op.PUSH1[0x1]
        + Op.ADD
        + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(
            Op.CALL(
                gas=0x6,
                address=Op.DUP8,
                value=Op.DUP1,
                args_offset=Op.DUP2,
                args_size=0x20,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
        )
        + Op.PUSH1[0x1]
        + Op.ADD
        + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(
            Op.CALL(
                gas=0x6,
                address=Op.DUP8,
                value=Op.DUP1,
                args_offset=Op.DUP2,
                args_size=0x20,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
        )
        + Op.PUSH1[0x1]
        + Op.ADD
        + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(
            Op.CALL(
                gas=0x6,
                address=Op.DUP8,
                value=Op.DUP1,
                args_offset=Op.DUP2,
                args_size=0x20,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
        )
        + Op.PUSH1[0x1]
        + Op.ADD
        + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(
            Op.CALL(
                gas=0x6,
                address=Op.DUP8,
                value=Op.DUP1,
                args_offset=Op.DUP2,
                args_size=0x20,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
        )
        + Op.PUSH1[0x1]
        + Op.ADD
        + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(
            Op.CALL(
                gas=0x6,
                address=Op.DUP8,
                value=Op.DUP1,
                args_offset=Op.DUP2,
                args_size=0x20,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
        )
        + Op.PUSH1[0x1]
        + Op.ADD
        + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(
            Op.CALL(
                gas=0x6,
                address=Op.DUP8,
                value=Op.DUP1,
                args_offset=Op.DUP2,
                args_size=0x20,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
        )
        + Op.PUSH1[0x1]
        + Op.ADD
        + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(
            Op.CALL(
                gas=0x6,
                address=Op.DUP8,
                value=Op.DUP1,
                args_offset=Op.DUP2,
                args_size=0x20,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
        )
        + Op.PUSH1[0x1]
        + Op.ADD
        + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(
            Op.CALL(
                gas=0x6,
                address=Op.DUP8,
                value=Op.DUP1,
                args_offset=Op.DUP2,
                args_size=0x20,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
        )
        + Op.PUSH1[0x1]
        + Op.ADD
        + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(
            Op.CALL(
                gas=0x6,
                address=Op.DUP8,
                value=Op.DUP1,
                args_offset=Op.DUP2,
                args_size=0x20,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
        )
        + Op.PUSH1[0x1]
        + Op.ADD
        + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(
            Op.CALL(
                gas=0x6,
                address=Op.DUP8,
                value=Op.DUP1,
                args_offset=Op.DUP2,
                args_size=0x20,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
        )
        + Op.PUSH1[0x1]
        + Op.ADD
        + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(
            Op.CALL(
                gas=0x6,
                address=Op.DUP8,
                value=Op.DUP1,
                args_offset=Op.DUP2,
                args_size=0x20,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
        )
        + Op.PUSH1[0x1]
        + Op.ADD
        + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(
            Op.CALL(
                gas=0x6,
                address=Op.DUP8,
                value=Op.DUP1,
                args_offset=Op.DUP2,
                args_size=0x20,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
        )
        + Op.JUMPI(pc=Op.PUSH3[0x2F], condition=Op.LT(0x6000, Op.GAS))
        + Op.PUSH1[0x0]
        + Op.SSTORE,
        balance=0xDE0B6B3A7640000,
    )

    gas_limit = 10000000
    if fork.is_eip_enabled(8037):
        gas_limit += 100 * fork.gas_costs().NEW_ACCOUNT
    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=Bytes(""),
        gas_limit=gas_limit,
    )

    contract_0_storage = Storage.model_validate({0: 0x10C20})
    if fork.is_eip_enabled(8037):
        contract_0_storage = Storage.model_validate({})
        contract_0_storage.set_expect_any(0)
    post = {
        contract_0: Account(storage=contract_0_storage, nonce=2),
        sender: Account(storage={}, nonce=1),
        Address(
            0x0000000000000000000000000000000000000001
        ): Account.NONEXISTENT,
        Address(
            0x0000000000000000000000000000000000000002
        ): Account.NONEXISTENT,
        Address(
            0x0000000000000000000000000000000000000003
        ): Account.NONEXISTENT,
        Address(
            0x0000000000000000000000000000000000000004
        ): Account.NONEXISTENT,
        Address(
            0x0000000000000000000000000000000000000005
        ): Account.NONEXISTENT,
        Address(
            0x0000000000000000000000000000000000000006
        ): Account.NONEXISTENT,
        Address(
            0x0000000000000000000000000000000000000015
        ): Account.NONEXISTENT,
        Address(
            0x000000000000000000000000000000000000006E
        ): Account.NONEXISTENT,
        Address(
            0x0000000000000000000000000000000000002170
        ): Account.NONEXISTENT,
    }

    state_test(pre=pre, post=post, tx=tx)
