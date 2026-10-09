"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
state_tests/VMTests/vmArithmeticTest/notFiller.yml
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytes,
    Hash,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/VMTests/vmArithmeticTest/notFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
def test_not(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Ori Pomerantz qbzzt1@gmail."""
    sender = pre.fund_eoa(amount=0xBA1A9CE0BA1A9CE)

    # Source: lll
    # {
    #    [[0]] (not 0x0123456789abcdef)
    # }
    contract_0 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.NOT(0x123456789ABCDEF)) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
    )
    # Source: lll
    # {
    #     (call 0xffffff (+ 0x1000 $4) 0 0 0 0 0)
    # }
    contract_1 = pre.deploy_contract(
        code=Op.CALL(
            gas=0xFFFFFF,
            address=Op.ADD(contract_0, Op.CALLDATALOAD(offset=0x4)),
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
    )

    tx = Transaction(
        sender=sender,
        to=contract_1,
        data=Bytes("693c6139") + Hash(0x0),
        gas_limit=16777216,
        value=1,
    )

    post = {
        contract_0: Account(
            storage={
                0: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEDCBA9876543210,  # noqa: E501
            },
        ),
    }

    state_test(pre=pre, post=post, tx=tx)
