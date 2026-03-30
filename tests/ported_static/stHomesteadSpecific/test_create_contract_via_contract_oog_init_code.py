"""
Test_create_contract_via_contract_oog_init_code.

Ported from:
state_tests/stHomesteadSpecific/createContractViaContractOOGInitCodeFiller.json
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
    [
        "state_tests/stHomesteadSpecific/createContractViaContractOOGInitCodeFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_create_contract_via_contract_oog_init_code(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_create_contract_via_contract_oog_init_code."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0x1000000000000000000000000000000000000001)
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre[sender] = Account(balance=0x10C8E0)
    # Source: lll
    # { (MSTORE 0 0x602060406000f0600c600055)(CREATE 0 20 12)}
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=0x602060406000F0600C600055)
        + Op.CREATE(value=0x0, offset=0x14, size=0xC)
        + Op.STOP,
        nonce=0,
        address=Address(0x1000000000000000000000000000000000000001),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=Bytes(""),
        gas_limit=105044,
    )

    post = {
        Address(
            0x4FF884BFFC83E888AE11B32B1D94BF9BC8D1732F
        ): Account.NONEXISTENT,
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
