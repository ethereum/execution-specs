"""
test_create_init_fail_oo_gduring_init2

Ported from:
state_tests/stCallCreateCallCodeTest/createInitFail_OOGduringInit2Filler.json
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
    ["state_tests/stCallCreateCallCodeTest/createInitFail_OOGduringInit2Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_create_init_fail_oo_gduring_init2(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_create_init_fail_oo_gduring_init2"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    contract_0 = Address("0x095e7baea6a6c7c4c2dfeb977efac326af552d87")
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
        gas_limit=10000000,
    )

    # Source: lll
    # { (CREATE 1 0  (lll(seq [[1]] 1 (KECCAK256 0x00 0x2fffff) )0))   }
    contract_0 = pre.deploy_contract(
        code=Op.PUSH1[0xd] + Op.CODECOPY(dest_offset=0x0, offset=0xf, size=Op.DUP1)
        + Op.PUSH1[0x0] + Op.PUSH1[0x1] + Op.CREATE + Op.STOP + Op.INVALID
        + Op.SSTORE(key=0x1, value=0x1) + Op.SHA3(offset=0x0, size=0x2fffff)
        + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0x095e7baea6a6c7c4c2dfeb977efac326af552d87"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000)


    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=b'',
        gas_limit=1000000,
        value=0x186a0,
        nonce=0,
        gas_price=10,
    )

    post = {
        Address("0xd2571607e241ecf590ed94b12d87c94babe36db6"): Account.NONEXISTENT,  # noqa: E501
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
