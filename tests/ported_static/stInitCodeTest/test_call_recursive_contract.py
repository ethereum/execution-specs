"""
Test_call_recursive_contract.

Ported from:
state_tests/stInitCodeTest/CallRecursiveContractFiller.json
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
    ["state_tests/stInitCodeTest/CallRecursiveContractFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_call_recursive_contract(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_call_recursive_contract."""
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
        gas_limit=100000000,
    )

    # Source: lll
    # {[[ 2 ]](ADDRESS)(CODECOPY 0 0 32)(CREATE 0 0 32)}
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x2, value=Op.ADDRESS)
        + Op.CODECOPY(dest_offset=0x0, offset=0x0, size=0x20)
        + Op.CREATE(value=0x0, offset=0x0, size=0x20)
        + Op.STOP,
        nonce=40,
        address=Address(0x095E7BAEA6A6C7C4C2DFEB977EFAC326AF552D87),  # noqa: E501
    )
    pre[sender] = Account(balance=0x989680)

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=Bytes("00"),
        gas_limit=400000,
        value=1,
    )

    post = {
        contract_0: Account(
            storage={2: 0x95E7BAEA6A6C7C4C2DFEB977EFAC326AF552D87},
            balance=1,
            nonce=41,
        ),
        Address(
            0x1A4C83E1A9834CDC7E4A905FF7F0CF44AED73180
        ): Account.NONEXISTENT,
        Address(
            0x8E3411C91D5DD4081B4846FA2F93808F5AD19686
        ): Account.NONEXISTENT,
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
