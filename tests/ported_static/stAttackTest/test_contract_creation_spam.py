"""
Test_contract_creation_spam.

Ported from:
state_tests/stAttackTest/ContractCreationSpamFiller.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stAttackTest/ContractCreationSpamFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.slow
@pytest.mark.pre_alloc_mutable
def test_contract_creation_spam(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_contract_creation_spam."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0x6A0A0FC761C612C340A0E98D33B37A75E5268472)
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000000,
    )

    pre[sender] = Account(balance=0xC9F2C9CD04674EDEA40000000)
    # Source: hex
    # 0x7f6004600c60003960046000f3600035ff00000000000000000000000000000000600052602060006000f0600054805b6001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1505a616000106200002f57600055  # noqa: E501
    contract_0 = pre.deploy_contract(  # noqa: F841
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
        nonce=0,
        address=Address(0x6A0A0FC761C612C340A0E98D33B37A75E5268472),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=Bytes(""),
        gas_limit=10000000,
    )

    post = {
        contract_0: Account(storage={0: 0x10C20}, nonce=1),
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

    state_test(env=env, pre=pre, post=post, tx=tx)
