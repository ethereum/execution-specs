"""
call with value and oog happens inside.

Ported from:
tests/static/state_tests/stCallCreateCallCodeTest
callWithHighValueOOGinCallFiller.json
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
    [
        "tests/static/state_tests/stCallCreateCallCodeTest/callWithHighValueOOGinCallFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_call_with_high_value_oo_gin_call(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Call with value and oog happens inside."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xE04D1AC7DDDA0C98397D56A0B501E960D4CD325A39286919AC23C1A07009A869
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=30000000,
    )

    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x1, value=0x1)
            + Op.MSTORE8(offset=0x0, value=0x37)
            + Op.RETURN(offset=0x0, size=0x2)
        ),
        balance=23,
        nonce=0,
        address=Address("0x0896f13e800125c0ccec44f3c434335f0a97bc1b"),  # noqa: E501
    )
    # Source: LLL
    # {  [[ 0 ]] (ADD (CALL 10000 <contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5> 1000000000000000000 0 0 0 0 ) 1) }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.ADD(
                    Op.CALL(
                        gas=0x2710,
                        address=0x896F13E800125C0CCEC44F3C434335F0A97BC1B,
                        value=0xDE0B6B3A7640000,
                        args_offset=0x0,
                        args_size=0x0,
                        ret_offset=0x0,
                        ret_size=0x0,
                    ),
                    0x1,
                ),
            )
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640001,
        nonce=0,
        address=Address("0xab77465b5abf0c394945e4186c02776f8eb9f2e7"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=3000000,
    )

    post = {
        contract: Account(storage={0: 1}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
