"""
Test_create_init_fail_oo_gduring_init2.

Ported from:
state_tests/stCallCreateCallCodeTest/createInitFail_OOGduringInit2Filler.json
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
    compute_create_address,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stCallCreateCallCodeTest/createInitFail_OOGduringInit2Filler.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_create_init_fail_oo_gduring_init2(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_create_init_fail_oo_gduring_init2."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0x095E7BAEA6A6C7C4C2DFEB977EFAC326AF552D87)
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    # Source: lll
    # { (CREATE 1 0  (lll(seq [[1]] 1 (KECCAK256 0x00 0x2fffff) )0))   }
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.PUSH1[0xD]
        + Op.CODECOPY(dest_offset=0x0, offset=0xF, size=Op.DUP1)
        + Op.PUSH1[0x0]
        + Op.PUSH1[0x1]
        + Op.CREATE
        + Op.STOP
        + Op.INVALID
        + Op.SSTORE(key=0x1, value=0x1)
        + Op.SHA3(offset=0x0, size=0x2FFFFF)
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0x095E7BAEA6A6C7C4C2DFEB977EFAC326AF552D87),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=Bytes(""),
        gas_limit=1000000,
        value=0x186A0,
    )

    post = {
        compute_create_address(
            address=contract_0, nonce=0
        ): Account.NONEXISTENT,
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
