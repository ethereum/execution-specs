"""
check output memory after callcode. callcode fails with underflow stack

Ported from:
state_tests/stCallCreateCallCodeTest/callcodeOutput3partialFailFiller.json
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
    ["state_tests/stCallCreateCallCodeTest/callcodeOutput3partialFailFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_callcode_output3partial_fail(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """check output memory after callcode."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xb1f4cbc3a50042184425a6f9e996d0910f7ba879457ce5dac5c71e498ad3c005
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    # Source: lll
    # { (MSTORE 0 0x5e20a0453cecd065ea59c37ac63e079ee08998b6045136a8ce6635c7912ec0b6) (CALLCODE 50000 <contract:0xaaae7baea6a6c7c4c2dfeb977efac326af552d87> 0 0 0 0 10) [[ 0 ]] (MLOAD 0)}
    target = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=0x5e20a0453cecd065ea59c37ac63e079ee08998b6045136a8ce6635c7912ec0b6)
        + Op.POP(Op.CALLCODE(gas=0xc350, address=0x834abc2c68c5f44ea9ae82b67aaf92044901cdc6, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0xa))
        + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0)) + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0xee172f045cfa9101ee8c62faf6975d8f4c1e2099"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000)
    # Source: raw
    # 0x016001600101600055
    addr_0xaaae7baea6a6c7c4c2dfeb977efac326af552d87 = pre.deploy_contract(
        code=Op.ADD + Op.SSTORE(key=0x0, value=Op.ADD(0x1, 0x1)),
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0x834abc2c68c5f44ea9ae82b67aaf92044901cdc6"),  # noqa: E501
    )


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=1000000,
        value=0x186a0,
        nonce=0,
        gas_price=10,
    )

    post = {
        target: Account(
                storage={
            0: 0x5e20a0453cecd065ea59c37ac63e079ee08998b6045136a8ce6635c7912ec0b6,
        },
            ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
