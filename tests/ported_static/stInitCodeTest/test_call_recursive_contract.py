"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stInitCodeTest/CallRecursiveContractFiller.json
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
        "tests/static/state_tests/stInitCodeTest/CallRecursiveContractFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_call_recursive_contract(
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
        gas_limit=100000000,
    )

    # Source: LLL
    # {[[ 2 ]](ADDRESS)(CODECOPY 0 0 32)(CREATE 0 0 32)}
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x2, value=Op.ADDRESS)
            + Op.CODECOPY(dest_offset=0x0, offset=0x0, size=0x20)
            + Op.CREATE(value=0x0, offset=0x0, size=0x20)
            + Op.STOP
        ),
        nonce=40,
        address=Address("0x095e7baea6a6c7c4c2dfeb977efac326af552d87"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x989680)

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex("00"),
        gas_limit=400000,
        value=1,
    )

    post = {
        contract: Account(
            storage={2: 0x95E7BAEA6A6C7C4C2DFEB977EFAC326AF552D87},
            nonce=41,
            balance=1,
        ),
        Address(
            "0x1a4c83e1a9834cdc7e4a905ff7f0cf44aed73180"
        ): Account.NONEXISTENT,
        Address(
            "0x8e3411c91d5dd4081b4846fa2f93808f5ad19686"
        ): Account.NONEXISTENT,
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
