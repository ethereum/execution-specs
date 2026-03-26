"""
test_create_contract_via_contract_oog_init_code

Ported from:
state_tests/stHomesteadSpecific/createContractViaContractOOGInitCodeFiller.json
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
    ["state_tests/stHomesteadSpecific/createContractViaContractOOGInitCodeFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_create_contract_via_contract_oog_init_code(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_create_contract_via_contract_oog_init_code"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    contract_0 = Address("0x1000000000000000000000000000000000000001")
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
        gas_limit=1000000,
    )

    pre[sender] = Account(balance=0x10c8e0)
    # Source: lll
    # { (MSTORE 0 0x602060406000f0600c600055)(CREATE 0 20 12)}
    contract_0 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=0x602060406000f0600c600055)
        + Op.CREATE(value=0x0, offset=0x14, size=0xc) + Op.STOP,
        nonce=0,
        address=Address("0x1000000000000000000000000000000000000001"),  # noqa: E501
    )


    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=b'',
        gas_limit=105044,
        nonce=0,
        gas_price=10,
    )

    post = {
        Address("0x4ff884bffc83e888ae11b32b1d94bf9bc8d1732f"): Account.NONEXISTENT,  # noqa: E501
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
