"""
test_contract_creation_spam

Ported from:
state_tests/stAttackTest/ContractCreationSpamFiller.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
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
@pytest.mark.pre_alloc_mutable
def test_contract_creation_spam(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_contract_creation_spam"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    contract_0 = Address("0x6a0a0fc761c612c340a0e98d33b37a75e5268472")
    sender = EOA(
        key=0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000000,
    )

    # Source: hex
    # 0x7f6004600c60003960046000f3600035ff00000000000000000000000000000000600052602060006000f0600054805b6001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1506001018060005260008060208180876006f1505a616000106200002f57600055
    contract_0 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=0x6004600c60003960046000f3600035ff00000000000000000000000000000000)
        + Op.CREATE(value=0x0, offset=0x0, size=0x20) + Op.SLOAD(key=0x0)
        + Op.DUP1 + Op.JUMPDEST + Op.PUSH1[0x1] + Op.ADD
        + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(Op.CALL(gas=0x6, address=Op.DUP8, value=Op.DUP1, args_offset=Op.DUP2, args_size=0x20, ret_offset=Op.DUP1, ret_size=0x0))
        + Op.PUSH1[0x1] + Op.ADD + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(Op.CALL(gas=0x6, address=Op.DUP8, value=Op.DUP1, args_offset=Op.DUP2, args_size=0x20, ret_offset=Op.DUP1, ret_size=0x0))
        + Op.PUSH1[0x1] + Op.ADD + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(Op.CALL(gas=0x6, address=Op.DUP8, value=Op.DUP1, args_offset=Op.DUP2, args_size=0x20, ret_offset=Op.DUP1, ret_size=0x0))
        + Op.PUSH1[0x1] + Op.ADD + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(Op.CALL(gas=0x6, address=Op.DUP8, value=Op.DUP1, args_offset=Op.DUP2, args_size=0x20, ret_offset=Op.DUP1, ret_size=0x0))
        + Op.PUSH1[0x1] + Op.ADD + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(Op.CALL(gas=0x6, address=Op.DUP8, value=Op.DUP1, args_offset=Op.DUP2, args_size=0x20, ret_offset=Op.DUP1, ret_size=0x0))
        + Op.PUSH1[0x1] + Op.ADD + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(Op.CALL(gas=0x6, address=Op.DUP8, value=Op.DUP1, args_offset=Op.DUP2, args_size=0x20, ret_offset=Op.DUP1, ret_size=0x0))
        + Op.PUSH1[0x1] + Op.ADD + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(Op.CALL(gas=0x6, address=Op.DUP8, value=Op.DUP1, args_offset=Op.DUP2, args_size=0x20, ret_offset=Op.DUP1, ret_size=0x0))
        + Op.PUSH1[0x1] + Op.ADD + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(Op.CALL(gas=0x6, address=Op.DUP8, value=Op.DUP1, args_offset=Op.DUP2, args_size=0x20, ret_offset=Op.DUP1, ret_size=0x0))
        + Op.PUSH1[0x1] + Op.ADD + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(Op.CALL(gas=0x6, address=Op.DUP8, value=Op.DUP1, args_offset=Op.DUP2, args_size=0x20, ret_offset=Op.DUP1, ret_size=0x0))
        + Op.PUSH1[0x1] + Op.ADD + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(Op.CALL(gas=0x6, address=Op.DUP8, value=Op.DUP1, args_offset=Op.DUP2, args_size=0x20, ret_offset=Op.DUP1, ret_size=0x0))
        + Op.PUSH1[0x1] + Op.ADD + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(Op.CALL(gas=0x6, address=Op.DUP8, value=Op.DUP1, args_offset=Op.DUP2, args_size=0x20, ret_offset=Op.DUP1, ret_size=0x0))
        + Op.PUSH1[0x1] + Op.ADD + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(Op.CALL(gas=0x6, address=Op.DUP8, value=Op.DUP1, args_offset=Op.DUP2, args_size=0x20, ret_offset=Op.DUP1, ret_size=0x0))
        + Op.PUSH1[0x1] + Op.ADD + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(Op.CALL(gas=0x6, address=Op.DUP8, value=Op.DUP1, args_offset=Op.DUP2, args_size=0x20, ret_offset=Op.DUP1, ret_size=0x0))
        + Op.PUSH1[0x1] + Op.ADD + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(Op.CALL(gas=0x6, address=Op.DUP8, value=Op.DUP1, args_offset=Op.DUP2, args_size=0x20, ret_offset=Op.DUP1, ret_size=0x0))
        + Op.PUSH1[0x1] + Op.ADD + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(Op.CALL(gas=0x6, address=Op.DUP8, value=Op.DUP1, args_offset=Op.DUP2, args_size=0x20, ret_offset=Op.DUP1, ret_size=0x0))
        + Op.PUSH1[0x1] + Op.ADD + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(Op.CALL(gas=0x6, address=Op.DUP8, value=Op.DUP1, args_offset=Op.DUP2, args_size=0x20, ret_offset=Op.DUP1, ret_size=0x0))
        + Op.PUSH1[0x1] + Op.ADD + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(Op.CALL(gas=0x6, address=Op.DUP8, value=Op.DUP1, args_offset=Op.DUP2, args_size=0x20, ret_offset=Op.DUP1, ret_size=0x0))
        + Op.PUSH1[0x1] + Op.ADD + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(Op.CALL(gas=0x6, address=Op.DUP8, value=Op.DUP1, args_offset=Op.DUP2, args_size=0x20, ret_offset=Op.DUP1, ret_size=0x0))
        + Op.PUSH1[0x1] + Op.ADD + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(Op.CALL(gas=0x6, address=Op.DUP8, value=Op.DUP1, args_offset=Op.DUP2, args_size=0x20, ret_offset=Op.DUP1, ret_size=0x0))
        + Op.PUSH1[0x1] + Op.ADD + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(Op.CALL(gas=0x6, address=Op.DUP8, value=Op.DUP1, args_offset=Op.DUP2, args_size=0x20, ret_offset=Op.DUP1, ret_size=0x0))
        + Op.PUSH1[0x1] + Op.ADD + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(Op.CALL(gas=0x6, address=Op.DUP8, value=Op.DUP1, args_offset=Op.DUP2, args_size=0x20, ret_offset=Op.DUP1, ret_size=0x0))
        + Op.PUSH1[0x1] + Op.ADD + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(Op.CALL(gas=0x6, address=Op.DUP8, value=Op.DUP1, args_offset=Op.DUP2, args_size=0x20, ret_offset=Op.DUP1, ret_size=0x0))
        + Op.PUSH1[0x1] + Op.ADD + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(Op.CALL(gas=0x6, address=Op.DUP8, value=Op.DUP1, args_offset=Op.DUP2, args_size=0x20, ret_offset=Op.DUP1, ret_size=0x0))
        + Op.PUSH1[0x1] + Op.ADD + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(Op.CALL(gas=0x6, address=Op.DUP8, value=Op.DUP1, args_offset=Op.DUP2, args_size=0x20, ret_offset=Op.DUP1, ret_size=0x0))
        + Op.PUSH1[0x1] + Op.ADD + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(Op.CALL(gas=0x6, address=Op.DUP8, value=Op.DUP1, args_offset=Op.DUP2, args_size=0x20, ret_offset=Op.DUP1, ret_size=0x0))
        + Op.PUSH1[0x1] + Op.ADD + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(Op.CALL(gas=0x6, address=Op.DUP8, value=Op.DUP1, args_offset=Op.DUP2, args_size=0x20, ret_offset=Op.DUP1, ret_size=0x0))
        + Op.PUSH1[0x1] + Op.ADD + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(Op.CALL(gas=0x6, address=Op.DUP8, value=Op.DUP1, args_offset=Op.DUP2, args_size=0x20, ret_offset=Op.DUP1, ret_size=0x0))
        + Op.PUSH1[0x1] + Op.ADD + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(Op.CALL(gas=0x6, address=Op.DUP8, value=Op.DUP1, args_offset=Op.DUP2, args_size=0x20, ret_offset=Op.DUP1, ret_size=0x0))
        + Op.PUSH1[0x1] + Op.ADD + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(Op.CALL(gas=0x6, address=Op.DUP8, value=Op.DUP1, args_offset=Op.DUP2, args_size=0x20, ret_offset=Op.DUP1, ret_size=0x0))
        + Op.PUSH1[0x1] + Op.ADD + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(Op.CALL(gas=0x6, address=Op.DUP8, value=Op.DUP1, args_offset=Op.DUP2, args_size=0x20, ret_offset=Op.DUP1, ret_size=0x0))
        + Op.PUSH1[0x1] + Op.ADD + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(Op.CALL(gas=0x6, address=Op.DUP8, value=Op.DUP1, args_offset=Op.DUP2, args_size=0x20, ret_offset=Op.DUP1, ret_size=0x0))
        + Op.PUSH1[0x1] + Op.ADD + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(Op.CALL(gas=0x6, address=Op.DUP8, value=Op.DUP1, args_offset=Op.DUP2, args_size=0x20, ret_offset=Op.DUP1, ret_size=0x0))
        + Op.PUSH1[0x1] + Op.ADD + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(Op.CALL(gas=0x6, address=Op.DUP8, value=Op.DUP1, args_offset=Op.DUP2, args_size=0x20, ret_offset=Op.DUP1, ret_size=0x0))
        + Op.PUSH1[0x1] + Op.ADD + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(Op.CALL(gas=0x6, address=Op.DUP8, value=Op.DUP1, args_offset=Op.DUP2, args_size=0x20, ret_offset=Op.DUP1, ret_size=0x0))
        + Op.PUSH1[0x1] + Op.ADD + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(Op.CALL(gas=0x6, address=Op.DUP8, value=Op.DUP1, args_offset=Op.DUP2, args_size=0x20, ret_offset=Op.DUP1, ret_size=0x0))
        + Op.PUSH1[0x1] + Op.ADD + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(Op.CALL(gas=0x6, address=Op.DUP8, value=Op.DUP1, args_offset=Op.DUP2, args_size=0x20, ret_offset=Op.DUP1, ret_size=0x0))
        + Op.PUSH1[0x1] + Op.ADD + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(Op.CALL(gas=0x6, address=Op.DUP8, value=Op.DUP1, args_offset=Op.DUP2, args_size=0x20, ret_offset=Op.DUP1, ret_size=0x0))
        + Op.PUSH1[0x1] + Op.ADD + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(Op.CALL(gas=0x6, address=Op.DUP8, value=Op.DUP1, args_offset=Op.DUP2, args_size=0x20, ret_offset=Op.DUP1, ret_size=0x0))
        + Op.PUSH1[0x1] + Op.ADD + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(Op.CALL(gas=0x6, address=Op.DUP8, value=Op.DUP1, args_offset=Op.DUP2, args_size=0x20, ret_offset=Op.DUP1, ret_size=0x0))
        + Op.PUSH1[0x1] + Op.ADD + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.POP(Op.CALL(gas=0x6, address=Op.DUP8, value=Op.DUP1, args_offset=Op.DUP2, args_size=0x20, ret_offset=Op.DUP1, ret_size=0x0))
        + Op.JUMPI(pc=Op.PUSH3[0x2f], condition=Op.LT(0x6000, Op.GAS))
        + Op.PUSH1[0x0] + Op.SSTORE,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0x6a0a0fc761c612c340a0e98d33b37a75e5268472"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xc9f2c9cd04674edea40000000)


    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=b'',
        gas_limit=10000000,
        nonce=0,
        gas_price=10,
    )

    post = {
        contract_0: Account(storage={0: 0x10c20}, nonce=1),
        sender: Account(storage={}, nonce=1),
        Address("0x0000000000000000000000000000000000000001"): Account.NONEXISTENT,  # noqa: E501
        Address("0x0000000000000000000000000000000000000002"): Account.NONEXISTENT,  # noqa: E501
        Address("0x0000000000000000000000000000000000000003"): Account.NONEXISTENT,  # noqa: E501
        Address("0x0000000000000000000000000000000000000004"): Account.NONEXISTENT,  # noqa: E501
        Address("0x0000000000000000000000000000000000000005"): Account.NONEXISTENT,  # noqa: E501
        Address("0x0000000000000000000000000000000000000006"): Account.NONEXISTENT,  # noqa: E501
        Address("0x0000000000000000000000000000000000000015"): Account.NONEXISTENT,  # noqa: E501
        Address("0x000000000000000000000000000000000000006e"): Account.NONEXISTENT,  # noqa: E501
        Address("0x0000000000000000000000000000000000002170"): Account.NONEXISTENT,  # noqa: E501
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
