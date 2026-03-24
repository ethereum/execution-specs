"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stAttackTest/ContractCreationSpamFiller.json
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
    ["tests/static/state_tests/stAttackTest/ContractCreationSpamFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.slow
@pytest.mark.pre_alloc_mutable
def test_contract_creation_spam(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
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

    # Source: raw bytecode
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(
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
                ),
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
                ),
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
                ),
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
                ),
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
                ),
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
                ),
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
                ),
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
                ),
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
                ),
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
                ),
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
                ),
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
                ),
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
                ),
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
                ),
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
                ),
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
                ),
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
                ),
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
                ),
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
                ),
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
                ),
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
                ),
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
                ),
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
                ),
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
                ),
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
                ),
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
                ),
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
                ),
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
                ),
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
                ),
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
                ),
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
                ),
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
                ),
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
                ),
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
                ),
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
                ),
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
                ),
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
                ),
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
                ),
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
                ),
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
                ),
            )
            + Op.JUMPI(pc=Op.PUSH3[0x2F], condition=Op.LT(0x6000, Op.GAS))
            + Op.PUSH1[0x0]
            + Op.SSTORE
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x6a0a0fc761c612c340a0e98d33b37a75e5268472"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xC9F2C9CD04674EDEA40000000)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=10000000,
    )

    post = {
        contract: Account(storage={0: 0x10C20}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
